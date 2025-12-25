"""
MetaDetailView - Système de vues standardisées pour objets métier
================================================================

Fournit un système unifié de vues détail avec modes :
- fiche : état courant + attributs
- timeline : journal d'événements
- relations : données liées avec recherche HTMX
- documents : pièces jointes
- + modes personnalisés

Usage:
    class ParcelleDetailView(MetaDetailView):
        model = Parcelle
        meta_modes = ['fiche', 'timeline', 'relations', 'carte']
        
        def get_fiche_context(self):
            return {'stats': self.get_stats()}
        
        def get_relations_config(self):
            return [
                {'name': 'interventions', 'model': Intervention, 'lookup': 'parcelle'},
                {'name': 'analyses', 'model': Analyse, 'lookup': 'parcelle'},
            ]
"""

from django.views.generic import DetailView
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.apps import apps

from apps.core.models import TimelineEvent, Document


class MetaDetailMixin:
    """
    Mixin pour ajouter les fonctionnalités meta view à n'importe quelle DetailView.
    """
    
    # Modes disponibles pour cette vue
    meta_modes = ['fiche', 'timeline', 'relations']
    
    # Mode par défaut
    default_mode = 'fiche'
    
    # Template de base pour le layout meta
    meta_template_name = 'core/meta/base_meta_detail.html'
    
    # Préfixe pour les templates de mode (ex: 'parcelles/' -> 'parcelles/fiche.html')
    template_prefix = ''
    
    # Pagination
    timeline_per_page = 20
    relations_per_page = 15
    
    def get_current_mode(self):
        """Récupère le mode actuel depuis l'URL ou les paramètres"""
        mode = self.kwargs.get('mode') or self.request.GET.get('mode', self.default_mode)
        if mode not in self.meta_modes:
            mode = self.default_mode
        return mode
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.get_current_mode()
        
        # Contexte de base meta
        context['meta'] = {
            'modes': self.get_available_modes(),
            'current_mode': mode,
            'object_type': self.model._meta.verbose_name,
            'object_type_plural': self.model._meta.verbose_name_plural,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
        }
        
        # Ajouter le contexte spécifique au mode
        mode_context_method = getattr(self, f'get_{mode}_context', None)
        if mode_context_method:
            context.update(mode_context_method())
        
        # Outils disponibles (section repliée)
        context['tools'] = self.get_tools_config()
        
        return context
    
    def get_available_modes(self):
        """Retourne la liste des modes avec leur configuration"""
        modes_config = {
            'fiche': {'label': 'Fiche', 'icon': 'bi-card-text'},
            'timeline': {'label': 'Timeline', 'icon': 'bi-clock-history'},
            'relations': {'label': 'Relations', 'icon': 'bi-diagram-3'},
            'documents': {'label': 'Documents', 'icon': 'bi-folder'},
            'carte': {'label': 'Carte', 'icon': 'bi-geo-alt'},
            'kpi': {'label': 'KPI', 'icon': 'bi-graph-up'},
            'conformite': {'label': 'Conformité', 'icon': 'bi-check-circle'},
        }
        
        return [
            {
                'name': mode,
                'label': modes_config.get(mode, {}).get('label', mode.title()),
                'icon': modes_config.get(mode, {}).get('icon', 'bi-circle'),
                'active': mode == self.get_current_mode(),
            }
            for mode in self.meta_modes
        ]
    
    def get_tools_config(self):
        """Retourne la configuration des outils (actions utilitaires)"""
        return [
            {'name': 'export_pdf', 'label': 'Exporter PDF', 'icon': 'bi-file-pdf', 'url': '#'},
            {'name': 'duplicate', 'label': 'Dupliquer', 'icon': 'bi-copy', 'url': '#'},
            {'name': 'archive', 'label': 'Archiver', 'icon': 'bi-archive', 'url': '#'},
        ]
    
    def get_template_names(self):
        """Retourne le template approprié selon le mode"""
        mode = self.get_current_mode()
        
        # Si requête HTMX, retourner le partial
        if self.request.headers.get('HX-Request'):
            return [f'core/meta/partials/_{mode}.html']
        
        # Template spécifique au modèle si existe
        if self.template_prefix:
            specific_template = f'{self.template_prefix}{mode}.html'
            return [specific_template, self.meta_template_name]
        
        return [self.meta_template_name]
    
    # =========================================
    # CONTEXTE MODE FICHE
    # =========================================
    
    def get_fiche_context(self):
        """Contexte pour la vue Fiche - à surcharger"""
        obj = self.object
        
        # Dernier événement
        last_event = TimelineEvent.objects.filter(
            target_content_type=ContentType.objects.get_for_model(obj),
            target_object_id=str(obj.pk)
        ).first()
        
        # Compteurs résumés
        events_count = TimelineEvent.objects.filter(
            target_content_type=ContentType.objects.get_for_model(obj),
            target_object_id=str(obj.pk)
        ).count()
        
        docs_count = Document.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=str(obj.pk)
        ).count()
        
        return {
            'last_event': last_event,
            'events_count': events_count,
            'documents_count': docs_count,
            'summary_cards': self.get_summary_cards(),
        }
    
    def get_summary_cards(self):
        """Cards résumées à afficher sur la fiche - à surcharger"""
        return []
    
    # =========================================
    # CONTEXTE MODE TIMELINE
    # =========================================
    
    def get_timeline_context(self):
        """Contexte pour la vue Timeline"""
        obj = self.object
        ct = ContentType.objects.get_for_model(obj)
        
        # Filtres
        event_type = self.request.GET.get('event_type', '')
        search = self.request.GET.get('q', '')
        page = self.request.GET.get('page', 1)
        
        # Query de base
        events = TimelineEvent.objects.filter(
            target_content_type=ct,
            target_object_id=str(obj.pk),
            is_visible=True
        )
        
        # Appliquer filtres
        if event_type:
            events = events.filter(event_type=event_type)
        if search:
            events = events.filter(
                Q(title__icontains=search) | Q(summary__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(events, self.timeline_per_page)
        page_obj = paginator.get_page(page)
        
        # Types d'événements pour filtres
        event_types = TimelineEvent.EVENT_TYPES
        
        return {
            'timeline_events': page_obj,
            'timeline_paginator': paginator,
            'timeline_page': page_obj,
            'event_types': event_types,
            'current_event_type': event_type,
            'timeline_search': search,
            'can_add_event': self.can_add_timeline_event(),
        }
    
    def can_add_timeline_event(self):
        """Vérifie si l'utilisateur peut ajouter des événements"""
        return self.request.user.is_authenticated
    
    # =========================================
    # CONTEXTE MODE RELATIONS
    # =========================================
    
    def get_relations_context(self):
        """Contexte pour la vue Relations"""
        relations = self.get_relations_config()
        
        # Charger les données pour chaque relation
        relations_data = []
        for rel in relations:
            rel_data = self.load_relation_data(rel)
            relations_data.append(rel_data)
        
        return {
            'relations': relations_data,
        }
    
    def get_relations_config(self):
        """Configuration des relations à afficher - à surcharger"""
        return []
    
    def load_relation_data(self, rel_config):
        """Charge les données pour une relation"""
        obj = self.object
        
        # Récupérer le modèle
        model_path = rel_config.get('model')
        if isinstance(model_path, str):
            app_label, model_name = model_path.rsplit('.', 1)
            Model = apps.get_model(app_label, model_name)
        else:
            Model = model_path
        
        # Query
        lookup = rel_config.get('lookup', 'id')
        lookup_value = rel_config.get('lookup_value', obj.pk)
        
        queryset = Model.objects.filter(**{lookup: lookup_value})
        
        # Recherche si spécifiée
        section_id = rel_config.get('name', '')
        search = self.request.GET.get(f'search_{section_id}', '')
        if search and rel_config.get('search_fields'):
            q = Q()
            for field in rel_config['search_fields']:
                q |= Q(**{f'{field}__icontains': search})
            queryset = queryset.filter(q)
        
        # Tri
        ordering = rel_config.get('ordering', '-pk')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        page = self.request.GET.get(f'page_{section_id}', 1)
        paginator = Paginator(queryset, self.relations_per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'name': rel_config.get('name', ''),
            'label': rel_config.get('label', Model._meta.verbose_name_plural),
            'icon': rel_config.get('icon', 'bi-link'),
            'items': page_obj,
            'paginator': paginator,
            'page': page_obj,
            'total_count': paginator.count,
            'search': search,
            'search_fields': rel_config.get('search_fields', []),
            'list_fields': rel_config.get('list_fields', ['__str__']),
            'can_create': rel_config.get('can_create', False),
            'create_url': rel_config.get('create_url', ''),
            'can_link': rel_config.get('can_link', False),
            'detail_url_name': rel_config.get('detail_url_name', ''),
        }
    
    # =========================================
    # CONTEXTE MODE DOCUMENTS
    # =========================================
    
    def get_documents_context(self):
        """Contexte pour la vue Documents"""
        obj = self.object
        ct = ContentType.objects.get_for_model(obj)
        
        # Filtres
        category = self.request.GET.get('category', '')
        search = self.request.GET.get('q', '')
        page = self.request.GET.get('page', 1)
        
        # Query
        docs = Document.objects.filter(
            content_type=ct,
            object_id=str(obj.pk)
        )
        
        if category:
            docs = docs.filter(category=category)
        if search:
            docs = docs.filter(
                Q(title__icontains=search) | Q(filename__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(docs, self.relations_per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'documents': page_obj,
            'documents_paginator': paginator,
            'documents_page': page_obj,
            'document_categories': Document.CATEGORIES,
            'current_category': category,
            'documents_search': search,
            'can_upload': self.request.user.is_authenticated,
        }


class MetaDetailView(MetaDetailMixin, DetailView):
    """
    Vue détail avec système de modes (fiche, timeline, relations, etc.)
    
    Usage:
        class ParcelleDetailView(MetaDetailView):
            model = Parcelle
            meta_modes = ['fiche', 'timeline', 'relations', 'carte']
            template_prefix = 'production/parcelles/'
    """
    pass


# =========================================
# FONCTIONS UTILITAIRES
# =========================================

def get_timeline_for_object(obj, limit=10, event_type=None):
    """
    Récupère la timeline d'un objet.
    
    Usage:
        events = get_timeline_for_object(parcelle, limit=5)
    """
    ct = ContentType.objects.get_for_model(obj)
    
    qs = TimelineEvent.objects.filter(
        target_content_type=ct,
        target_object_id=str(obj.pk),
        is_visible=True
    )
    
    if event_type:
        qs = qs.filter(event_type=event_type)
    
    return qs[:limit]


def get_relations_for_object(obj, relations_config):
    """
    Récupère les relations d'un objet selon une configuration.
    
    Usage:
        relations = get_relations_for_object(parcelle, [
            {'model': 'production.Intervention', 'lookup': 'parcelle'},
        ])
    """
    results = {}
    
    for rel in relations_config:
        model_path = rel.get('model')
        if isinstance(model_path, str):
            app_label, model_name = model_path.rsplit('.', 1)
            Model = apps.get_model(app_label, model_name)
        else:
            Model = model_path
        
        lookup = rel.get('lookup', 'id')
        queryset = Model.objects.filter(**{lookup: obj.pk})
        
        if rel.get('ordering'):
            queryset = queryset.order_by(rel['ordering'])
        
        results[rel.get('name', Model._meta.model_name)] = queryset
    
    return results


# =========================================
# VUES HTMX POUR PARTIALS
# =========================================

def timeline_partial_view(request, content_type_id, object_id):
    """
    Vue HTMX pour charger/filtrer la timeline.
    URL: /core/timeline/<ct_id>/<obj_id>/
    """
    ct = ContentType.objects.get(id=content_type_id)
    
    # Vérifier accès tenant
    Model = ct.model_class()
    obj = Model.objects.get(pk=object_id)
    
    # Filtres
    event_type = request.GET.get('event_type', '')
    search = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    events = TimelineEvent.objects.filter(
        target_content_type=ct,
        target_object_id=str(object_id),
        is_visible=True
    )
    
    if event_type:
        events = events.filter(event_type=event_type)
    if search:
        events = events.filter(
            Q(title__icontains=search) | Q(summary__icontains=search)
        )
    
    paginator = Paginator(events, 20)
    page_obj = paginator.get_page(page)
    
    html = render_to_string('core/meta/partials/_timeline_list.html', {
        'timeline_events': page_obj,
        'timeline_page': page_obj,
        'content_type_id': content_type_id,
        'object_id': object_id,
    }, request=request)
    
    return HttpResponse(html)


def relations_partial_view(request, content_type_id, object_id, relation_name):
    """
    Vue HTMX pour charger/filtrer une section relation.
    URL: /core/relations/<ct_id>/<obj_id>/<relation_name>/
    """
    ct = ContentType.objects.get(id=content_type_id)
    Model = ct.model_class()
    obj = Model.objects.get(pk=object_id)
    
    # Récupérer la config de relation depuis la vue
    # Cette fonction nécessite que la config soit passée ou stockée
    
    search = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    # Pour l'instant, retourner un placeholder
    # La vraie implémentation dépend de la config de relation
    
    return HttpResponse('<div class="text-muted">Relation data...</div>')
