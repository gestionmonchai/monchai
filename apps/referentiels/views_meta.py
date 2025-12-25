"""
Vues Meta pour les référentiels (Parcelle, etc.)
================================================

Implémente le système MetaDetailView pour les objets référentiels.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from apps.core.views import MetaDetailView
from apps.core.models import TimelineEvent
from .models import Parcelle, ParcelleEncepagement


class ParcelleMetaDetailView(LoginRequiredMixin, MetaDetailView):
    """
    Vue détail Parcelle avec modes : fiche, timeline, relations, carte
    
    URL: /referentiels/parcelles/<pk>/
    """
    model = Parcelle
    meta_modes = ['fiche', 'timeline', 'relations', 'carte']
    template_prefix = 'referentiels/parcelles/'
    context_object_name = 'parcelle'
    
    def get_summary_cards(self):
        """Cards résumées pour la fiche parcelle"""
        parcelle = self.object
        
        return [
            {
                'icon': 'bi-rulers',
                'label': 'Surface',
                'value': f"{parcelle.surface} ha",
                'color': '#3b82f6',
            },
            {
                'icon': 'bi-geo-alt',
                'label': 'Commune',
                'value': parcelle.commune or '-',
                'color': '#10b981',
            },
            {
                'icon': 'bi-basket',
                'label': 'Récolté',
                'value': f"{parcelle.quantite_recoltee_kg} kg",
                'color': '#f59e0b',
            },
            {
                'icon': 'bi-tree',
                'label': 'Cépages',
                'value': parcelle.encepagements.count(),
                'color': '#8b5cf6',
            },
        ]
    
    def get_fiche_context(self):
        """Contexte pour la vue Fiche"""
        context = super().get_fiche_context()
        parcelle = self.object
        
        # Encépagements
        context['encepagements'] = parcelle.encepagements.select_related('cepage').all()
        
        # Certifications
        context['certifications'] = parcelle.certifications
        
        # Alertes éventuelles
        alerts = []
        if parcelle.get_encepagement_total_percent() > 100:
            alerts.append({
                'level': 'warning',
                'icon': 'exclamation-triangle',
                'message': f"L'encépagement total dépasse 100% ({parcelle.get_encepagement_total_percent()}%)"
            })
        if not parcelle.encepagements.exists():
            alerts.append({
                'level': 'info',
                'icon': 'info-circle',
                'message': "Aucun encépagement défini pour cette parcelle"
            })
        context['alerts'] = alerts
        
        return context
    
    def get_relations_config(self):
        """Configuration des relations pour la parcelle"""
        parcelle = self.object
        
        return [
            {
                'name': 'encepagements',
                'label': 'Encépagements',
                'icon': 'bi-tree',
                'model': ParcelleEncepagement,
                'lookup': 'parcelle',
                'lookup_value': parcelle.pk,
                'list_fields': ['__str__'],
                'search_fields': ['cepage__nom'],
                'ordering': '-pourcentage',
                'can_create': True,
                'create_url': reverse('referentiels:parcelle_encepagement_add', args=[parcelle.pk]) if hasattr(parcelle, 'pk') else '',
            },
            {
                'name': 'vendanges',
                'label': 'Vendanges',
                'icon': 'bi-basket',
                'model': 'production.Vendange',
                'lookup': 'parcelle',
                'lookup_value': parcelle.pk,
                'list_fields': ['__str__'],
                'search_fields': ['code', 'cepage__nom'],
                'ordering': '-date_reception',
                'can_create': True,
                'create_url': f"{reverse('production:vendange_new')}?parcelle={parcelle.pk}",
                'detail_url_name': 'production:vendange_detail',
            },
        ]
    
    def get_carte_context(self):
        """Contexte pour la vue Carte"""
        parcelle = self.object
        
        return {
            'has_coordinates': bool(parcelle.latitude and parcelle.longitude),
            'latitude': parcelle.latitude,
            'longitude': parcelle.longitude,
            'geojson': parcelle.geojson,
        }
    
    def get_tools_config(self):
        """Outils disponibles pour la parcelle"""
        parcelle = self.object
        
        return [
            {
                'name': 'export_pdf',
                'label': 'Exporter fiche PDF',
                'icon': 'bi-file-pdf',
                'url': '#',
            },
            {
                'name': 'duplicate',
                'label': 'Dupliquer',
                'icon': 'bi-copy',
                'url': '#',
            },
            {
                'name': 'journal',
                'label': 'Journal cultural',
                'icon': 'bi-journal-text',
                'url': f"{reverse('production:journal_cultural')}?parcelle={parcelle.pk}",
            },
        ]


# Alias pour compatibilité
parcelle_meta_detail = ParcelleMetaDetailView.as_view()
