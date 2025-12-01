"""
API Views pour le catalogue - Roadmap 25
Endpoint /api/catalogue avec recherche, facettes, tri et pagination keyset
Query Builder v2 avec caching Redis et mesures de performance
"""

import json
import time
import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, F, Prefetch
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from apps.accounts.decorators import require_membership
from apps.viticulture.models import Cuvee
from apps.viticulture.models import Appellation, Vintage, UnitOfMeasure
from apps.viticulture.models import VineyardPlot, GrapeVariety
from apps.produits.models_catalog import SKU
import hashlib

logger = logging.getLogger(__name__)


class CatalogueQueryBuilder:
    """
    Query Builder v2 pour le catalogue avec optimisations performance
    """
    
    def __init__(self, organization):
        self.organization = organization
        self.query_stats = {
            'queries_count': 0,
            'cache_hits': 0,
            'total_time': 0
        }
    
    def build_base_query(self):
        """Requête de base optimisée avec prefetch"""
        return Cuvee.objects.filter(
            organization=self.organization,
            is_active=True
        ).select_related(
            'appellation', 
            'vintage', 
            'default_uom'
        ).prefetch_related(
            Prefetch('appellation', queryset=Appellation.objects.select_related())
        )
    
    def apply_search(self, queryset, search_query):
        """Application de la recherche textuelle avec optimisation"""
        if not search_query:
            return queryset
            
        # Recherche optimisée avec index
        return queryset.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(appellation__name__icontains=search_query)
        )
    
    def apply_filters(self, queryset, filters):
        """Application des filtres avec validation"""
        if filters.get('appellation'):
            queryset = queryset.filter(appellation__id=filters['appellation'])
        
        if filters.get('vintage'):
            queryset = queryset.filter(vintage__id=filters['vintage'])
        
        if filters.get('color'):
            queryset = queryset.filter(appellation__type=filters['color'])
            
        return queryset
    
    def apply_sorting(self, queryset, sort_param):
        """Application du tri avec index optimisé"""
        sort_mapping = {
            'name_asc': ['name', 'id'],
            'name_desc': ['-name', '-id'],
            'updated_desc': ['-updated_at', '-id']
        }
        
        if sort_param in sort_mapping:
            return queryset.order_by(*sort_mapping[sort_param])
        
        return queryset.order_by('name', 'id')  # Défaut
    
    def apply_keyset_pagination(self, queryset, cursor, sort_param):
        """Pagination keyset optimisée"""
        if not cursor:
            return queryset
            
        try:
            cursor_data = json.loads(cursor)
            
            if sort_param == 'updated_desc':
                return queryset.filter(
                    Q(updated_at__lt=cursor_data['updated_at']) |
                    Q(updated_at=cursor_data['updated_at'], id__lt=cursor_data['id'])
                )
            elif sort_param == 'name_asc':
                return queryset.filter(
                    Q(name__gt=cursor_data['name']) |
                    Q(name=cursor_data['name'], id__gt=cursor_data['id'])
                )
            else:  # name_desc
                return queryset.filter(
                    Q(name__lt=cursor_data['name']) |
                    Q(name=cursor_data['name'], id__lt=cursor_data['id'])
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid cursor format: {e}")
            return queryset


@login_required
@require_membership()
@require_http_methods(["GET"])
def catalogue_api(request):
    """
    API endpoint pour le catalogue des cuvées - Query Builder v2
    GET /api/catalogue?q=&appellation=&vintage=&color=&sort=&cursor=&page_size=24
    
    Retourne:
    {
        "items": [...],
        "next_cursor": "...",
        "facets": {...},
        "perf": {"elapsed_ms": 123, "cache_hit": false, "queries_count": 3}
    }
    """
    start_time = time.time()
    queries_start = len(connection.queries)
    organization = request.current_org
    
    # Paramètres de requête
    search_query = request.GET.get('q', '').strip()
    appellation_filter = request.GET.get('appellation', '')
    vintage_filter = request.GET.get('vintage', '')
    color_filter = request.GET.get('color', '')
    sort_param = request.GET.get('sort', 'name_asc')
    cursor = request.GET.get('cursor', '')
    page_size = min(int(request.GET.get('page_size', 24)), 100)  # Max 100
    
    # Validation des paramètres de tri
    valid_sorts = ['name_asc', 'name_desc', 'updated_desc']
    if sort_param not in valid_sorts:
        return JsonResponse({'error': 'Invalid sort parameter'}, status=400)
    
    # Cache key basée sur les paramètres
    cache_params = f"{search_query}:{appellation_filter}:{vintage_filter}:{color_filter}:{sort_param}:{cursor}:{page_size}"
    cache_key = f"catalogue_api_v2:{organization.id}:{hashlib.md5(cache_params.encode()).hexdigest()}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        cached_result['perf']['cache_hit'] = True
        cached_result['perf']['elapsed_ms'] = int((time.time() - start_time) * 1000)
        return JsonResponse(cached_result)
    
    try:
        # Utilisation du Query Builder v2
        builder = CatalogueQueryBuilder(organization)
        
        # Construction de la requête optimisée
        cuvees = builder.build_base_query()
        
        # Application de la recherche
        cuvees = builder.apply_search(cuvees, search_query)
        
        # Application des filtres
        filters = {
            'appellation': appellation_filter,
            'vintage': vintage_filter,
            'color': color_filter
        }
        cuvees = builder.apply_filters(cuvees, filters)
        
        # Application du tri
        cuvees = builder.apply_sorting(cuvees, sort_param)
        
        # Application de la pagination keyset
        cuvees = builder.apply_keyset_pagination(cuvees, cursor, sort_param)
        
        # Limiter les résultats
        cuvees_list = list(cuvees[:page_size + 1])  # +1 pour détecter s'il y a une page suivante
        
        # Préparer les données
        items = []
        for cuvee in cuvees_list[:page_size]:
            items.append({
                'id': str(cuvee.id),
                'name': cuvee.name,
                'slug': cuvee.code or str(cuvee.id),
                'appellation': {
                    'id': str(cuvee.appellation.id) if cuvee.appellation else None,
                    'name': cuvee.appellation.name if cuvee.appellation else None,
                    'type': cuvee.appellation.type if cuvee.appellation else None,
                },
                'vintage': {
                    'id': str(cuvee.vintage.id) if cuvee.vintage else None,
                    'year': cuvee.vintage.year if cuvee.vintage else None,
                },
                'color': cuvee.appellation.type if cuvee.appellation else None,
                'media': {
                    'thumb_url': None  # TODO: Intégrer avec système de médias
                },
                'updated_at': cuvee.updated_at.isoformat() if cuvee.updated_at else None,
            })
        
        # Cursor pour la page suivante
        next_cursor = None
        if len(cuvees_list) > page_size:
            last_item = cuvees_list[page_size - 1]
            if sort_param == 'updated_desc':
                next_cursor = json.dumps({
                    'updated_at': last_item.updated_at.isoformat(),
                    'id': str(last_item.id)
                })
            else:
                next_cursor = json.dumps({
                    'name': last_item.name,
                    'id': str(last_item.id)
                })
        
        # Facettes (compteurs pour filtres)
        base_cuvees = Cuvee.objects.filter(organization=organization, is_active=True)
        if search_query:
            base_cuvees = base_cuvees.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(appellation__name__icontains=search_query)
            )
        
        # Facettes appellations
        appellations_facets = list(
            base_cuvees.values('appellation__id', 'appellation__name')
            .annotate(count=Count('id'))
            .filter(appellation__id__isnull=False)
            .order_by('appellation__name')
        )
        
        # Facettes millésimes
        vintages_facets = list(
            base_cuvees.values('vintage__id', 'vintage__year')
            .annotate(count=Count('id'))
            .filter(vintage__id__isnull=False)
            .order_by('-vintage__year')
        )
        
        # Facettes couleurs
        colors_facets = list(
            base_cuvees.values('appellation__type')
            .annotate(count=Count('id'))
            .filter(appellation__type__isnull=False)
            .order_by('appellation__type')
        )
        
        facets = {
            'appellations': [
                {
                    'id': str(f['appellation__id']),
                    'name': f['appellation__name'],
                    'count': f['count']
                }
                for f in appellations_facets
            ],
            'vintages': [
                {
                    'id': str(f['vintage__id']),
                    'year': f['vintage__year'],
                    'count': f['count']
                }
                for f in vintages_facets
            ],
            'colors': [
                {
                    'value': f['appellation__type'],
                    'count': f['count']
                }
                for f in colors_facets
            ]
        }
        
        # Métriques de performance
        elapsed_ms = int((time.time() - start_time) * 1000)
        queries_count = len(connection.queries) - queries_start
        
        result = {
            'items': items,
            'next_cursor': next_cursor,
            'facets': facets,
            'perf': {
                'elapsed_ms': elapsed_ms,
                'cache_hit': False,
                'queries_count': queries_count,
                'items_count': len(items),
                'has_next_page': len(cuvees_list) > page_size
            }
        }
        
        # Cache pendant 120 secondes (TTL optimisé)
        cache.set(cache_key, result, 120)
        
        # Log des performances pour monitoring
        if elapsed_ms > 1000:  # Log si > 1s
            logger.warning(f"Slow catalogue API query: {elapsed_ms}ms, {queries_count} queries, org={organization.id}")
        elif elapsed_ms > 500:  # Log si > 500ms
            logger.info(f"Catalogue API query: {elapsed_ms}ms, {queries_count} queries, org={organization.id}")
        
        return JsonResponse(result)
        
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return JsonResponse({
            'error': 'Internal server error',
            'perf': {'elapsed_ms': elapsed_ms, 'cache_hit': False}
        }, status=500)


