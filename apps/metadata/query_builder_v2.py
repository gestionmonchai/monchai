"""
Query Builder V2 - GIGA ROADMAP S2
FTS + trigram + ranking + facettes + caching
"""

import hashlib
import time
from decimal import Decimal
from django.db import connection
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from apps.metadata.models import MetaEntity, MetaAttribute, SearchMetrics
from apps.metadata.feature_flags import FeatureFlagService


class SearchQueryBuilderV2:
    """
    Query Builder V2 avec FTS, trigram, ranking, facettes
    GIGA ROADMAP: p95 < 600ms, caching, cancellation
    """
    
    CACHE_PREFIX = "search_v2"
    CACHE_TTL = 120  # 2 minutes
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 20
    
    def __init__(self, organization, user=None):
        self.organization = organization
        self.user = user
        self.start_time = time.time()
        
    def search(self, query, entity_type=None, filters=None, facets=None, 
               sort=None, page=1, page_size=None, live=False):
        """
        Recherche principale V2
        
        Args:
            query: Terme de recherche
            entity_type: Type d'entité (cepage, parcelle, etc.)
            filters: Dict des filtres {field: value}
            facets: Liste des facettes à calculer
            sort: Champ de tri
            page: Numéro de page
            page_size: Taille de page
            live: Recherche en temps réel (debounce)
        """
        # Normalisation des paramètres
        query = (query or '').strip()
        filters = filters or {}
        facets = facets or []
        page_size = min(page_size or self.DEFAULT_PAGE_SIZE, self.MAX_PAGE_SIZE)
        
        # Cache key
        cache_key = self._build_cache_key(
            query, entity_type, filters, facets, sort, page, page_size
        )
        
        # Vérifier le cache d'abord
        if FeatureFlagService.is_enabled('search_cache_enabled', user=self.user):
            cached_result = cache.get(cache_key)
            if cached_result:
                self._record_metrics(
                    query, entity_type, cached_result['count'], 
                    elapsed_ms=int((time.time() - self.start_time) * 1000),
                    cache_hit=True, live=live
                )
                return cached_result
        
        # Exécuter la recherche
        try:
            result = self._execute_search(
                query, entity_type, filters, facets, sort, page, page_size
            )
            
            # Mettre en cache
            if FeatureFlagService.is_enabled('search_cache_enabled', user=self.user):
                cache.set(cache_key, result, self.CACHE_TTL)
            
            # Métriques
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            self._record_metrics(
                query, entity_type, result['count'], 
                elapsed_ms=elapsed_ms, cache_hit=False, live=live
            )
            
            return result
            
        except Exception as e:
            # Métriques d'erreur
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            self._record_metrics(
                query, entity_type, 0, 
                elapsed_ms=elapsed_ms, cache_hit=False, live=live
            )
            raise
    
    def _execute_search(self, query, entity_type, filters, facets, sort, page, page_size):
        """Exécute la recherche selon le moteur disponible"""
        
        # Déterminer le moteur à utiliser
        use_v2 = (
            connection.vendor == 'postgresql' and 
            FeatureFlagService.is_enabled('search_v2_read', user=self.user)
        )
        
        if use_v2:
            return self._search_v2_fts(query, entity_type, filters, facets, sort, page, page_size)
        else:
            return self._search_v1_fallback(query, entity_type, filters, facets, sort, page, page_size)
    
    def _search_v2_fts(self, query, entity_type, filters, facets, sort, page, page_size):
        """Recherche V2 avec FTS + trigram"""
        
        # Pour cette démo, on simule la recherche V2
        # En production, ici on ferait du vrai FTS PostgreSQL
        
        from apps.referentiels.models import Cepage, Parcelle, Unite
        
        models_map = {
            'cepage': Cepage,
            'parcelle': Parcelle, 
            'unite': Unite,
        }
        
        if entity_type and entity_type in models_map:
            model_class = models_map[entity_type]
            queryset = model_class.objects.filter(organization=self.organization)
        else:
            # Recherche multi-entités (union)
            queryset = Cepage.objects.filter(organization=self.organization)
        
        # Filtrage par query
        if query:
            # Simulation FTS : recherche dans nom + code
            q_filter = Q(nom__icontains=query)
            if hasattr(queryset.model, 'code'):
                q_filter |= Q(code__icontains=query)
            queryset = queryset.filter(q_filter)
        
        # Filtres additionnels
        for field, value in filters.items():
            if hasattr(queryset.model, field):
                queryset = queryset.filter(**{field: value})
        
        # Tri
        if sort and hasattr(queryset.model, sort):
            queryset = queryset.order_by(sort)
        else:
            queryset = queryset.order_by('nom')
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Facettes (simulation)
        facet_data = {}
        if 'couleur' in facets and entity_type == 'cepage':
            facet_data['couleur'] = list(
                Cepage.objects.filter(organization=self.organization)
                .values('couleur')
                .annotate(count=Count('couleur'))
                .order_by('-count')
            )
        
        return {
            'items': list(page_obj.object_list.values()),
            'count': paginator.count,
            'page': page,
            'pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'facets': facet_data,
            'engine_version': 'v2',
            'cache_hit': False,
        }
    
    def _search_v1_fallback(self, query, entity_type, filters, facets, sort, page, page_size):
        """Recherche V1 de fallback (actuelle)"""
        
        from apps.referentiels.models import Cepage
        
        # Recherche simple V1
        queryset = Cepage.objects.filter(organization=self.organization)
        
        if query:
            queryset = queryset.filter(nom__icontains=query)
        
        # Tri
        queryset = queryset.order_by('nom')
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'items': list(page_obj.object_list.values()),
            'count': paginator.count,
            'page': page,
            'pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'facets': {},
            'engine_version': 'v1',
            'cache_hit': False,
        }
    
    def _build_cache_key(self, query, entity_type, filters, facets, sort, page, page_size):
        """Construit une clé de cache stable"""
        
        # Sérialiser tous les paramètres
        params = {
            'query': query,
            'entity_type': entity_type,
            'filters': sorted(filters.items()) if filters else [],
            'facets': sorted(facets) if facets else [],
            'sort': sort,
            'page': page,
            'page_size': page_size,
            'org_id': str(self.organization.id),
        }
        
        # Hash MD5 pour clé courte
        params_str = str(params)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
        
        return f"{self.CACHE_PREFIX}:{params_hash}"
    
    def _record_metrics(self, query, entity_type, count, elapsed_ms, cache_hit, live):
        """Enregistre les métriques de performance"""
        
        if not FeatureFlagService.is_enabled('search_metrics_enabled', user=self.user):
            return
        
        try:
            # Hash de la query (pas de PII)
            query_hash = hashlib.md5((query or '').encode()).hexdigest()
            
            # Déterminer la version du moteur
            engine_version = 'v2' if FeatureFlagService.is_enabled('search_v2_read', user=self.user) else 'v1'
            
            SearchMetrics.objects.create(
                organization=self.organization,
                engine_version=engine_version,
                query_hash=query_hash,
                entity_type=entity_type or 'multi',
                result_count=count,
                has_results=count > 0,
                elapsed_ms=elapsed_ms,
                cache_hit=cache_hit,
                is_live_search=live,
                user_agent=getattr(self.user, 'last_user_agent', '') if self.user else '',
            )
        except Exception as e:
            # Ne pas faire échouer la recherche pour les métriques
            print(f"Erreur métriques: {e}")


