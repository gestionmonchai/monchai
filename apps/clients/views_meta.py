"""
Vues Meta pour les Clients
==========================

Implémente le système MetaDetailView pour les clients.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from apps.core.views import MetaDetailView
from .models import Customer


class CustomerMetaDetailView(LoginRequiredMixin, MetaDetailView):
    """
    Vue détail Client avec modes : fiche, timeline, relations, documents
    
    URL: /referentiels/clients/<uuid:pk>/
    """
    model = Customer
    meta_modes = ['fiche', 'timeline', 'relations', 'documents']
    template_prefix = 'clients/'
    context_object_name = 'customer'
    pk_url_kwarg = 'pk'
    
    def get_summary_cards(self):
        """Cards résumées pour la fiche client"""
        customer = self.object
        
        cards = [
            {
                'icon': 'bi-tag',
                'label': 'Segment',
                'value': customer.get_segment_display(),
                'color': '#3b82f6',
            },
            {
                'icon': 'bi-check-circle' if customer.is_active else 'bi-x-circle',
                'label': 'Statut',
                'value': 'Actif' if customer.is_active else 'Inactif',
                'color': '#10b981' if customer.is_active else '#ef4444',
            },
        ]
        
        # KPIs si disponibles
        if hasattr(customer, 'ca_12m') and customer.ca_12m:
            cards.append({
                'icon': 'bi-currency-euro',
                'label': 'CA 12 mois',
                'value': f"{customer.ca_12m:,.0f} €".replace(',', ' '),
                'color': '#f59e0b',
            })
        
        if hasattr(customer, 'nb_commandes_12m') and customer.nb_commandes_12m:
            cards.append({
                'icon': 'bi-cart',
                'label': 'Commandes',
                'value': customer.nb_commandes_12m,
                'color': '#8b5cf6',
            })
        
        return cards
    
    def get_fiche_context(self):
        """Contexte pour la vue Fiche"""
        context = super().get_fiche_context()
        customer = self.object
        
        # Informations principales
        context['customer_info'] = {
            'segment': customer.get_segment_display(),
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'country': customer.country_code,
            'vat_number': customer.vat_number,
        }
        
        # Alertes
        alerts = []
        if not customer.is_active:
            alerts.append({
                'level': 'warning',
                'icon': 'exclamation-triangle',
                'message': "Ce client est actuellement inactif"
            })
        if customer.segment in ('business', 'export') and not customer.vat_number:
            alerts.append({
                'level': 'info',
                'icon': 'info-circle',
                'message': "Numéro de TVA non renseigné (recommandé pour ce type de client)"
            })
        context['alerts'] = alerts
        
        return context
    
    def get_relations_config(self):
        """Configuration des relations pour le client"""
        customer = self.object
        
        relations = [
            {
                'name': 'quotes',
                'label': 'Devis',
                'icon': 'bi-file-text',
                'model': 'commerce.Quote',
                'lookup': 'customer',
                'lookup_value': customer.pk,
                'list_fields': ['__str__'],
                'search_fields': ['reference', 'subject'],
                'ordering': '-created_at',
                'can_create': True,
                'create_url': f"{reverse('ventes:devis_new')}?customer={customer.pk}",
                'detail_url_name': 'ventes:devis_detail',
            },
            {
                'name': 'orders',
                'label': 'Commandes',
                'icon': 'bi-cart',
                'model': 'commerce.Order',
                'lookup': 'customer',
                'lookup_value': customer.pk,
                'list_fields': ['__str__'],
                'search_fields': ['reference'],
                'ordering': '-created_at',
                'can_create': True,
                'create_url': f"{reverse('ventes:order_new')}?customer={customer.pk}",
                'detail_url_name': 'ventes:order_detail',
            },
            {
                'name': 'invoices',
                'label': 'Factures',
                'icon': 'bi-receipt',
                'model': 'commerce.Invoice',
                'lookup': 'customer',
                'lookup_value': customer.pk,
                'list_fields': ['__str__'],
                'search_fields': ['reference'],
                'ordering': '-created_at',
                'detail_url_name': 'ventes:invoice_detail',
            },
        ]
        
        return relations
    
    def get_tools_config(self):
        """Outils disponibles pour le client"""
        customer = self.object
        
        tools = [
            {
                'name': 'export_pdf',
                'label': 'Exporter fiche PDF',
                'icon': 'bi-file-pdf',
                'url': '#',
            },
            {
                'name': 'new_quote',
                'label': 'Créer un devis',
                'icon': 'bi-file-plus',
                'url': f"{reverse('ventes:devis_new')}?customer={customer.pk}",
            },
            {
                'name': 'new_order',
                'label': 'Créer une commande',
                'icon': 'bi-cart-plus',
                'url': f"{reverse('ventes:order_new')}?customer={customer.pk}",
            },
        ]
        
        if customer.is_active:
            tools.append({
                'name': 'archive',
                'label': 'Archiver',
                'icon': 'bi-archive',
                'url': '#',
            })
        else:
            tools.append({
                'name': 'reactivate',
                'label': 'Réactiver',
                'icon': 'bi-arrow-counterclockwise',
                'url': '#',
            })
        
        return tools


# Alias pour compatibilité
customer_meta_detail = CustomerMetaDetailView.as_view()