@login_required
@require_membership()
@require_http_methods(["GET"])
def catalogue_facets_api(request):
    """
    API pour récupérer uniquement les facettes disponibles
    GET /api/catalogue/facets
    """
    organization = request.current_org
    
    # Cache key pour les facettes
    cache_key = f"catalogue_facets:{organization.id}"
    cached_facets = cache.get(cache_key)
    
    if cached_facets:
        return JsonResponse(cached_facets)
    
    try:
        # Toutes les appellations de l'organisation
        appellations = list(
            Appellation.objects.filter(organization=organization)
            .values('id', 'name', 'type')
            .order_by('name')
        )
        
        # Tous les millésimes de l'organisation
        vintages = list(
            Vintage.objects.filter(organization=organization)
            .values('id', 'year')
            .order_by('-year')
        )
        
        # Couleurs disponibles (types d'appellations)
        colors = list(
            Appellation.objects.filter(organization=organization)
            .values_list('type', flat=True)
            .distinct()
            .order_by('type')
        )
        
        facets = {
            'appellations': [
                {
                    'id': str(a['id']),
                    'name': a['name'],
                    'type': a['type']
                }
                for a in appellations
            ],
            'vintages': [
                {
                    'id': str(v['id']),
                    'year': v['year']
                }
                for v in vintages
            ],
            'colors': [
                {'value': color, 'label': color.title()}
                for color in colors if color
            ]
        }
        
        # Cache pendant 5 minutes
        cache.set(cache_key, facets, 300)
        
        return JsonResponse(facets)
        
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_membership()
@require_http_methods(["GET", "PUT"])
def catalogue_detail_api(request, cuvee_id):
    """
    API endpoint pour le détail d'une cuvée
    GET /api/catalogue/:id - Récupérer les détails
    PUT /api/catalogue/:id - Modifier avec locking optimiste
    
    Headers PUT:
    - If-Match: row_version (requis pour locking optimiste)
    
    Retourne:
    {
        "id": "...",
        "name": "...",
        "code": "...",
        "appellation": {...},
        "vintage": {...},
        "default_uom": {...},
        "media": {...},
        "stats": {"lots_count": 0, "last_update": "..."},
        "row_version": 1,
        "created_at": "...",
        "updated_at": "..."
    }
    """
    organization = request.current_org
    
    try:
        # Récupérer la cuvée avec optimisations
        cuvee = Cuvee.objects.select_related(
            'appellation', 'vintage', 'default_uom'
        ).get(
            id=cuvee_id,
            organization=organization,
            is_active=True
        )
        
        if request.method == 'GET':
            return _get_cuvee_detail(cuvee)
        
        elif request.method == 'PUT':
            return _update_cuvee_detail(request, cuvee)
            
    except Cuvee.DoesNotExist:
        return JsonResponse({
            'error': 'Cuvée non trouvée'
        }, status=404)
    except Exception as e:
        logger.error(f"Erreur API catalogue detail: {e}")
        return JsonResponse({
            'error': 'Erreur interne du serveur'
        }, status=500)


