"""
API V2 - GIGA ROADMAP S2
Recherche temps réel + debounce + cancellation + facettes
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import require_membership
from apps.metadata.query_builder_v2 import SearchQueryBuilderV2
from apps.metadata.feature_flags import FeatureFlagService


@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def search_api_v2(request):
    """
    API de recherche V2 - GIGA ROADMAP
    
    Params:
        q: Terme de recherche
        entity: Type d'entité (cepage, parcelle, unite)
        filters[]: Filtres additionnels
        facets[]: Facettes à calculer
        sort: Champ de tri
        page: Numéro de page (défaut: 1)
        page_size: Taille de page (défaut: 20, max: 100)
        live: 1 si recherche en temps réel
        v: Version API (1 ou 2)
    """
    
    # Vérifier si V2 est activé pour cet utilisateur
    if not FeatureFlagService.is_enabled('search_v2_read', user=request.user):
        return JsonResponse({
            'error': 'API V2 non disponible',
            'fallback_url': '/ref/cepages/search-ajax/',
        }, status=503)
    
    # Validation des paramètres
    query = request.GET.get('q', '').strip()
    entity_type = request.GET.get('entity', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    live = request.GET.get('live') == '1'
    
    # Filtres (format: filters[couleur]=rouge)
    filters = {}
    for key, value in request.GET.items():
        if key.startswith('filters[') and key.endswith(']'):
            filter_name = key[8:-1]  # Extraire le nom entre []
            filters[filter_name] = value
    
    # Facettes (format: facets[]=couleur&facets[]=type)
    facets = request.GET.getlist('facets[]')
    
    # Tri
    sort = request.GET.get('sort', '')
    
    # Validation sécurité
    allowed_entities = ['cepage', 'parcelle', 'unite', 'cuvee', 'entrepot']
    if entity_type and entity_type not in allowed_entities:
        return JsonResponse({'error': 'Type d\'entité non autorisé'}, status=400)
    
    allowed_sorts = ['nom', 'code', 'created_at', '-created_at']
    if sort and sort not in allowed_sorts:
        return JsonResponse({'error': 'Tri non autorisé'}, status=400)
    
    if page_size > 100:
        return JsonResponse({'error': 'page_size maximum: 100'}, status=400)
    
    try:
        # Exécuter la recherche
        builder = SearchQueryBuilderV2(
            organization=request.current_org,
            user=request.user
        )
        
        result = builder.search(
            query=query,
            entity_type=entity_type,
            filters=filters,
            facets=facets,
            sort=sort,
            page=page,
            page_size=page_size,
            live=live
        )
        
        # Ajouter métadonnées de performance
        result['meta'] = {
            'version': '2.0',
            'live_search': live,
            'query_length': len(query),
            'filters_count': len(filters),
            'facets_count': len(facets),
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Erreur de recherche',
            'details': str(e) if request.user.is_staff else None,
        }, status=500)


@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def search_suggestions_v2(request):
    """
    API de suggestions V2 pour autocomplétion
    GIGA ROADMAP: suggestions orthographe + synonymes
    """
    
    query = request.GET.get('q', '').strip()
    entity_type = request.GET.get('entity', '')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Pour cette démo, suggestions simples
    suggestions = []
    
    if entity_type == 'cepage':
        grape_suggestions = [
            'Cabernet Sauvignon', 'Merlot', 'Chardonnay', 
            'Sauvignon Blanc', 'Pinot Noir', 'Syrah'
        ]
        suggestions = [
            s for s in grape_suggestions 
            if query.lower() in s.lower()
        ][:5]
    
    return JsonResponse({
        'suggestions': suggestions,
        'query': query,
        'entity': entity_type,
    })


@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def search_facets_v2(request):
    """
    API des facettes V2 pour filtrage avancé
    GIGA ROADMAP: facettes top N + pagination
    """
    
    entity_type = request.GET.get('entity', '')
    facet_field = request.GET.get('field', '')
    
    if not entity_type or not facet_field:
        return JsonResponse({'error': 'entity et field requis'}, status=400)
    
    # Simulation facettes
    facets_data = {}
    
    if entity_type == 'cepage' and facet_field == 'couleur':
        from apps.referentiels.models import Cepage
        from django.db.models import Count
        
        facets_data = list(
            Cepage.objects.filter(organization=request.current_org)
            .values('couleur')
            .annotate(count=Count('couleur'))
            .order_by('-count')
        )
    
    return JsonResponse({
        'facets': facets_data,
        'entity': entity_type,
        'field': facet_field,
    })


@require_membership(role_min='editor')
@require_http_methods(["GET"])
def inline_edit_cell_v2(request, entity_type, entity_id, field_name):
    """
    API inline edit V2 - GET cellule pour édition
    GIGA ROADMAP S2: double-clic → éditeur
    """
    
    if not FeatureFlagService.is_enabled('inline_edit_v2_enabled', user=request.user):
        return JsonResponse({'error': 'Édition inline non disponible'}, status=503)
    
    # Validation sécurité
    allowed_entities = ['cepage', 'parcelle', 'unite']
    if entity_type not in allowed_entities:
        return JsonResponse({'error': 'Type d\'entité non autorisé'}, status=400)
    
    allowed_fields = {
        'cepage': ['nom', 'code', 'couleur'],
        'parcelle': ['nom', 'surface_ha', 'lieu_dit', 'commune'],
        'unite': ['nom', 'symbole', 'facteur_conversion'],
    }
    
    if field_name not in allowed_fields.get(entity_type, []):
        return JsonResponse({'error': 'Champ non éditable'}, status=403)
    
    try:
        # Récupérer l'objet
        from apps.referentiels.models import Cepage, Parcelle, Unite
        
        models_map = {
            'cepage': Cepage,
            'parcelle': Parcelle,
            'unite': Unite,
        }
        
        model_class = models_map[entity_type]
        obj = model_class.objects.get(
            id=entity_id,
            organization=request.current_org
        )
        
        # Valeur actuelle
        current_value = getattr(obj, field_name)
        
        # Métadonnées du champ
        field_meta = obj._meta.get_field(field_name)
        field_type = field_meta.__class__.__name__
        
        # Choix pour les champs avec choices
        choices = []
        if hasattr(field_meta, 'choices') and field_meta.choices:
            choices = [{'value': k, 'label': v} for k, v in field_meta.choices]
        
        return JsonResponse({
            'value': current_value,
            'field_type': field_type,
            'choices': choices,
            'row_version': getattr(obj, 'row_version', 1),
            'max_length': getattr(field_meta, 'max_length', None),
            'required': not field_meta.null,
        })
        
    except model_class.DoesNotExist:
        return JsonResponse({'error': 'Objet non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_membership(role_min='editor')
@require_http_methods(["PUT"])
@csrf_exempt
def inline_edit_save_v2(request, entity_type, entity_id, field_name):
    """
    API inline edit V2 - PUT sauvegarde cellule
    GIGA ROADMAP S2: optimistic locking + undo
    """
    
    if not FeatureFlagService.is_enabled('inline_edit_v2_enabled', user=request.user):
        return JsonResponse({'error': 'Édition inline non disponible'}, status=503)
    
    try:
        # Parser le JSON
        data = json.loads(request.body)
        new_value = data.get('value')
        row_version = data.get('row_version')
        
        # Récupérer l'objet avec locking optimiste
        from apps.referentiels.models import Cepage, Parcelle, Unite
        
        models_map = {
            'cepage': Cepage,
            'parcelle': Parcelle,
            'unite': Unite,
        }
        
        model_class = models_map[entity_type]
        obj = model_class.objects.get(
            id=entity_id,
            organization=request.current_org
        )
        
        # Vérifier row_version (optimistic locking)
        current_row_version = getattr(obj, 'row_version', 1)
        if row_version and current_row_version != row_version:
            return JsonResponse({
                'error': 'Conflit de version',
                'current_value': getattr(obj, field_name),
                'current_row_version': current_row_version,
            }, status=409)
        
        # Sauvegarder l'ancienne valeur pour undo
        old_value = getattr(obj, field_name)
        
        # Mettre à jour
        setattr(obj, field_name, new_value)
        obj.save()
        
        # Nouvelle row_version après save
        obj.refresh_from_db()
        new_row_version = getattr(obj, 'row_version', current_row_version + 1)
        
        return JsonResponse({
            'success': True,
            'value': new_value,
            'row_version': new_row_version,
            'undo_data': {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'field_name': field_name,
                'old_value': old_value,
                'old_row_version': current_row_version,
            }
        })
        
    except model_class.DoesNotExist:
        return JsonResponse({'error': 'Objet non trouvé'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_membership(role_min='editor')
@require_http_methods(["POST"])
@csrf_exempt
def inline_edit_undo_v2(request):
    """
    API inline edit V2 - POST undo
    GIGA ROADMAP S2: toast 5-10s avec undo
    """
    
    try:
        data = json.loads(request.body)
        undo_data = data.get('undo_data', {})
        
        entity_type = undo_data.get('entity_type')
        entity_id = undo_data.get('entity_id')
        field_name = undo_data.get('field_name')
        old_value = undo_data.get('old_value')
        old_row_version = undo_data.get('old_row_version')
        
        # Récupérer l'objet
        from apps.referentiels.models import Cepage, Parcelle, Unite
        
        models_map = {
            'cepage': Cepage,
            'parcelle': Parcelle,
            'unite': Unite,
        }
        
        model_class = models_map[entity_type]
        obj = model_class.objects.get(
            id=entity_id,
            organization=request.current_org
        )
        
        # Vérifier qu'il n'y a pas eu d'autres modifications
        current_row_version = getattr(obj, 'row_version', 1)
        if current_row_version != old_row_version + 1:
            return JsonResponse({
                'error': 'Impossible d\'annuler - objet modifié entre temps'
            }, status=409)
        
        # Restaurer l'ancienne valeur
        setattr(obj, field_name, old_value)
        obj.save()
        
        return JsonResponse({
            'success': True,
            'restored_value': old_value,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
