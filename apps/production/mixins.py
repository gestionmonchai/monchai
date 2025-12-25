"""
=====================================================================
MIXIN PRODUCTION LAYOUT - STANDARDISATION VUES /production/*
=====================================================================
Fournit le contexte standard pour toutes les vues production :
- Sidebar active section
- Actions topbar
- Timelapse events
- Breadcrumbs
=====================================================================
"""

from django.views.generic.base import ContextMixin
from apps.production.services.timelapse import get_timelapse_for_context


class ProductionLayoutMixin(ContextMixin):
    """
    Mixin pour standardiser le layout des vues Production.
    
    Ajoute automatiquement au contexte :
    - production_sidebar_active_section
    - actions_topbar (liste des actions de création)
    - actions_quick (actions rapides contextuelles)
    - timelapse_events
    - timelapse_scope_label
    - show_timelapse (bool)
    
    Usage:
        class MyView(ProductionLayoutMixin, TemplateView):
            production_sidebar_section = 'lots'
            timelapse_context_type = 'lot'
            
            def get_timelapse_context_id(self):
                return self.object.pk
    """
    
    # Configuration par défaut (à surcharger)
    production_sidebar_section = 'home'  # home, parcelles, vendanges, lots, contenants, analyses, etc.
    timelapse_context_type = 'production_home'  # production_home, parcelle, lot, cuve, vendange
    timelapse_scope_label = 'Production'
    show_timelapse = True
    show_actions_topbar = True
    
    # Actions par défaut
    default_actions_create = [
        {'label': 'Opération', 'url': '/production/operations/nouvelle/', 'icon': 'gear'},
        {'label': 'Analyse', 'url': '/production/lots-elevage/analyses/nouvelle/', 'icon': 'clipboard-pulse'},
        {'label': 'Lot technique', 'url': '/production/lots-techniques/nouveau/', 'icon': 'box-seam'},
        {'label': 'Vendange', 'url': '/production/vendanges/nouveau/', 'icon': 'basket'},
        {'label': 'Contenant', 'url': '/production/contenants/nouveau/', 'icon': 'archive'},
    ]
    
    def get_timelapse_context_id(self):
        """Retourne l'ID du contexte pour la timelapse. À surcharger."""
        if hasattr(self, 'object') and self.object:
            return self.object.pk
        return None
    
    def get_production_sidebar_section(self):
        """Retourne la section active du sidebar. À surcharger si besoin."""
        return self.production_sidebar_section
    
    def get_timelapse_context_type(self):
        """Retourne le type de contexte timelapse. À surcharger si besoin."""
        return self.timelapse_context_type
    
    def get_timelapse_scope_label(self):
        """Retourne le label du scope timelapse. À surcharger si besoin."""
        return self.timelapse_scope_label
    
    def get_actions_create(self):
        """Retourne la liste des actions de création. À surcharger."""
        return self.default_actions_create
    
    def get_actions_quick(self):
        """Retourne les actions rapides contextuelles. À surcharger."""
        return []
    
    def get_timelapse_events(self):
        """Récupère les événements timelapse pour le contexte actuel."""
        if not self.show_timelapse:
            return []
        
        try:
            organization = getattr(self.request, 'current_org', None)
            if not organization:
                return []
            
            context_type = self.get_timelapse_context_type()
            context_id = self.get_timelapse_context_id()
            
            return get_timelapse_for_context(
                organization=organization,
                context_type=context_type,
                context_id=context_id,
                limit=30
            )
        except Exception:
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Sidebar
        context['production_sidebar_active_section'] = self.get_production_sidebar_section()
        
        # Actions topbar
        if self.show_actions_topbar:
            context['actions_create'] = self.get_actions_create()
            context['actions_quick'] = self.get_actions_quick()
            context['show_alert_btn'] = True
        
        # Timelapse
        if self.show_timelapse:
            context['timelapse_events'] = self.get_timelapse_events()
            context['timelapse_scope_label'] = self.get_timelapse_scope_label()
            context['show_timelapse'] = True
        else:
            context['show_timelapse'] = False
        
        return context


class ProductionDetailMixin(ProductionLayoutMixin):
    """
    Mixin spécialisé pour les vues de détail Production.
    Configure automatiquement l'objet principal et l'URL d'édition.
    """
    
    def get_primary_object_edit_url(self):
        """Retourne l'URL d'édition de l'objet. À surcharger."""
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Objet principal pour le topbar
        if hasattr(self, 'object') and self.object:
            context['primary_object'] = self.object
            context['primary_object_edit_url'] = self.get_primary_object_edit_url()
        
        return context


class ProductionListMixin(ProductionLayoutMixin):
    """
    Mixin spécialisé pour les vues de liste Production.
    Désactive la timelapse par défaut pour les listes.
    """
    
    show_timelapse = False  # Pas de timelapse sur les listes par défaut
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Les listes affichent la timelapse globale si activée
        if self.show_timelapse:
            context['timelapse_scope_label'] = 'Récent'
        return context


class ProductionFormMixin(ProductionLayoutMixin):
    """
    Mixin spécialisé pour les formulaires Production.
    Désactive les éléments non pertinents pour les formulaires.
    """
    
    show_timelapse = False
    show_actions_topbar = False


# Helpers pour les actions contextuelles
def get_parcelle_actions(parcelle):
    """Actions rapides pour une parcelle."""
    return [
        {'label': 'Intervention', 'url': f'/production/journal-cultural/?parcelle={parcelle.pk}', 'icon': 'journal-text'},
        {'label': 'Vendange', 'url': f'/production/vendanges/nouveau/?parcelle={parcelle.pk}', 'icon': 'basket'},
    ]


def get_lot_actions(lot):
    """Actions rapides pour un lot technique."""
    return [
        {'label': 'Opération', 'url': f'/production/operations/nouvelle/?lot={lot.pk}', 'icon': 'gear'},
        {'label': 'Analyse', 'url': f'/production/lots-elevage/analyses/nouvelle/?lot={lot.pk}', 'icon': 'clipboard-pulse'},
        {'label': 'Soutirage', 'url': f'/production/lots-techniques/{lot.pk}/soutirage/', 'icon': 'arrow-down-up'},
    ]


def get_contenant_actions(contenant):
    """Actions rapides pour un contenant (cuve/barrique)."""
    return [
        {'label': 'Affecter lot', 'url': f'/production/contenants/{contenant.pk}/actions/affecter-lot/', 'icon': 'box-arrow-in-down'},
        {'label': 'Vidange', 'url': f'/production/contenants/{contenant.pk}/actions/vidange/', 'icon': 'box-arrow-up'},
        {'label': 'Nettoyage', 'url': f'/production/contenants/{contenant.pk}/actions/nettoyage/', 'icon': 'droplet'},
    ]