@login_required
@require_membership()
@require_http_methods(["POST"])
def create_vineyard_plot_api(request):
    """
    Crée une parcelle (VineyardPlot) via AJAX sans quitter le formulaire cuvée.
    POST JSON attendu:
    {
        "name": "Parcelle A",
        "area_ha": "1.2500",
        "grape_variety_id": "<uuid>",
        "appellation_name": "Bordeaux AOC" (optionnel),
        "planting_year": 2005 (optionnel)
    }
    Retourne 201 + {id, name}
    """
    organization = request.current_org
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)

    name = (data.get('name') or '').strip()
    area_ha = (data.get('area_ha') or '').strip()
    grape_variety_id = (data.get('grape_variety_id') or '').strip()
    appellation_name = (data.get('appellation_name') or '').strip()
    planting_year = data.get('planting_year')

    errors = {}
    if not name:
        errors['name'] = 'Le nom est requis.'
    if not area_ha:
        errors['area_ha'] = 'La surface (ha) est requise.'
    if not grape_variety_id:
        errors['grape_variety_id'] = 'Le cépage est requis.'
    if errors:
        return JsonResponse({'error': 'Erreur de validation', 'details': errors}, status=400)

    # Résolution des FK
    try:
        gv = GrapeVariety.objects.get(id=grape_variety_id, organization=organization)
    except GrapeVariety.DoesNotExist:
        return JsonResponse({'error': 'Cépage introuvable'}, status=400)

    app = None
    if appellation_name:
        app = Appellation.objects.filter(organization=organization, name__iexact=appellation_name).first()
        if not app:
            app = Appellation.objects.create(
                organization=organization,
                name=appellation_name,
                type='autre',
            )

    # Création de la parcelle
    from decimal import Decimal
    try:
        planting_year_int = int(planting_year) if planting_year not in (None, '', []) else None
    except Exception:
        planting_year_int = None

    try:
        vp = VineyardPlot.objects.create(
            organization=organization,
            name=name,
            area_ha=Decimal(area_ha),
            grape_variety=gv,
            appellation=app,
            planting_year=planting_year_int,
        )
        return JsonResponse({'id': str(vp.id), 'name': vp.name}, status=201)
    except ValidationError as e:
        return JsonResponse({'error': 'Erreur de validation', 'details': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=400)
    except Exception as e:
        logger.error(f"Erreur création parcelle: {e}")
        return JsonResponse({'error': 'Erreur interne du serveur'}, status=500)


def _get_cuvee_detail(cuvee):
    """Formatage des détails d'une cuvée pour l'API"""
    
    # Statistiques (lots, lots techniques, tirages, dernière modification)
    lots_count = cuvee.lots.count() if hasattr(cuvee, 'lots') else 0
    lots_techniques_count = getattr(cuvee, 'lots_techniques', None)
    lots_techniques_count = lots_techniques_count.count() if lots_techniques_count is not None else 0
    tirages_count = getattr(cuvee, 'lots_commerciaux', None)
    tirages_count = tirages_count.count() if tirages_count is not None else 0
    skus_count = 0
    try:
        skus_count = SKU.objects.filter(product__cuvee=cuvee).count()
    except Exception:
        skus_count = 0
    stats = {
        'lots_count': lots_count,
        'lots_techniques_count': lots_techniques_count,
        'tirages_count': tirages_count,
        'skus_count': skus_count,
        'last_update': cuvee.updated_at.isoformat()
    }
    
    # Médias (étiquette principale)
    # TODO: Intégrer avec le système de médias
    media = {
        'main_image': None,  # À implémenter avec le système de médias
        'gallery': []
    }
    
    # Bloc modèle (si présent)
    model_block = None
    try:
        if getattr(cuvee, 'model_id', None):
            model_block = {
                'id': str(cuvee.model.id),
                'name': cuvee.model.name,
                'appellation_target': {
                    'id': str(cuvee.model.appellation_target.id) if cuvee.model.appellation_target else None,
                    'name': cuvee.model.appellation_target.name if cuvee.model.appellation_target else None,
                    'type': cuvee.model.appellation_target.type if cuvee.model.appellation_target else None,
                } if cuvee.model.appellation_target else None,
            }
    except Exception:
        model_block = None

    data = {
        'id': str(cuvee.id),
        'name': cuvee.name,
        'code': cuvee.code or '',
        'model': model_block,
        'appellation': {
            'id': str(cuvee.appellation.id) if cuvee.appellation else None,
            'name': cuvee.appellation.name if cuvee.appellation else None,
            'type': cuvee.appellation.type if cuvee.appellation else None
        } if cuvee.appellation else None,
        'vintage': {
            'id': str(cuvee.vintage.id) if cuvee.vintage else None,
            'year': cuvee.vintage.year if cuvee.vintage else None
        } if cuvee.vintage else None,
        'default_uom': {
            'id': str(cuvee.default_uom.id),
            'name': cuvee.default_uom.name,
            'code': cuvee.default_uom.code
        },
        'media': media,
        'stats': stats,
        'row_version': cuvee.row_version,
        'created_at': cuvee.created_at.isoformat(),
        'updated_at': cuvee.updated_at.isoformat()
    }
    
    return JsonResponse(data)


def _update_cuvee_detail(request, cuvee):
    """Mise à jour d'une cuvée avec locking optimiste"""
    
    # Vérification du header If-Match pour locking optimiste
    if_match = request.headers.get('If-Match')
    if not if_match:
        return JsonResponse({
            'error': 'Header If-Match requis pour la modification'
        }, status=400)
    
    try:
        expected_version = int(if_match)
    except ValueError:
        return JsonResponse({
            'error': 'Header If-Match doit être un entier'
        }, status=400)
    
    # Vérification du conflit de version
    if cuvee.row_version != expected_version:
        return JsonResponse({
            'error': 'Conflit de version détecté',
            'current_version': cuvee.row_version,
            'expected_version': expected_version,
            'message': 'La cuvée a été modifiée par un autre utilisateur. Veuillez actualiser et réessayer.'
        }, status=409)
    
    try:
        # Parser les données JSON
        data = json.loads(request.body)
        
        # Validation et mise à jour des champs
        if 'name' in data:
            if not data['name'].strip():
                return JsonResponse({
                    'error': 'Le nom de la cuvée est requis'
                }, status=400)
            cuvee.name = data['name'].strip()
        
        if 'code' in data:
            cuvee.code = data['code'].strip() if data['code'] else ''
        
        # Mise à jour des relations FK avec validation same-org
        if 'appellation_id' in data:
            if data['appellation_id']:
                try:
                    appellation = Appellation.objects.get(
                        id=data['appellation_id'],
                        organization=cuvee.organization
                    )
                    cuvee.appellation = appellation
                except Appellation.DoesNotExist:
                    return JsonResponse({
                        'error': 'Appellation non trouvée'
                    }, status=400)
            else:
                cuvee.appellation = None
        
        if 'vintage_id' in data:
            if data['vintage_id']:
                try:
                    vintage = Vintage.objects.get(
                        id=data['vintage_id'],
                        organization=cuvee.organization
                    )
                    cuvee.vintage = vintage
                except Vintage.DoesNotExist:
                    return JsonResponse({
                        'error': 'Millésime non trouvé'
                    }, status=400)
            else:
                cuvee.vintage = None
        
        if 'default_uom_id' in data:
            if not data['default_uom_id']:
                return JsonResponse({
                    'error': 'L\'unité de mesure par défaut est requise'
                }, status=400)
            try:
                uom = UnitOfMeasure.objects.get(
                    id=data['default_uom_id'],
                    organization=cuvee.organization
                )
                cuvee.default_uom = uom
            except UnitOfMeasure.DoesNotExist:
                return JsonResponse({
                    'error': 'Unité de mesure non trouvée'
                }, status=400)
        
        # Validation complète du modèle
        cuvee.full_clean()
        
        # Sauvegarde (row_version sera incrémenté automatiquement)
        cuvee.save()
        
        # Invalider le cache
        cache_keys_to_delete = [
            f"catalogue_api_v2:{cuvee.organization.id}",
            f"catalogue_facets:{cuvee.organization.id}"
        ]
        for cache_key in cache_keys_to_delete:
            cache.delete(cache_key)
        
        # Retourner les données mises à jour
        return _get_cuvee_detail(cuvee)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Données JSON invalides'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'error': 'Erreur de validation',
            'details': e.message_dict if hasattr(e, 'message_dict') else str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la cuvée {cuvee.id}: {e}")
        return JsonResponse({
            'error': 'Erreur interne du serveur'
        }, status=500)
