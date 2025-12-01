"""
Services pour la gestion des clients - Roadmap 36
Recherche FTS + trigram + keyset pagination + facettes
"""

from decimal import Decimal
from django.db import models
from django.db.models import Q, Count, Case, When, Value, CharField
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.core.cache import cache
import hashlib
import json


class CustomerSearchService:
    """Service de recherche clients avec FTS + trigram + keyset pagination - Roadmap 36"""
    
    # Configuration
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    CACHE_TTL = 120  # 2 minutes
    
    # Whitelist des champs de tri autorisés
    ALLOWED_SORT_FIELDS = [
        'name', 'updated_at', 'created_at', 'segment', 'country_code'
    ]
    
    # Whitelist des filtres autorisés
    ALLOWED_FILTERS = [
        'segment', 'country_code', 'is_active', 'tags'
    ]
    
    @staticmethod
    def search_customers(organization, query_params=None):
        """
        Recherche clients avec filtres, tri et pagination keyset
        
        Args:
            organization: Organisation courante
            query_params: Paramètres de requête (q, segment, tags[], country, sort, cursor, page_size)
            
        Returns:
            dict: {
                'items': [...],
                'next_cursor': str,
                'facets': {...},
                'perf': {...}
            }
        """
        import time
        start_time = time.time()
        
        if query_params is None:
            query_params = {}
        
        # Paramètres de recherche
        q = query_params.get('q', '').strip()
        segment = query_params.get('segment', '')
        tags = query_params.getlist('tags[]') or query_params.getlist('tags')
        country = query_params.get('country', '')
        sort_by = query_params.get('sort', 'updated_at')
        cursor = query_params.get('cursor', '')
        page_size = min(int(query_params.get('page_size', CustomerSearchService.DEFAULT_PAGE_SIZE)), 
                       CustomerSearchService.MAX_PAGE_SIZE)
        
        # Validation des paramètres
        if sort_by not in CustomerSearchService.ALLOWED_SORT_FIELDS:
            sort_by = 'updated_at'
        
        # Construction de la requête de base
        from .models import Customer
        
        queryset = Customer.objects.filter(
            organization=organization
        ).select_related('organization').prefetch_related('tag_links__tag')
        
        # Application des filtres
        if segment and segment in dict(Customer.SEGMENT_CHOICES):
            queryset = queryset.filter(segment=segment)
        
        if country:
            queryset = queryset.filter(country_code=country)
        
        if 'is_active' in query_params:
            is_active = query_params.get('is_active', '').lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active)
        
        if tags:
            queryset = queryset.filter(tag_links__tag__name__in=tags).distinct()
        
        # Recherche textuelle
        if q:
            queryset = CustomerSearchService._apply_text_search(queryset, q)
        
        # Application du tri et pagination keyset
        items, next_cursor = CustomerSearchService._apply_keyset_pagination(
            queryset, sort_by, cursor, page_size
        )
        
        # Sérialisation des résultats
        serialized_items = []
        for customer in items:
            # Récupération des tags
            customer_tags = [link.tag.name for link in customer.tag_links.all()]
            
            # Dernière activité (si disponible)
            last_activity = customer.activities.first()
            last_activity_at = last_activity.activity_date if last_activity else None
            
            serialized_items.append({
                'id': str(customer.id),
                'name': customer.name,
                'segment': customer.segment,
                'segment_display': customer.get_segment_display(),
                'email': customer.email,
                'phone': customer.phone,
                'vat_number': customer.vat_number,
                'country_code': customer.country_code,
                'is_active': customer.is_active,
                'tags': customer_tags,
                'last_activity_at': last_activity_at.isoformat() if last_activity_at else None,
                'created_at': customer.created_at.isoformat(),
                'updated_at': customer.updated_at.isoformat(),
            })
        
        # Calcul des facettes
        facets = CustomerSearchService._calculate_facets(organization, query_params)
        
        # Métriques de performance
        end_time = time.time()
        perf = {
            'query_time_ms': round((end_time - start_time) * 1000, 2),
            'result_count': len(serialized_items),
            'has_next': bool(next_cursor),
        }
        
        return {
            'customers': serialized_items,  # Changé de 'items' à 'customers' pour compatibilité frontend
            'items': serialized_items,      # Gardé pour rétrocompatibilité
            'total': len(serialized_items),
            'next_cursor': next_cursor,
            'facets': facets,
            'perf': perf
        }
    
    @staticmethod
    def _apply_text_search(queryset, query):
        """
        Application de la recherche textuelle compatible SQLite et PostgreSQL
        """
        from django.db import connection
        from django.db.models import Q
        
        # Recherche compatible SQLite avec LIKE et icontains
        search_terms = query.lower().split()
        search_q = Q()
        
        for term in search_terms:
            term_q = (
                Q(name__icontains=term) |
                Q(email__icontains=term) |
                Q(phone__icontains=term) |
                Q(vat_number__icontains=term)
            )
            search_q &= term_q
        
        if search_q:
            queryset = queryset.filter(search_q)
        
        return queryset
    
    @staticmethod
    def _apply_keyset_pagination(queryset, sort_by, cursor, page_size):
        """
        Application de la pagination keyset pour éviter les trous/doublons
        """
        # Tri par défaut : updated_at DESC, id DESC pour stabilité
        if sort_by == 'updated_at':
            order_fields = ['-updated_at', '-id']
        elif sort_by == 'name':
            order_fields = ['name', 'id']
        elif sort_by == 'created_at':
            order_fields = ['-created_at', '-id']
        elif sort_by == 'segment':
            order_fields = ['segment', 'name', 'id']
        else:
            order_fields = ['-updated_at', '-id']
        
        queryset = queryset.order_by(*order_fields)
        
        # Application du curseur si fourni
        if cursor:
            try:
                import base64
                cursor_data = json.loads(base64.b64decode(cursor).decode('utf-8'))
                
                if sort_by == 'updated_at':
                    queryset = queryset.filter(
                        Q(updated_at__lt=cursor_data['updated_at']) |
                        Q(updated_at=cursor_data['updated_at'], id__lt=cursor_data['id'])
                    )
                elif sort_by == 'name':
                    queryset = queryset.filter(
                        Q(name__gt=cursor_data['name']) |
                        Q(name=cursor_data['name'], id__gt=cursor_data['id'])
                    )
                # Ajouter d'autres cas selon les besoins
                
            except (ValueError, KeyError, json.JSONDecodeError):
                # Curseur invalide, ignorer
                pass
        
        # Récupération des résultats + 1 pour détecter s'il y a une page suivante
        items = list(queryset[:page_size + 1])
        
        has_next = len(items) > page_size
        if has_next:
            items = items[:page_size]
        
        # Génération du curseur suivant
        next_cursor = None
        if has_next and items:
            last_item = items[-1]
            cursor_data = {
                'id': str(last_item.id),
            }
            
            if sort_by == 'updated_at':
                cursor_data['updated_at'] = last_item.updated_at.isoformat()
            elif sort_by == 'name':
                cursor_data['name'] = last_item.name
            
            import base64
            next_cursor = base64.b64encode(
                json.dumps(cursor_data).encode('utf-8')
            ).decode('utf-8')
        
        return items, next_cursor
    
    @staticmethod
    def _calculate_facets(organization, query_params):
        """
        Calcul des facettes pour les filtres
        """
        from .models import Customer, CustomerTag
        
        # Cache key basé sur l'organisation et les paramètres
        cache_key = f"customer_facets_{organization.id}_{hashlib.md5(str(query_params).encode()).hexdigest()}"
        cached_facets = cache.get(cache_key)
        if cached_facets:
            return cached_facets
        
        base_queryset = Customer.objects.filter(organization=organization)
        
        # Facettes par segment
        segment_facets = list(
            base_queryset.values('segment')
            .annotate(count=Count('id'))
            .order_by('segment')
        )
        
        # Facettes par pays
        country_facets = list(
            base_queryset.exclude(country_code__isnull=True)
            .exclude(country_code='')
            .values('country_code')
            .annotate(count=Count('id'))
            .order_by('country_code')
        )
        
        # Facettes par tags
        tag_facets = list(
            CustomerTag.objects.filter(organization=organization)
            .annotate(count=Count('customer_links'))
            .values('name', 'count')
            .order_by('-count', 'name')[:20]  # Top 20 tags
        )
        
        facets = {
            'segment': [
                {
                    'value': item['segment'],
                    'label': dict(Customer.SEGMENT_CHOICES).get(item['segment'], item['segment']),
                    'count': item['count']
                }
                for item in segment_facets
            ],
            'country': [
                {
                    'value': item['country_code'],
                    'label': item['country_code'],  # Pourrait être enrichi avec le nom du pays
                    'count': item['count']
                }
                for item in country_facets
            ],
            'tags': [
                {
                    'value': item['name'],
                    'label': item['name'],
                    'count': item['count']
                }
                for item in tag_facets if item['count'] > 0
            ]
        }
        
        # Cache pendant 2 minutes
        cache.set(cache_key, facets, CustomerSearchService.CACHE_TTL)
        
        return facets
    
    @staticmethod
    def get_customer_suggestions(organization, query, limit=5):
        """
        Suggestions de clients pour autocomplétion
        """
        if not query or len(query) < 2:
            return []
        
        from .models import Customer
        
        # Cache key
        cache_key = f"customer_suggestions_{organization.id}_{hashlib.md5(query.encode()).hexdigest()}"
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            return cached_suggestions
        
        # Recherche par similarité trigram
        suggestions = list(
            Customer.objects.filter(organization=organization, is_active=True)
            .extra(
                select={'similarity': "similarity(name_norm, %s)"},
                select_params=[query.lower()],
                where=["similarity(name_norm, %s) > 0.2"],
                params=[query.lower()],
                order_by=['-similarity']
            )
            .values('id', 'name', 'segment')[:limit]
        )
        
        # Formatage des suggestions
        formatted_suggestions = [
            {
                'id': str(item['id']),
                'name': item['name'],
                'segment': item['segment'],
                'segment_display': dict(Customer.SEGMENT_CHOICES).get(item['segment'], item['segment'])
            }
            for item in suggestions
        ]
        
        # Cache pendant 5 minutes
        cache.set(cache_key, formatted_suggestions, 300)
        
        return formatted_suggestions
