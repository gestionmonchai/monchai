"""
Context processors pour les suggestions intelligentes.
Injecte automatiquement les notifications dans tous les templates.
"""

from django.conf import settings


def smart_notifications(request):
    """
    Injecte les notifications intelligentes dans le contexte.
    - drm_status: Statut DRM pour le header
    - header_nudges: Nudges à afficher dans le header
    """
    context = {
        'drm_status': None,
        'header_nudges': [],
        'smart_features_enabled': getattr(settings, 'SMART_FEATURES_ENABLED', True),
    }
    
    # Ne pas exécuter pour les requêtes non authentifiées ou API
    if not request.user.is_authenticated:
        return context
    
    # Ne pas exécuter pour les requêtes AJAX/HTMX partielles
    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return context
    
    # Ne pas exécuter sur les pages admin ou API
    path = request.path
    if path.startswith('/admin/') or path.startswith('/api/'):
        return context
    
    try:
        from apps.ai.smart_suggestions import DRMTimer, SmartSuggestions
        
        # Récupérer l'organisation courante
        organization = getattr(request, 'current_org', None)
        if not organization:
            return context
        
        # Statut DRM
        context['drm_status'] = DRMTimer.get_drm_status(organization)
        
        # Notifications header
        context['header_nudges'] = SmartSuggestions.get_header_notifications(organization)
        
    except Exception as e:
        # Silencieux en cas d'erreur pour ne pas casser le site
        import logging
        logging.getLogger(__name__).debug(f"Smart notifications error: {e}")
    
    return context