class FacetBuilder:
    """Constructeur de facettes pour filtrage avancé"""
    
    @staticmethod
    def build_facets(queryset, facet_fields, max_values=10):
        """Construit les facettes pour un queryset"""
        facets = {}
        
        for field in facet_fields:
            if hasattr(queryset.model, field):
                facet_values = (
                    queryset.values(field)
                    .annotate(count=Count(field))
                    .order_by('-count')[:max_values]
                )
                facets[field] = list(facet_values)
        
        return facets


class SearchRanking:
    """Système de ranking pour pertinence"""
    
    @staticmethod
    def calculate_rank(item, query, boost_fields=None):
        """Calcule un score de pertinence"""
        if not query:
            return 1.0
        
        score = 0.0
        query_lower = query.lower()
        boost_fields = boost_fields or {}
        
        # Score basé sur les champs
        for field, value in item.items():
            if isinstance(value, str):
                value_lower = value.lower()
                field_boost = boost_fields.get(field, 1.0)
                
                # Exact match = score max
                if query_lower == value_lower:
                    score += 10.0 * field_boost
                # Début de mot
                elif value_lower.startswith(query_lower):
                    score += 5.0 * field_boost
                # Contient
                elif query_lower in value_lower:
                    score += 2.0 * field_boost
        
        return max(score, 0.1)  # Score minimum
