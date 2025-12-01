"""
Vues pour le catalogue en grille - Roadmap 25
Interface utilisateur avec recherche, facettes, tri et pagination keyset
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from apps.accounts.decorators import require_membership
from apps.viticulture.models import Cuvee, Appellation, Vintage


@login_required
@require_membership()
def catalogue_grid(request):
    """
    Page principale du catalogue en grille
    /catalogue avec recherche, facettes, tri et pagination
    """
    organization = request.current_org
    
    # Paramètres de requête
    search_query = request.GET.get('q', '').strip()
    appellation_filter = request.GET.get('appellation', '')
    vintage_filter = request.GET.get('vintage', '')
    color_filter = request.GET.get('color', '')
    sort_param = request.GET.get('sort', 'name_asc')
    page = request.GET.get('page', 1)
    
    # Requête de base
    cuvees = Cuvee.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('appellation', 'vintage', 'default_uom')
    
    # Recherche textuelle
    if search_query:
        cuvees = cuvees.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(appellation__name__icontains=search_query)
        )
    
    # Filtres par facettes
    if appellation_filter:
        cuvees = cuvees.filter(appellation__id=appellation_filter)
    
    if vintage_filter:
        cuvees = cuvees.filter(vintage__id=vintage_filter)
    
    if color_filter:
        cuvees = cuvees.filter(appellation__type=color_filter)
    
    # Tri
    if sort_param == 'name_asc':
        cuvees = cuvees.order_by('name')
    elif sort_param == 'name_desc':
        cuvees = cuvees.order_by('-name')
    elif sort_param == 'updated_desc':
        cuvees = cuvees.order_by('-updated_at')
    else:
        cuvees = cuvees.order_by('name')  # Défaut
    
    # Pagination
    paginator = Paginator(cuvees, 24)  # 24 éléments par page comme spécifié
    page_obj = paginator.get_page(page)
    
    # Facettes pour les filtres
    all_cuvees = Cuvee.objects.filter(organization=organization, is_active=True)
    if search_query:
        all_cuvees = all_cuvees.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(appellation__name__icontains=search_query)
        )
    
    # Appellations avec compteurs
    appellations_facets = (
        all_cuvees.values('appellation__id', 'appellation__name')
        .annotate(count=Count('id'))
        .filter(appellation__id__isnull=False)
        .order_by('appellation__name')
    )
    
    # Millésimes avec compteurs
    vintages_facets = (
        all_cuvees.values('vintage__id', 'vintage__year')
        .annotate(count=Count('id'))
        .filter(vintage__id__isnull=False)
        .order_by('-vintage__year')
    )
    
    # Couleurs avec compteurs
    colors_facets = (
        all_cuvees.values('appellation__type')
        .annotate(count=Count('id'))
        .filter(appellation__type__isnull=False)
        .order_by('appellation__type')
    )
    
    context = {
        'page_obj': page_obj,
        'cuvees': page_obj.object_list,
        'search_query': search_query,
        'appellation_filter': appellation_filter,
        'vintage_filter': vintage_filter,
        'color_filter': color_filter,
        'sort_param': sort_param,
        'appellations_facets': appellations_facets,
        'vintages_facets': vintages_facets,
        'colors_facets': colors_facets,
        'total_count': paginator.count,
    }
    
    return render(request, 'catalogue/catalogue_grid.html', context)


@login_required
@require_membership()
def catalogue_search_ajax(request):
    """
    Recherche AJAX pour le catalogue
    Utilisé pour l'autocomplétion et les suggestions
    """
    query = request.GET.get('q', '').strip()
    organization = request.current_org
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    # Recherche dans les cuvées
    cuvees = Cuvee.objects.filter(
        organization=organization,
        is_active=True
    ).filter(
        Q(name__icontains=query) |
        Q(code__icontains=query) |
        Q(appellation__name__icontains=query)
    ).select_related('appellation', 'vintage')[:10]
    
    results = []
    for cuvee in cuvees:
        results.append({
            'id': str(cuvee.id),
            'name': cuvee.name,
            'code': cuvee.code or '',
            'appellation': cuvee.appellation.name if cuvee.appellation else '',
            'vintage': cuvee.vintage.year if cuvee.vintage else None,
            'url': f'/catalogue/{cuvee.id}/'
        })
    
    return JsonResponse({'results': results})
