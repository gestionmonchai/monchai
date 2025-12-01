"""
Vues API pour système d'import générique
Endpoints REST selon roadmaps CSV 1-5
"""

import json
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from apps.accounts.decorators import require_membership
from .models import ImportJob
from .services.upload_service import UploadService
from .adapters import IMPORT_ADAPTERS, get_adapter


@require_http_methods(["POST"])
@login_required
@require_membership(role_min='editor')
@csrf_exempt
def upload_file(request, entity):
    """
    Upload fichier pour import
    POST /import/{entity}/upload/
    
    Roadmap CSV_1: Upload sécurisé
    """
    try:
        # Validation entité
        if entity not in IMPORT_ADAPTERS:
            return JsonResponse({
                'error': f'Entité non supportée: {entity}',
                'supported_entities': list(IMPORT_ADAPTERS.keys())
            }, status=400)
        
        # Validation fichier
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Aucun fichier fourni'}, status=400)
        
        file = request.FILES['file']
        
        # Service upload
        upload_service = UploadService(request.current_org, request.user)
        job = upload_service.upload_file(file, entity)
        
        return JsonResponse({
            'job_id': str(job.id),
            'filename': job.filename,
            'size_bytes': job.size_bytes,
            'sha256': job.sha256,
            'status': job.status,
            'entity': job.entity
        })
        
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=422)
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)


@require_http_methods(["GET"])
@login_required
@require_membership(role_min='read_only')
def preview_file(request, job_id):
    """
    Prévisualisation fichier uploadé
    GET /import/{job_id}/preview/
    
    Roadmap CSV_1: Prévisualisation sécurisée
    """
    try:
        # Récupération job
        job = get_object_or_404(
            ImportJob,
            id=job_id,
            organization=request.current_org
        )
        
        # Paramètres
        rows = int(request.GET.get('rows', 10))
        sheet = int(request.GET.get('sheet', 0))
        
        # Validation limites
        if rows > 50:
            rows = 50
        
        # Service upload
        upload_service = UploadService(request.current_org, request.user)
        preview_data = upload_service.preview_file(job, rows, sheet)
        
        return JsonResponse({
            'job_id': str(job.id),
            'status': job.status,
            **preview_data
        })
        
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=422)
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)


@require_http_methods(["GET"])
@login_required
@require_membership(role_min='read_only')
def get_entity_schema(request, entity):
    """
    Schéma entité pour mapping
    GET /import/schema/{entity}/
    
    Roadmap CSV_2: Configuration mapping
    """
    try:
        # Validation entité
        if entity not in ENTITY_ADAPTERS:
            return JsonResponse({
                'error': f'Entité non supportée: {entity}'
            }, status=400)
        
        adapter = ENTITY_ADAPTERS[entity]
        schema = adapter.get_schema()
        
        return JsonResponse({
            'entity': entity,
            'display_name': adapter.display_name,
            'schema': schema
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@login_required
@require_membership(role_min='editor')
@csrf_exempt
def auto_map_columns(request, job_id):
    """
    Auto-mapping colonnes CSV → champs entité
    POST /import/{job_id}/auto-map/
    
    Roadmap CSV_2: Auto-mapping intelligent
    """
    try:
        # Récupération job
        job = get_object_or_404(
            ImportJob,
            id=job_id,
            organization=request.current_org
        )
        
        # Validation statut
        if job.status not in ['uploaded', 'previewed']:
            return JsonResponse({
                'error': f'Job dans état invalide: {job.status}'
            }, status=400)
        
        # Données POST
        data = json.loads(request.body)
        csv_columns = data.get('csv_columns', [])
        
        if not csv_columns:
            return JsonResponse({'error': 'Colonnes CSV requises'}, status=400)
        
        # Adapter entité
        if job.entity not in ENTITY_ADAPTERS:
            return JsonResponse({
                'error': f'Entité non supportée: {job.entity}'
            }, status=400)
        
        adapter = ENTITY_ADAPTERS[job.entity]
        
        # Auto-mapping
        mapping = {}
        for i, csv_col in enumerate(csv_columns):
            field = adapter.find_field_by_synonym(csv_col)
            if field:
                confidence = adapter.calculate_mapping_confidence(csv_col, field)
                mapping[csv_col] = {
                    'csv_index': i,
                    'entity_field': field,
                    'confidence': confidence,
                    'transforms': adapter.get_transforms_defaults().get(field, []),
                    'is_required': field in adapter.get_required_fields(),
                    'is_unique_key': field == adapter.get_unique_key(),
                    'help_text': adapter.get_field_help_text(field),
                    'examples': adapter.get_example_values(field)
                }
        
        return JsonResponse({
            'job_id': str(job.id),
            'mapping': mapping,
            'coverage': len(mapping) / len(csv_columns) if csv_columns else 0,
            'required_fields_mapped': [
                field for field in adapter.get_required_fields()
                if any(m['entity_field'] == field for m in mapping.values())
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)


@require_http_methods(["GET"])
@login_required
@require_membership(role_min='read_only')
def job_status(request, job_id):
    """
    Statut job d'import
    GET /import/{job_id}/status/
    
    Roadmap CSV_4: Polling progression
    """
    try:
        job = get_object_or_404(
            ImportJob,
            id=job_id,
            organization=request.current_org
        )
        
        return JsonResponse({
            'job_id': str(job.id),
            'status': job.status,
            'entity': job.entity,
            'filename': job.filename,
            'progress_pct': job.progress_pct,
            'success_rate': job.success_rate,
            'total_rows': job.total_rows,
            'inserted_count': job.inserted_count,
            'updated_count': job.updated_count,
            'skipped_count': job.skipped_count,
            'error_count': job.error_count,
            'warning_count': job.warning_count,
            'duration_seconds': job.duration_seconds,
            'started_at': job.started_at.isoformat(),
            'ended_at': job.ended_at.isoformat() if job.ended_at else None
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)


@require_http_methods(["GET"])
@login_required
@require_membership(role_min='read_only')
def list_jobs(request):
    """
    Liste jobs d'import utilisateur
    GET /import/jobs/
    
    Roadmap CSV_5: Historique
    """
    try:
        jobs = ImportJob.objects.filter(
            organization=request.current_org,
            created_by=request.user
        ).order_by('-started_at')[:50]  # 50 derniers
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'job_id': str(job.id),
                'entity': job.entity,
                'filename': job.filename,
                'status': job.status,
                'progress_pct': job.progress_pct,
                'success_rate': job.success_rate,
                'started_at': job.started_at.isoformat(),
                'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                'duration_seconds': job.duration_seconds
            })
        
        return JsonResponse({
            'jobs': jobs_data,
            'count': len(jobs_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)
