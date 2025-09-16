"""
Vues UI pour l'application DRM
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET"])
def export_list(request):
    """Page de liste des exports DRM"""
    # Récupérer le domaine de l'utilisateur
    domaine = None
    try:
        domaine = request.user.profile.domaine
    except:
        # Fallback pour les tests - prendre le premier domaine
        from monchai.apps.accounts.models import Domaine
        domaine = Domaine.objects.first()
    
    context = {
        'domaine': domaine,
        'page_title': 'Exports DRM',
        'breadcrumbs': [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Exports DRM', 'url': None}
        ]
    }
    
    return render(request, 'drm/export_list.html', context)
