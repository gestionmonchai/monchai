"""
Vues pour les référentiels viticoles
Roadmap Cut #3 : Référentiels (starter pack)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import hashlib
import mimetypes
from .models import ImportBatch, ImportExecution
import json
from decimal import Decimal

from apps.accounts.decorators import require_membership, require_perm
from apps.accounts.models import Organization
from .models import Cepage, CepageReference, Parcelle, ParcelleEncepagement, Unite, Cuvee, Entrepot
from apps.viticulture.models import GrapeVariety, Appellation, Vintage, UnitOfMeasure, VineyardPlot, Warehouse
from .forms import (
    CepageForm, ParcelleForm, UniteForm, CuveeForm, EntrepotForm
)
from .csv_import import CSVImportService, CSVImportError
from .export_service import CSVExportService


def _is_ajax(request):
    """Souple: accepte X-Requested-With, Accept: application/json ou ?format=json."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in (request.headers.get('Accept') or '')
        or request.GET.get('format') == 'json'
    )


def _compute_metrics_from_geojson(geojson):
    """Compute bbox, centroid, and approximate area/perimeter in meters for a lon/lat GeoJSON Feature.
    Returns dict with keys: area_m2, perimeter_m, minx,miny,maxx,maxy, centroid_x, centroid_y.
    Uses pyproj to project to EPSG:3857 if available; otherwise rough degree→meter conversion.
    """
    try:
        from shapely.geometry import shape
        from shapely.ops import transform
    except Exception:
        return {}

    try:
        geom = shape((geojson or {}).get('geometry') or {})
        if geom.is_empty:
            return {}
    except Exception:
        return {}

    minx, miny, maxx, maxy = geom.bounds
    c = geom.centroid

    # Try accurate meters via WebMercator
    area_m2 = 0.0
    perimeter_m = 0.0
    try:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        g_m = transform(lambda x, y, z=None: transformer.transform(x, y), geom)
        area_m2 = float(getattr(g_m, 'area', 0.0))
        perimeter_m = float(getattr(g_m, 'length', 0.0))
    except Exception:
        # Fallback: approximate meters per degree
        try:
            area_m2 = float(abs(getattr(geom, 'area', 0.0))) * 123640000.0  # rough WGS84 scale
        except Exception:
            area_m2 = 0.0
        try:
            perimeter_m = float(getattr(geom, 'length', 0.0)) * 111320.0
        except Exception:
            perimeter_m = 0.0

    return {
        'area_m2': area_m2,
        'perimeter_m': perimeter_m,
        'minx': float(minx), 'miny': float(miny), 'maxx': float(maxx), 'maxy': float(maxy),
        'centroid_x': float(getattr(c, 'x', 0.0)), 'centroid_y': float(getattr(c, 'y', 0.0)),
    }

@require_perm('parcelles', 'view')
def parcelles_map(request):
    """Visualisation carte des parcelles avec fond satellite + édition tags/coordonnées."""
    organization = request.current_org
    qs = Parcelle.objects.filter(organization=organization).only(
        'id', 'nom', 'surface', 'commune', 'appellation', 'latitude', 'longitude', 'tags', 'geojson'
    ).order_by('nom')
    items = []
    for p in qs[:1000]:
        try:
            raw = getattr(p, 'tags', []) or []
            if isinstance(raw, str):
                tags = [t.strip() for t in raw.split(',') if t.strip()]
            else:
                try:
                    tags = list(raw)
                except Exception:
                    tags = []
            item = {
                'id': p.pk,
                'nom': p.nom,
                'surface': float(p.surface) if p.surface is not None else None,
                'commune': p.commune or '',
                'appellation': p.appellation or '',
                'lat': float(p.latitude) if p.latitude is not None else None,
                'lng': float(p.longitude) if p.longitude is not None else None,
                'tags': tags,
                'geojson': getattr(p, 'geojson', None) or None,
            }
        except Exception:
            item = {
                'id': p.pk,
                'nom': p.nom,
                'surface': None,
                'commune': p.commune or '',
                'appellation': p.appellation or '',
                'lat': None,
                'lng': None,
                'tags': [],
                'geojson': None,
            }
        items.append(item)
    ctx = {
        'page_title': 'Carte des parcelles',
        'breadcrumb_items': [
            {'name': 'Référentiels', 'url': '/ref/'},
            {'name': 'Parcelles', 'url': '/ref/parcelles/'},
            {'name': 'Carte', 'url': None},
        ],
        'parcelles_json': json.dumps(items),
    }
    return render(request, 'referentiels/parcelles_map.html', ctx)


@require_perm('parcelles', 'edit')
@csrf_exempt
@require_http_methods(["POST"])
def parcelles_update_geo(request):
    """API: met à jour lat/lon/tags d'une parcelle.
    Accepte JSON: {id, lat, lng, tags}
    """
    try:
        payload = request.POST
        if request.content_type and 'application/json' in request.content_type.lower():
            payload = json.loads(request.body.decode('utf-8'))
        pid = payload.get('id')
        lat = payload.get('lat')
        lng = payload.get('lng')
        tags = payload.get('tags')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Payload invalide'}, status=400)

    if not pid:
        return JsonResponse({'ok': False, 'error': 'id requis'}, status=400)

    parcelle = get_object_or_404(Parcelle, pk=pid, organization=request.current_org)

    updates = []
    from decimal import Decimal
    if lat is not None and lat != '':
        try:
            parcelle.latitude = Decimal(str(lat))
            updates.append('latitude')
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Latitude invalide'}, status=400)
    if lng is not None and lng != '':
        try:
            parcelle.longitude = Decimal(str(lng))
            updates.append('longitude')
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Longitude invalide'}, status=400)
    if tags is not None:
        try:
            if isinstance(tags, str):
                # support "a,b,c"
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            if not isinstance(tags, list):
                return JsonResponse({'ok': False, 'error': 'tags doit être une liste'}, status=400)
            parcelle.tags = tags
            updates.append('tags')
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Tags invalides'}, status=400)

    if not updates:
        return JsonResponse({'ok': True, 'updated': []})
    parcelle.save(update_fields=list(set(updates)))
    return JsonResponse({'ok': True, 'updated': updates})

# ===== CÉPAGES =====

@require_membership(role_min='read_only')
def cepage_list(request):
    """Liste des cépages avec filtres avancés et référentiel officiel"""
    organization = request.current_org
    
    # Onglet actif : 'mes_cepages' ou 'reference'
    tab = request.GET.get('tab', 'mes_cepages')
    
    # Détecter la région de l'organisation (depuis la config ou les parcelles)
    region_org = organization.region_viticole if hasattr(organization, 'region_viticole') else ''
    
    # Si pas de région définie, essayer de la déduire des parcelles avec appellation
    if not region_org:
        # Chercher dans les appellations des parcelles
        from apps.referentiels.models import Parcelle
        appellations = Parcelle.objects.filter(
            organization=organization, 
            appellation__isnull=False
        ).exclude(appellation='').values_list('appellation', flat=True).distinct()[:5]
        
        # Détecter la région à partir des appellations
        appellation_text = ' '.join(appellations).lower()
        if 'bordeaux' in appellation_text or 'medoc' in appellation_text or 'saint-emilion' in appellation_text:
            region_org = 'bordeaux'
        elif 'bourgogne' in appellation_text or 'chablis' in appellation_text:
            region_org = 'bourgogne'
        elif 'alsace' in appellation_text:
            region_org = 'alsace'
        elif 'champagne' in appellation_text:
            region_org = 'champagne'
        elif 'loire' in appellation_text or 'anjou' in appellation_text or 'touraine' in appellation_text:
            region_org = 'loire'
        elif 'rhone' in appellation_text or 'cotes-du-rhone' in appellation_text:
            region_org = 'rhone'
        elif 'provence' in appellation_text:
            region_org = 'provence'
        elif 'languedoc' in appellation_text or 'roussillon' in appellation_text:
            region_org = 'languedoc'
    
    # Filtres communs
    filters = {}
    search = request.GET.get('search', '').strip()
    couleur = request.GET.get('couleur', '').strip()
    region_filter = request.GET.get('region', '').strip()
    
    if tab == 'reference':
        # Afficher les cépages de référence
        cepages_ref = CepageReference.objects.all()
        
        # Préfiltre par région si définie
        if region_filter:
            cepages_ref = cepages_ref.filter(regions__contains=region_filter)
            filters['region'] = region_filter
        elif region_org:
            # Préfiltre par région de l'organisation par défaut
            cepages_ref = cepages_ref.filter(regions__contains=region_org)
            filters['region'] = region_org
        
        if search:
            cepages_ref = cepages_ref.filter(
                Q(nom__icontains=search) | Q(synonymes__icontains=search)
            )
            filters['search'] = search
        
        if couleur and couleur in ['rouge', 'blanc', 'rose', 'gris']:
            cepages_ref = cepages_ref.filter(couleur=couleur)
            filters['couleur'] = couleur
        
        cepages_ref = cepages_ref.order_by('nom')
        
        # Cépages déjà importés dans l'organisation (liste pour le template)
        cepages_org_noms = list(Cepage.objects.filter(
            organization=organization
        ).values_list('name_norm', flat=True))
        
        # Pagination
        paginator = Paginator(cepages_ref, 30)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'tab': 'reference',
            'page_obj': page_obj,
            'cepages_ref': page_obj,
            'cepages_org_noms': cepages_org_noms,
            'filters': filters,
            'organization': organization,
            'region_org': region_org,
            'regions_choices': Organization.REGION_VITICOLE_CHOICES[1:],  # Sans le vide
            'page_title': 'Référentiel des Cépages',
            'search': search,
            'total_reference': CepageReference.objects.count(),
        }
    else:
        # Afficher les cépages de l'organisation
        cepages = Cepage.objects.filter(organization=organization, is_active=True)
        
        if search:
            cepages = cepages.filter(
                Q(nom__icontains=search) |
                Q(code__icontains=search) |
                Q(notes__icontains=search)
            )
            filters['search'] = search
        
        if couleur and couleur in ['rouge', 'blanc', 'rose']:
            cepages = cepages.filter(couleur=couleur)
            filters['couleur'] = couleur
        
        # Tri
        sort_by = request.GET.get('sort', 'nom')
        sort_order = request.GET.get('order', 'asc')
        valid_sorts = ['nom', 'code', 'couleur', 'created_at', 'updated_at']
        if sort_by in valid_sorts:
            order_field = f'-{sort_by}' if sort_order == 'desc' else sort_by
            cepages = cepages.order_by(order_field)
        else:
            cepages = cepages.order_by('nom')
            sort_by = 'nom'
            sort_order = 'asc'
        
        # Pagination
        paginator = Paginator(cepages, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Statistiques
        all_cepages = Cepage.objects.filter(organization=organization, is_active=True)
        stats = {
            'total': all_cepages.count(),
            'filtered': cepages.count(),
            'couleurs': [
                {'value': 'rouge', 'label': 'Rouge', 'count': all_cepages.filter(couleur='rouge').count()},
                {'value': 'blanc', 'label': 'Blanc', 'count': all_cepages.filter(couleur='blanc').count()},
                {'value': 'rose', 'label': 'Rosé', 'count': all_cepages.filter(couleur='rose').count()},
            ]
        }
        
        # Si aucun cépage, préparer l'onboarding avec les cépages de référence
        cepages_ref_json = []
        if stats['total'] == 0 and not search:
            # Charger tous les cépages de référence pour l'onboarding
            cepages_ref = CepageReference.objects.all().order_by('nom')
            cepages_ref_json = [
                {
                    'id': c.id,
                    'nom': c.nom,
                    'couleur': c.couleur,
                    'regions': c.regions or [],
                }
                for c in cepages_ref
            ]
        
        context = {
            'tab': 'mes_cepages',
            'page_obj': page_obj,
            'filters': filters,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'stats': stats,
            'organization': organization,
            'region_org': region_org,
            'regions_choices': Organization.REGION_VITICOLE_CHOICES[1:],
            'page_title': 'Mes Cépages',
            'search': search,
            'total_reference': CepageReference.objects.count(),
            'cepages_ref_json': json.dumps(cepages_ref_json),
        }
    
    return render(request, 'referentiels/cepage_list.html', context)


@require_membership(role_min='admin')
def cepage_import_from_reference(request):
    """Importe un ou plusieurs cépages du référentiel vers l'organisation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    organization = request.current_org
    
    # IDs des cépages de référence à importer
    try:
        data = json.loads(request.body)
        ref_ids = data.get('ids', [])
    except:
        ref_ids = request.POST.getlist('ids')
    
    if not ref_ids:
        return JsonResponse({'error': 'Aucun cépage sélectionné'}, status=400)
    
    imported = 0
    skipped = 0
    errors = []
    
    for ref_id in ref_ids:
        try:
            ref = CepageReference.objects.get(id=int(ref_id))
            
            # Vérifier si déjà existant
            if Cepage.objects.filter(organization=organization, name_norm=ref.name_norm).exists():
                skipped += 1
                continue
            
            # Créer le cépage
            Cepage.objects.create(
                organization=organization,
                nom=ref.nom,
                couleur=ref.couleur if ref.couleur != 'gris' else 'blanc',
                reference=ref,
                is_active=True,
            )
            imported += 1
            
        except CepageReference.DoesNotExist:
            errors.append(f"Cépage #{ref_id} non trouvé")
        except Exception as e:
            errors.append(str(e))
    
    return JsonResponse({
        'success': True,
        'imported': imported,
        'skipped': skipped,
        'errors': errors,
    })


@require_membership(role_min='read_only')
def cepage_search_ajax(request):
    """API AJAX pour recherche en temps réel des cépages avec filtres avancés"""
    if not _is_ajax(request):
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    
    organization = request.current_org
    page = request.GET.get('page', 1)
    
    # Appliquer les mêmes filtres que la vue principale
    cepages = Cepage.objects.filter(organization=organization, is_active=True)
    
    # Filtres par champs individuels
    filters = {}
    
    # Filtre par nom
    nom = request.GET.get('nom', '').strip()
    if nom:
        cepages = cepages.filter(nom__icontains=nom)
        filters['nom'] = nom
    
    # Filtre par code
    code = request.GET.get('code', '').strip()
    if code:
        cepages = cepages.filter(code__icontains=code)
        filters['code'] = code
    
    # Filtre par couleur
    couleur = request.GET.get('couleur', '').strip()
    if couleur and couleur in ['rouge', 'blanc', 'rose']:
        cepages = cepages.filter(couleur=couleur)
        filters['couleur'] = couleur
    
    # Filtre par notes
    notes = request.GET.get('notes', '').strip()
    if notes:
        cepages = cepages.filter(notes__icontains=notes)
        filters['notes'] = notes
    
    # Recherche globale (pour compatibilité)
    search = request.GET.get('search', '').strip()
    if search:
        cepages = cepages.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search) |
            Q(notes__icontains=search)
        )
        filters['search'] = search
    
    # Tri
    sort_by = request.GET.get('sort', 'nom')
    sort_order = request.GET.get('order', 'asc')
    
    valid_sorts = ['nom', 'code', 'couleur', 'created_at', 'updated_at']
    if sort_by in valid_sorts:
        order_field = sort_by
        if sort_order == 'desc':
            order_field = f'-{order_field}'
        cepages = cepages.order_by(order_field)
    else:
        cepages = cepages.order_by('nom')
    
    # Pagination
    paginator = Paginator(cepages, 20)
    page_obj = paginator.get_page(page)
    
    # Rendu du template partiel
    html = render_to_string('referentiels/partials/cepage_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    
    # Construire les paramètres pour la pagination
    pagination_params = {}
    pagination_params.update(filters)
    if sort_by != 'nom':
        pagination_params['sort'] = sort_by
    if sort_order != 'asc':
        pagination_params['order'] = sort_order
    
    # Rendu de la pagination
    pagination_html = render_to_string('referentiels/partials/pagination.html', {
        'page_obj': page_obj,
        'params': pagination_params,
        'base_url': 'referentiels:cepage_list'
    })
    
    return JsonResponse({
        'html': html,
        'pagination': pagination_html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
        'filters': filters
    })

    
    # Recherche simple
    search = request.GET.get('search', '').strip()
    if search:
        unites = unites.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(unites, 20)
    page_obj = paginator.get_page(page)
    
    # Rendu du template partiel
    html = render_to_string('referentiels/partials/unite_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    
    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
    })


@require_membership(role_min='read_only')
def parcelle_search_ajax(request):
    """API AJAX pour recherche en temps réel des parcelles"""
    if not _is_ajax(request):
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    organization = request.current_org
    page = request.GET.get('page', 1)
    parcelles = Parcelle.objects.filter(organization=organization)
    search = request.GET.get('search', '').strip()
    if search:
        parcelles = parcelles.filter(nom__icontains=search)
    paginator = Paginator(parcelles, 20)
    page_obj = paginator.get_page(page)
    html = render_to_string('referentiels/partials/parcelle_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    # Lightweight items for selects/autocomplete (id, nom)
    try:
        items = [{'id': str(p.pk), 'nom': p.nom} for p in page_obj.object_list]
    except Exception:
        items = []
    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
        'items': items,
    })


@require_membership(role_min='read_only')
def unite_search_ajax(request):
    """API AJAX pour recherche en temps réel des unités"""
    if not _is_ajax(request):
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    organization = request.current_org
    page = request.GET.get('page', 1)
    unites = Unite.objects.filter(organization=organization)
    search = request.GET.get('search', '').strip()
    if search:
        unites = unites.filter(nom__icontains=search)
    paginator = Paginator(unites, 20)
    page_obj = paginator.get_page(page)
    html = render_to_string('referentiels/partials/unite_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
    })


@require_membership(role_min='read_only')
def cuvee_search_ajax(request):
    """API AJAX pour recherche en temps réel des cuvées"""
    if not _is_ajax(request):
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    
    organization = request.current_org
    page = request.GET.get('page', 1)
    
    cuvees = Cuvee.objects.filter(organization=organization)
    
    # Recherche simple
    search = request.GET.get('search', '').strip()
    if search:
        cuvees = cuvees.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(cuvees, 20)
    page_obj = paginator.get_page(page)
    
    # Rendu du template partiel
    html = render_to_string('referentiels/partials/cuvee_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    
    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
    })


@require_membership(role_min='read_only')
def entrepot_search_ajax(request):
    """API AJAX pour recherche en temps réel des entrepôts"""
    if not _is_ajax(request):
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    
    organization = request.current_org
    page = request.GET.get('page', 1)
    
    entrepots = Entrepot.objects.filter(organization=organization)
    
    # Recherche simple
    search = request.GET.get('search', '').strip()
    if search:
        entrepots = entrepots.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(entrepots, 20)
    page_obj = paginator.get_page(page)
    
    # Rendu du template partiel
    html = render_to_string('referentiels/partials/entrepot_table_rows.html', {
        'page_obj': page_obj,
        'request': request,
    })
    
    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_results': len(page_obj.object_list) > 0,
    })


@require_membership(role_min='read_only')
def cepage_detail(request, pk):
    """Détail d'un cépage"""
    organization = request.current_org
    cepage = get_object_or_404(Cepage, pk=pk, organization=organization)
    
    context = {
        'cepage': cepage,
        'organization': organization,
        'page_title': f'Cépage : {cepage.nom}'
    }
    
    return render(request, 'referentiels/cepage_detail.html', context)


@require_membership(role_min='editor')
@require_http_methods(["GET", "POST"])
def cepage_create(request):
    """Création d'un cépage"""
    organization = request.current_org
    
    if request.method == 'POST':
        form = CepageForm(request.POST, organization=organization)
        if form.is_valid():
            cepage = form.save(commit=False)
            cepage.organization = organization
            cepage.save()
            
            messages.success(request, f'Le cépage "{cepage.nom}" a été créé avec succès.')
            return redirect('referentiels:cepage_detail', pk=cepage.pk)
    else:
        form = CepageForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouveau cépage'
    }
    
    return render(request, 'referentiels/cepage_form.html', context)


@require_membership(role_min='editor')
@require_http_methods(["GET", "POST"])
def cepage_update(request, pk):
    """Modification d'un cépage"""
    organization = request.current_org
    cepage = get_object_or_404(Cepage, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = CepageForm(request.POST, instance=cepage, organization=organization)
        if form.is_valid():
            cepage = form.save()
            
            messages.success(request, f'Le cépage "{cepage.nom}" a été modifié avec succès.')
            return redirect('referentiels:cepage_detail', pk=cepage.pk)
    else:
        form = CepageForm(instance=cepage, organization=organization)
    
    context = {
        'form': form,
        'cepage': cepage,
        'organization': organization,
        'page_title': f'Modifier : {cepage.nom}'
    }
    
    return render(request, 'referentiels/cepage_form.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST", "DELETE"])
def cepage_delete(request, pk):
    """Suppression d'un cépage"""
    organization = request.current_org
    cepage = get_object_or_404(Cepage, pk=pk, organization=organization)
    
    nom = cepage.nom
    cepage.delete()
    
    # Réponse AJAX ou redirect standard
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Le cépage "{nom}" a été supprimé.'})
    
    messages.success(request, f'Le cépage "{nom}" a été supprimé avec succès.')
    return redirect('referentiels:cepage_list')


# ===== PARCELLES =====

@require_perm('parcelles', 'view')
def parcelle_list(request):
    """Liste des parcelles - Roadmap item 15"""
    organization = request.current_org
    from django.db.models import Sum
    parcelles = Parcelle.objects.filter(organization=organization).annotate(harvested_kg=Sum('vendanges__poids_kg'))
    
    # Recherche simple
    search = request.GET.get('search', '')
    if search:
        parcelles = parcelles.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(parcelles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'organization': organization,
        'page_title': 'Parcelles'
    }
    
    return render(request, 'referentiels/parcelle_list.html', context)


@require_perm('parcelles', 'view')
def parcelle_detail(request, pk):
    """Détail d'une parcelle avec données métier viticoles"""
    from datetime import date
    from django.db.models import Sum, Avg, Max, Count
    from decimal import Decimal
    
    organization = request.current_org
    parcelle = get_object_or_404(
        Parcelle.objects.prefetch_related('cepages', 'encepagements__cepage'),
        pk=pk, 
        organization=organization
    )
    
    # Encépagements détaillés
    encepagements = parcelle.encepagements.select_related('cepage').all()
    encepagement_total_pct = sum(e.pourcentage for e in encepagements) if encepagements else Decimal('0')
    
    # Vendanges de cette parcelle
    vendanges = []
    derniere_vendange = None
    total_recolte_kg = Decimal('0')
    rendement_moyen = None
    try:
        from apps.production.models import VendangeReception
        vendanges_qs = VendangeReception.objects.filter(
            organization=organization, 
            parcelle=parcelle
        ).order_by('-date')[:5]
        vendanges = list(vendanges_qs)
        
        if vendanges:
            derniere_vendange = vendanges[0]
        
        # Stats agrégées sur toutes les vendanges
        agg = VendangeReception.objects.filter(
            organization=organization,
            parcelle=parcelle
        ).aggregate(
            total_kg=Sum('poids_kg'),
            nb_vendanges=Count('id')
        )
        total_recolte_kg = agg['total_kg'] or Decimal('0')
        nb_vendanges = agg['nb_vendanges'] or 0
        
        # Rendement moyen (kg/ha)
        if nb_vendanges > 0 and parcelle.surface > 0:
            rendement_moyen = (total_recolte_kg / nb_vendanges / parcelle.surface).quantize(Decimal('1'))
    except Exception:
        pass
    
    # Journal complet des opérations (combinaison des deux sources)
    operations = []
    timeline = []
    try:
        from apps.viticulture.models_parcelle_journal import ParcelleJournalEntry
        from apps.viticulture.models_ops import ParcelleOperation
        
        # Source 1: ParcelleJournalEntry
        journal_entries = ParcelleJournalEntry.objects.filter(
            organization=organization,
            parcelle=parcelle
        ).select_related('op_type').order_by('-date')[:50]
        
        for entry in journal_entries:
            operations.append({
                'id': str(entry.id),
                'date': entry.date,
                'created_at': entry.created_at,
                'type': entry.op_type.code,
                'type_label': entry.op_type.label,
                'resume': entry.resume,
                'notes': entry.notes,
                'cout': entry.cout_total_eur,
                'source': 'journal',
            })
            # Timeline - icônes par type d'opération
            icon_map = {
                'taille': ('bi-scissors', 'success'),
                'traitement': ('bi-droplet-fill', 'danger'),
                'palissage': ('bi-diagram-3', 'info'),
                'rognage': ('bi-scissors', 'success'),
                'effeuillage': ('bi-leaf', 'success'),
                'travail_sol': ('bi-tools', 'secondary'),
                'fertilisation': ('bi-droplet-half', 'primary'),
                'irrigation': ('bi-moisture', 'info'),
                'observation': ('bi-eye', 'secondary'),
            }
            icon, color = icon_map.get(entry.op_type.code, ('bi-calendar-event', 'primary'))
            timeline.append({
                'date': entry.date,
                'created_at': entry.created_at,
                'icon': icon,
                'color': color,
                'title': entry.op_type.label,
                'description': entry.resume or (entry.notes[:100] if entry.notes else ''),
                'type': 'operation',
                'url': f'/viticulture/journal/{entry.id}/',
            })
        
        # Source 2: ParcelleOperation (anciennes opérations)
        existing_keys = set((o['date'], o['type']) for o in operations)
        
        ops = ParcelleOperation.objects.filter(
            organization=organization,
            parcelle=parcelle
        ).order_by('-date')[:50]
        
        for op in ops:
            key = (op.date, op.operation_type)
            if key not in existing_keys:
                operations.append({
                    'id': str(op.id),
                    'date': op.date,
                    'created_at': op.created_at,
                    'type': op.operation_type,
                    'type_label': op.get_operation_type_display(),
                    'resume': op.label,
                    'notes': op.notes,
                    'cout': op.cout_eur,
                    'source': 'ops',
                })
                # Timeline - icônes par type d'opération
                icon_map2 = {
                    'taille': ('bi-scissors', 'success'),
                    'traitement': ('bi-droplet-fill', 'danger'),
                    'palissage': ('bi-diagram-3', 'info'),
                    'rognage': ('bi-scissors', 'success'),
                    'effeuillage': ('bi-leaf', 'success'),
                    'travail_sol': ('bi-tools', 'secondary'),
                    'fertilisation': ('bi-droplet-half', 'primary'),
                    'irrigation': ('bi-moisture', 'info'),
                    'observation': ('bi-eye', 'secondary'),
                }
                icon2, color2 = icon_map2.get(op.operation_type, ('bi-calendar-event', 'primary'))
                timeline.append({
                    'date': op.date,
                    'created_at': op.created_at,
                    'icon': icon2,
                    'color': color2,
                    'title': op.get_operation_type_display(),
                    'description': op.label or (op.notes[:100] if op.notes else ''),
                    'type': 'operation',
                })
        
        # Trier par date décroissante
        operations.sort(key=lambda x: (x['date'], str(x['id'])), reverse=True)
        operations = operations[:15]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    # Ajouter les vendanges à la timeline
    for v in vendanges:
        poids = v.poids_total  # Use poids_total property (calculates from lines or uses poids_kg)
        timeline.append({
            'date': v.date,
            'created_at': getattr(v, 'created_at', v.date),
            'icon': 'bi-basket-fill',
            'color': 'warning',
            'title': f'Vendange {v.code or ""}',
            'description': f"{poids} kg • {v.get_type_recolte_display()}" if poids else v.get_type_recolte_display(),
            'type': 'vendange',
            'url': f'/production/vendanges/{v.pk}/',
        })
    
    # Trier la timeline par date décroissante
    timeline.sort(key=lambda x: (x['date'], str(x.get('created_at', ''))), reverse=True)
    timeline = timeline[:20]
    
    # Calculs métier
    surface_m2 = int(parcelle.surface * 10000) if parcelle.surface else 0
    estimation_bouteilles = int(parcelle.surface * 7500) if parcelle.surface >= Decimal('0.1') else 0
    surface_plantee = parcelle.get_surface_plantee() if encepagements else Decimal('0')
    
    # Âge moyen des vignes
    age_moyen = None
    if encepagements:
        ages = [e.age_vignes for e in encepagements if e.age_vignes]
        if ages:
            age_moyen = sum(ages) // len(ages)
    
    # Données météo (si coordonnées disponibles)
    weather_forecasts = []
    weather_alerts = []
    if parcelle.latitude and parcelle.longitude:
        try:
            from apps.ai.smart_suggestions import WeatherService
            weather_forecasts = WeatherService.get_forecast(
                float(parcelle.latitude), 
                float(parcelle.longitude), 
                days=3
            )
            # Générer les alertes météo
            nudges = WeatherService.get_parcelle_alerts(parcelle)
            weather_alerts = [
                {
                    'title': n.title,
                    'message': n.message,
                    'type': 'warning' if n.nudge_type.value in ['warning', 'alert'] else 'info',
                }
                for n in nudges
            ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Weather fetch error: {e}")
    
    context = {
        'parcelle': parcelle,
        'organization': organization,
        'page_title': f'Parcelle : {parcelle.nom}',
        # Encépagement
        'encepagements': encepagements,
        'encepagement_total_pct': encepagement_total_pct,
        'surface_plantee': surface_plantee,
        'age_moyen_vignes': age_moyen,
        # Vendanges
        'vendanges': vendanges,
        'derniere_vendange': derniere_vendange,
        'total_recolte_kg': total_recolte_kg,
        'rendement_moyen': rendement_moyen,
        # Journal
        'operations': operations,
        # Timeline
        'timeline': timeline,
        # Calculs
        'surface_m2': surface_m2,
        'estimation_bouteilles': estimation_bouteilles,
        # Météo
        'weather_forecasts': weather_forecasts,
        'weather_alerts': weather_alerts,
    }
    
    return render(request, 'referentiels/parcelle_detail.html', context)


@require_perm('parcelles', 'edit')
@require_http_methods(["GET", "POST"])
def parcelle_create(request):
    """Création d'une parcelle"""
    organization = request.current_org
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    cepages = Cepage.objects.filter(organization=organization).order_by('nom')
    
    if request.method == 'POST':
        form = ParcelleForm(request.POST, organization=organization)
        if form.is_valid():
            parcelle = form.save(commit=False)
            parcelle.organization = organization
            gj_str = form.cleaned_data.get('geojson') or ''
            if gj_str:
                try:
                    gj = json.loads(gj_str)
                    parcelle.geojson = gj
                    metrics = _compute_metrics_from_geojson(gj)
                    for k, v in metrics.items():
                        setattr(parcelle, k, v)
                    if (not parcelle.surface) and metrics.get('area_m2'):
                        try:
                            parcelle.surface = (Decimal(str(metrics['area_m2'])) / Decimal('10000')).quantize(Decimal('0.01'))
                        except Exception:
                            pass
                except Exception:
                    form.add_error('geojson', 'GeoJSON invalide')
                    context = {
                        'form': form,
                        'organization': organization,
                        'page_title': 'Nouvelle parcelle',
                        'next': next_url,
                        'cepages': cepages,
                    }
                    return render(request, 'referentiels/parcelle_form.html', context)
            parcelle.save()
            try:
                form.save_m2m()
            except Exception:
                pass
            
            # Traiter les zones GeoJSON (rangs dessinés)
            zones_json = request.POST.get('zones_geojson', '')
            if zones_json:
                try:
                    zones_data = json.loads(zones_json)
                    parcelle.zones_geojson = zones_data
                    parcelle.save(update_fields=['zones_geojson'])
                except Exception:
                    pass
            
            # Traiter les encépagements JSON
            encepagements_json = request.POST.get('encepagements_json', '[]')
            try:
                encepagements_data = json.loads(encepagements_json)
                for enc in encepagements_data:
                    if enc.get('cepage_id') and enc.get('pourcentage'):
                        ParcelleEncepagement.objects.create(
                            parcelle=parcelle,
                            cepage_id=enc['cepage_id'],
                            pourcentage=Decimal(str(enc['pourcentage'])),
                            rang_debut=enc.get('rang_debut') or None,
                            rang_fin=enc.get('rang_fin') or None,
                            annee_plantation=enc.get('annee_plantation') or None,
                            porte_greffe=enc.get('porte_greffe') or '',
                            densite_pieds_ha=enc.get('densite') or None,
                        )
            except Exception:
                pass
            
            messages.success(request, f'La parcelle "{parcelle.nom}" a été créée avec succès.')
            if next_url:
                sep = '&' if ('?' in next_url) else '?'
                return redirect(f"{next_url}{sep}parcelle={parcelle.pk}")
            return redirect('referentiels:parcelle_detail', pk=parcelle.pk)
    else:
        form = ParcelleForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouvelle parcelle',
        'next': next_url,
        'cepages': cepages,
    }
    
    return render(request, 'referentiels/parcelle_form.html', context)


@require_perm('parcelles', 'edit')
@require_http_methods(["GET", "POST"])
def parcelle_update(request, pk):
    """Modification d'une parcelle"""
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=pk, organization=organization)
    cepages = Cepage.objects.filter(organization=organization).order_by('nom')
    
    if request.method == 'POST':
        form = ParcelleForm(request.POST, instance=parcelle, organization=organization)
        if form.is_valid():
            obj = form.save(commit=False)
            gj_str = form.cleaned_data.get('geojson') or ''
            if gj_str:
                try:
                    gj = json.loads(gj_str)
                    obj.geojson = gj
                    metrics = _compute_metrics_from_geojson(gj)
                    for k, v in metrics.items():
                        setattr(obj, k, v)
                    if (not obj.surface) and metrics.get('area_m2'):
                        try:
                            obj.surface = (Decimal(str(metrics['area_m2'])) / Decimal('10000')).quantize(Decimal('0.01'))
                        except Exception:
                            pass
                except Exception:
                    form.add_error('geojson', 'GeoJSON invalide')
                    context = {
                        'form': form,
                        'parcelle': parcelle,
                        'organization': organization,
                        'page_title': f'Modifier : {parcelle.nom}',
                        'cepages': cepages,
                    }
                    return render(request, 'referentiels/parcelle_form.html', context)
            obj.save()
            try:
                form.save_m2m()
            except Exception:
                pass
            
            # Traiter les zones GeoJSON (rangs dessinés)
            zones_json = request.POST.get('zones_geojson', '')
            if zones_json:
                try:
                    zones_data = json.loads(zones_json)
                    obj.zones_geojson = zones_data
                    obj.save(update_fields=['zones_geojson'])
                except Exception:
                    pass
            
            # Traiter les encépagements JSON - supprimer les anciens et recréer
            encepagements_json = request.POST.get('encepagements_json', '[]')
            try:
                encepagements_data = json.loads(encepagements_json)
                # Supprimer les anciens encépagements
                ParcelleEncepagement.objects.filter(parcelle=obj).delete()
                # Créer les nouveaux
                for enc in encepagements_data:
                    if enc.get('cepage_id') and enc.get('pourcentage'):
                        ParcelleEncepagement.objects.create(
                            parcelle=obj,
                            cepage_id=enc['cepage_id'],
                            pourcentage=Decimal(str(enc['pourcentage'])),
                            rang_debut=enc.get('rang_debut') or None,
                            rang_fin=enc.get('rang_fin') or None,
                            annee_plantation=enc.get('annee_plantation') or None,
                            porte_greffe=enc.get('porte_greffe') or '',
                            densite_pieds_ha=enc.get('densite') or None,
                        )
            except Exception:
                pass
            
            messages.success(request, f'La parcelle "{obj.nom}" a été modifiée avec succès.')
            return redirect('referentiels:parcelle_detail', pk=obj.pk)
    else:
        form = ParcelleForm(instance=parcelle, organization=organization)
    
    context = {
        'form': form,
        'parcelle': parcelle,
        'organization': organization,
        'page_title': f'Modifier : {parcelle.nom}',
        'cepages': cepages,
    }
    
    return render(request, 'referentiels/parcelle_form.html', context)


@require_perm('parcelles', 'edit', role_min='admin')
@require_http_methods(["POST"])
def parcelle_delete(request, pk):
    """Suppression d'une parcelle"""
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=pk, organization=organization)
    
    nom = parcelle.nom
    parcelle.delete()
    
    messages.success(request, f'La parcelle "{nom}" a été supprimée avec succès.')
    return redirect('referentiels:parcelle_list')


# ===== ENCÉPAGEMENT =====

@require_perm('parcelles', 'edit')
@require_http_methods(["GET", "POST"])
def encepagement_add(request, parcelle_pk):
    """Page de gestion complète des encépagements d'une parcelle"""
    from decimal import Decimal, InvalidOperation
    
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=parcelle_pk, organization=organization)
    cepages = Cepage.objects.filter(organization=organization).order_by('nom')
    
    if request.method == 'POST':
        # Traitement des suppressions
        delete_ids = request.POST.get('delete_ids', '').strip()
        if delete_ids:
            for del_id in delete_ids.split(','):
                if del_id.strip():
                    try:
                        ParcelleEncepagement.objects.filter(pk=int(del_id), parcelle=parcelle).delete()
                    except (ValueError, ParcelleEncepagement.DoesNotExist):
                        pass
        
        # Traitement des encépagements existants (mise à jour)
        for enc in parcelle.encepagements.all():
            prefix = f'enc_{enc.pk}_'
            cepage_id = request.POST.get(f'{prefix}cepage')
            pct = request.POST.get(f'{prefix}pct')
            
            if cepage_id and pct:
                try:
                    enc.cepage_id = int(cepage_id)
                    enc.pourcentage = Decimal(pct.replace(',', '.'))
                    enc.rang_debut = int(request.POST.get(f'{prefix}rang_debut') or 0) or None
                    enc.rang_fin = int(request.POST.get(f'{prefix}rang_fin') or 0) or None
                    enc.annee_plantation = int(request.POST.get(f'{prefix}annee') or 0) or None
                    enc.porte_greffe = request.POST.get(f'{prefix}porte_greffe', '').strip()
                    enc.densite_pieds_ha = int(request.POST.get(f'{prefix}densite') or 0) or None
                    enc.notes = request.POST.get(f'{prefix}notes', '').strip()
                    enc.save()
                except (ValueError, InvalidOperation):
                    pass
        
        # Traitement des nouveaux encépagements
        new_index = 0
        while True:
            prefix = f'new_{new_index}_'
            cepage_id = request.POST.get(f'{prefix}cepage')
            pct = request.POST.get(f'{prefix}pct')
            
            if not cepage_id:
                break
            
            if cepage_id and pct:
                try:
                    ParcelleEncepagement.objects.create(
                        parcelle=parcelle,
                        cepage_id=int(cepage_id),
                        pourcentage=Decimal(pct.replace(',', '.')),
                        rang_debut=int(request.POST.get(f'{prefix}rang_debut') or 0) or None,
                        rang_fin=int(request.POST.get(f'{prefix}rang_fin') or 0) or None,
                        annee_plantation=int(request.POST.get(f'{prefix}annee') or 0) or None,
                        porte_greffe=request.POST.get(f'{prefix}porte_greffe', '').strip(),
                        densite_pieds_ha=int(request.POST.get(f'{prefix}densite') or 0) or None,
                        notes=request.POST.get(f'{prefix}notes', '').strip(),
                    )
                except (ValueError, InvalidOperation):
                    pass
            
            new_index += 1
        
        messages.success(request, 'L\'encépagement a été mis à jour avec succès.')
        return redirect('production:parcelle_detail', pk=parcelle.pk)
    
    # GET: Afficher la page de gestion
    encepagements = parcelle.encepagements.select_related('cepage').all()
    total_pourcentage = sum(e.pourcentage for e in encepagements) if encepagements else Decimal('0')
    
    context = {
        'parcelle': parcelle,
        'encepagements': encepagements,
        'cepages': cepages,
        'total_pourcentage': total_pourcentage,
        'organization': organization,
        'page_title': f'Encépagement - {parcelle.nom}',
    }
    return render(request, 'referentiels/encepagement_manage.html', context)


@require_perm('parcelles', 'edit')
@require_http_methods(["GET", "POST"])
def encepagement_edit(request, parcelle_pk, pk):
    """Modifier un encépagement"""
    from .forms import ParcelleEncepagementForm
    
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=parcelle_pk, organization=organization)
    encepagement = get_object_or_404(ParcelleEncepagement, pk=pk, parcelle=parcelle)
    
    if request.method == 'POST':
        form = ParcelleEncepagementForm(request.POST, instance=encepagement, organization=organization, parcelle=parcelle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Encépagement "{encepagement.cepage.nom}" modifié avec succès.')
            return redirect('referentiels:parcelle_detail', pk=parcelle.pk)
    else:
        form = ParcelleEncepagementForm(instance=encepagement, organization=organization, parcelle=parcelle)
    
    context = {
        'form': form,
        'parcelle': parcelle,
        'encepagement': encepagement,
        'organization': organization,
        'page_title': f'Modifier encépagement - {parcelle.nom}',
    }
    return render(request, 'referentiels/encepagement_form.html', context)


@require_perm('parcelles', 'edit')
@require_http_methods(["POST"])
def encepagement_delete(request, parcelle_pk, pk):
    """Supprimer un encépagement"""
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=parcelle_pk, organization=organization)
    encepagement = get_object_or_404(ParcelleEncepagement, pk=pk, parcelle=parcelle)
    
    cepage_nom = encepagement.cepage.nom
    encepagement.delete()
    
    messages.success(request, f'Encépagement "{cepage_nom}" supprimé.')
    return redirect('referentiels:parcelle_detail', pk=parcelle.pk)


# ===== UNITÉS =====

@require_membership(role_min='read_only')
def unite_list(request):
    """Liste des unités - Roadmap item 16"""
    organization = request.current_org
    unites = Unite.objects.filter(organization=organization)

    # JSON content negotiation for API usage
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept or request.GET.get('format') == 'json':
        items = []
        for u in unites.order_by('nom'):
            items.append({
                'id': u.id,
                'nom': u.nom,
                'symbole': u.symbole,
                'type': getattr(u, 'type_unite', ''),
                'facteur': float(u.facteur_conversion) if u.facteur_conversion is not None else None,
            })
        return JsonResponse(items, safe=False)
    
    # Recherche simple
    search = request.GET.get('search', '')
    if search:
        unites = unites.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(unites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'organization': organization,
        'page_title': 'Unités'
    }
    
    return render(request, 'referentiels/unite_list.html', context)


@require_membership(role_min='read_only')
def unite_detail(request, pk):
    """Détail d'une unité"""
    organization = request.current_org
    unite = get_object_or_404(Unite, pk=pk, organization=organization)
    
    context = {
        'unite': unite,
        'organization': organization,
        'page_title': f'Unité : {unite.nom}'
    }
    
    return render(request, 'referentiels/unite_detail.html', context)


@require_membership(role_min='editor')
@require_http_methods(["GET", "POST"])
def unite_create(request):
    """Création d'une unité"""
    organization = request.current_org
    
    if request.method == 'POST':
        form = UniteForm(request.POST, organization=organization)
        if form.is_valid():
            unite = form.save(commit=False)
            unite.organization = organization
            unite.save()
            
            messages.success(request, f'L\'unité "{unite.nom}" a été créée avec succès.')
            return redirect('referentiels:unite_detail', pk=unite.pk)
    else:
        form = UniteForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouvelle unité'
    }
    
    return render(request, 'referentiels/unite_form.html', context)


@require_membership(role_min='editor')
@require_http_methods(["GET", "POST"])
def unite_update(request, pk):
    """Modification d'une unité"""
    organization = request.current_org
    unite = get_object_or_404(Unite, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = UniteForm(request.POST, instance=unite, organization=organization)
        if form.is_valid():
            unite = form.save()
            
            messages.success(request, f'L\'unité "{unite.nom}" a été modifiée avec succès.')
            return redirect('referentiels:unite_detail', pk=unite.pk)
    else:
        form = UniteForm(instance=unite, organization=organization)
    
    context = {
        'form': form,
        'unite': unite,
        'organization': organization,
        'page_title': f'Modifier : {unite.nom}'
    }
    
    return render(request, 'referentiels/unite_form.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def unite_delete(request, pk):
    """Suppression d'une unité"""
    organization = request.current_org
    unite = get_object_or_404(Unite, pk=pk, organization=organization)
    
    nom = unite.nom
    unite.delete()
    
    messages.success(request, f'L\'unité "{nom}" a été supprimée avec succès.')
    return redirect('referentiels:unite_list')


# ===== PAGE D'ACCUEIL RÉFÉRENTIELS =====

@require_membership(role_min='read_only')
def referentiels_home(request):
    """Page d'accueil des référentiels"""
    organization = request.current_org
    
    # Compter les éléments de chaque référentiel
    stats = {
        'cepages': Cepage.objects.filter(organization=organization).count(),
        'parcelles': Parcelle.objects.filter(organization=organization).count(),
        'unites': Unite.objects.filter(organization=organization).count(),
        'cuvees': Cuvee.objects.filter(organization=organization).count(),
        'entrepots': Entrepot.objects.filter(organization=organization).count(),
    }
    
    context = {
        'stats': stats,
        'organization': organization,
        'page_title': 'Référentiels'
    }
    
    return render(request, 'referentiels/home.html', context)


# ===== CUVÉES =====

@require_membership(role_min='read_only')
def cuvee_list(request):
    """Liste des cuvées - Roadmap item 17"""
    organization = request.current_org
    cuvees = Cuvee.objects.filter(organization=organization)
    
    # Recherche simple
    search = request.GET.get('search', '')
    if search:
        cuvees = cuvees.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(cuvees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'organization': organization,
        'page_title': 'Cuvées'
    }
    
    return render(request, 'referentiels/cuvee_list.html', context)


@require_membership(role_min='read_only')
def cuvee_detail(request, pk):
    """Détail d'une cuvée"""
    organization = request.current_org
    cuvee = get_object_or_404(Cuvee, pk=pk, organization=organization)
    
    context = {
        'cuvee': cuvee,
        'organization': organization,
        'page_title': f'Cuvée : {cuvee.nom}'
    }
    
    return render(request, 'referentiels/cuvee_detail.html', context)


@require_membership(role_min='editor')
def cuvee_create(request):
    """Création d'une nouvelle cuvée"""
    organization = request.current_org
    
    if request.method == 'POST':
        form = CuveeForm(request.POST, organization=organization)
        if form.is_valid():
            cuvee = form.save(commit=False)
            cuvee.organization = organization
            cuvee.save()
            form.save_m2m()  # Pour les relations ManyToMany (cépages)
            
            messages.success(request, f'La cuvée "{cuvee.nom}" a été créée avec succès.')
            return redirect('referentiels:cuvee_detail', pk=cuvee.pk)
    else:
        form = CuveeForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouvelle cuvée'
    }
    
    return render(request, 'referentiels/cuvee_form.html', context)


@require_membership(role_min='editor')
def cuvee_update(request, pk):
    """Modification d'une cuvée"""
    organization = request.current_org
    cuvee = get_object_or_404(Cuvee, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = CuveeForm(request.POST, instance=cuvee, organization=organization)
        if form.is_valid():
            cuvee = form.save()
            
            messages.success(request, f'La cuvée "{cuvee.nom}" a été modifiée avec succès.')
            return redirect('referentiels:cuvee_detail', pk=cuvee.pk)
    else:
        form = CuveeForm(instance=cuvee, organization=organization)
    
    context = {
        'form': form,
        'cuvee': cuvee,
        'organization': organization,
        'page_title': f'Modifier : {cuvee.nom}'
    }
    
    return render(request, 'referentiels/cuvee_form.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def cuvee_delete(request, pk):
    """Suppression d'une cuvée"""
    organization = request.current_org
    cuvee = get_object_or_404(Cuvee, pk=pk, organization=organization)
    
    nom = cuvee.nom
    cuvee.delete()
    
    messages.success(request, f'La cuvée "{nom}" a été supprimée avec succès.')
    return redirect('referentiels:cuvee_list')


# ===== ENTREPÔTS =====

@require_membership(role_min='read_only')
def entrepot_list(request):
    """Liste des entrepôts - Roadmap item 18"""
    organization = request.current_org
    entrepots = Entrepot.objects.filter(organization=organization)
    
    # Recherche simple
    search = request.GET.get('search', '')
    if search:
        entrepots = entrepots.filter(nom__icontains=search)
    
    # Pagination
    paginator = Paginator(entrepots, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'organization': organization,
        'page_title': 'Entrepôts'
    }
    
    return render(request, 'referentiels/entrepot_list.html', context)


@require_membership(role_min='read_only')
def entrepot_detail(request, pk):
    """Détail d'un entrepôt"""
    organization = request.current_org
    entrepot = get_object_or_404(Entrepot, pk=pk, organization=organization)
    
    context = {
        'entrepot': entrepot,
        'organization': organization,
        'page_title': f'Entrepôt : {entrepot.nom}'
    }
    
    return render(request, 'referentiels/entrepot_detail.html', context)


@require_membership(role_min='editor')
def entrepot_create(request):
    """Création d'un nouvel entrepôt"""
    organization = request.current_org
    
    if request.method == 'POST':
        form = EntrepotForm(request.POST, organization=organization)
        if form.is_valid():
            entrepot = form.save(commit=False)
            entrepot.organization = organization
            entrepot.save()
            
            messages.success(request, f'L\'entrepôt "{entrepot.nom}" a été créé avec succès.')
            return redirect('referentiels:entrepot_detail', pk=entrepot.pk)
    else:
        form = EntrepotForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouvel entrepôt'
    }
    
    return render(request, 'referentiels/entrepot_form.html', context)


@require_membership(role_min='editor')
def entrepot_update(request, pk):
    """Modification d'un entrepôt"""
    organization = request.current_org
    entrepot = get_object_or_404(Entrepot, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = EntrepotForm(request.POST, instance=entrepot, organization=organization)
        if form.is_valid():
            entrepot = form.save()
            
            messages.success(request, f'L\'entrepôt "{entrepot.nom}" a été modifié avec succès.')
            return redirect('referentiels:entrepot_detail', pk=entrepot.pk)
    else:
        form = EntrepotForm(instance=entrepot, organization=organization)
    
    context = {
        'form': form,
        'entrepot': entrepot,
        'organization': organization,
        'page_title': f'Modifier : {entrepot.nom}'
    }
    
    return render(request, 'referentiels/entrepot_form.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def entrepot_delete(request, pk):
    """Suppression d'un entrepôt"""
    organization = request.current_org
    entrepot = get_object_or_404(Entrepot, pk=pk, organization=organization)
    
    nom = entrepot.nom
    entrepot.delete()
    
    messages.success(request, f'L\'entrepôt "{nom}" a été supprimé avec succès.')
    return redirect('referentiels:entrepot_list')


# ===== IMPORT CSV - ROADMAP 18 =====

@require_membership(role_min='admin')
def import_csv(request):
    """Page d'import CSV des référentiels - Roadmap 18"""
    organization = request.current_org
    
    # Types d'import supportés
    import_types = [
        {'key': 'grape', 'label': 'Cépages', 'fields': ['nom', 'couleur', 'code', 'notes']},
        {'key': 'parcelle', 'label': 'Parcelles', 'fields': ['nom', 'surface_ha', 'notes']},
        {'key': 'unite', 'label': 'Unités', 'fields': ['nom', 'code', 'notes']},
        {'key': 'cuvee', 'label': 'Cuvées', 'fields': ['nom', 'notes']},
        {'key': 'entrepot', 'label': 'Entrepôts', 'fields': ['nom', 'notes']},
    ]
    
    # Pré-sélection du type via paramètre GET
    preselected_type = request.GET.get('type', '')
    valid_types = [item['key'] for item in import_types]
    if preselected_type not in valid_types:
        preselected_type = ''
    
    # Convertir en format JSON pour JavaScript
    import_types_json = {}
    for item in import_types:
        import_types_json[item['key']] = {
            'label': item['label'],
            'fields': item['fields']
        }
    
    context = {
        'import_types': import_types,
        'import_types_json': json.dumps(import_types_json),
        'preselected_type': preselected_type,
        'organization': organization,
        'page_title': 'Import CSV des référentiels'
    }
    
    return render(request, 'referentiels/import_csv.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def import_csv_preview(request):
    """Prévisualisation de l'import CSV"""
    organization = request.current_org
    
    try:
        # Récupérer les données du formulaire
        import_type = request.POST.get('import_type')
        csv_file = request.FILES.get('csv_file')
        
        if not import_type or not csv_file:
            return JsonResponse({
                'error': 'Type d\'import et fichier CSV requis'
            }, status=400)
        
        # Vérifier la taille du fichier (10MB max)
        if csv_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'error': 'Fichier trop volumineux (maximum 10MB)'
            }, status=400)
        
        # Initialiser le service d'import
        import_service = CSVImportService(organization)
        
        # Parser le fichier CSV
        headers, rows, encoding = import_service.parse_csv_file(csv_file)
        
        # Limiter à 10000 lignes
        if len(rows) > 10000:
            return JsonResponse({
                'error': 'Trop de lignes (maximum 10000)'
            }, status=400)
        
        # Mapping automatique des colonnes
        config = import_service.SUPPORTED_TYPES.get(import_type, {})
        expected_fields = config.get('fields', [])
        
        auto_mapping = {}
        for header in headers:
            header_lower = header.lower().strip()
            for field in expected_fields:
                if field.lower() in header_lower or header_lower in field.lower():
                    auto_mapping[header] = field
                    break
        
        # Prévisualisation
        preview_result = import_service.preview_import(
            import_type, headers, rows, auto_mapping, limit=10
        )
        
        # Stocker les données en session pour l'exécution
        request.session['csv_import_data'] = {
            'import_type': import_type,
            'headers': headers,
            'rows': rows[:1000],  # Limiter pour la session
            'encoding': encoding,
            'total_rows': len(rows)
        }
        
        return JsonResponse({
            'success': True,
            'headers': headers,
            'expected_fields': expected_fields,
            'auto_mapping': auto_mapping,
            'preview': preview_result['preview'],
            'errors': preview_result['errors'],
            'warnings': preview_result['warnings'],
            'total_rows': len(rows),
            'encoding': encoding
        })
        
    except CSVImportError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur inattendue: {str(e)}'}, status=500)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def import_csv_execute(request):
    """Exécution de l'import CSV"""
    organization = request.current_org
    
    try:
        # Récupérer les données de la session
        import_data = request.session.get('csv_import_data')
        if not import_data:
            return JsonResponse({
                'error': 'Données d\'import non trouvées. Veuillez recommencer.'
            }, status=400)
        
        # Récupérer le mapping des colonnes
        mapping_data = request.POST.get('mapping')
        if not mapping_data:
            return JsonResponse({
                'error': 'Mapping des colonnes requis'
            }, status=400)
        
        try:
            mapping = json.loads(mapping_data)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Format de mapping invalide'
            }, status=400)
        
        # Initialiser le service d'import
        import_service = CSVImportService(organization)
        
        # Valider le mapping
        mapping_errors = import_service.validate_mapping(
            import_data['import_type'], mapping
        )
        if mapping_errors:
            return JsonResponse({
                'error': 'Erreurs de mapping: ' + ', '.join(mapping_errors)
            }, status=400)
        
        # Exécuter l'import
        result = import_service.execute_import(
            import_data['import_type'],
            import_data['headers'],
            import_data['rows'],
            mapping
        )
        
        # Nettoyer la session
        if 'csv_import_data' in request.session:
            del request.session['csv_import_data']
        
        # Générer le rapport d'erreurs si nécessaire
        error_report_csv = None
        if result['error_details']:
            error_report_csv = import_service.generate_error_report(
                result['error_details']
            )
        
        return JsonResponse({
            'success': True,
            'created': result['created'],
            'updated': result['updated'],
            'errors': result['errors'],
            'total_processed': result['total_processed'],
            'error_details': result['error_details'],
            'error_report_csv': error_report_csv
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de l\'import: {str(e)}'}, status=500)


@require_membership(role_min='admin')
def import_csv_download_errors(request):
    """Téléchargement du rapport d'erreurs CSV"""
    error_report = request.GET.get('report')
    if not error_report:
        return HttpResponse('Rapport non trouvé', status=404)
    
    response = HttpResponse(error_report, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="erreurs_import.csv"'
    return response


# ===== NEW: Secure Import Pipeline (Drag-and-Drop) =====

ALLOWED_IMPORT_EXTS = {'.csv', '.txt'}  # CSV-only quick-win; add xlsx/ods/json later


def _guess_ext(name):
    try:
        return (name and name.lower().rsplit('.', 1)[-1]) and ('.' + name.lower().rsplit('.', 1)[-1])
    except Exception:
        return ''


def _sanitize_cell(v: str) -> str:
    try:
        s = (v or '').strip()
        if not s:
            return ''
        if s[0] in ('=', '+', '-', '@'):
            return "'" + s  # neutralize potential spreadsheet formulas
        return s
    except Exception:
        return ''


def _auto_mapping(headers, expected_fields):
    syn = {
        'nom': ['nom', 'name', 'libelle', 'libellé', 'titre'],
        'couleur': ['couleur', 'color'],
        'code': ['code', 'sku', 'ref', 'reference'],
        'notes': ['notes', 'commentaire', 'comments'],
        'surface_ha': ['surface', 'surface_ha', 'ha', 'hectares'],
        'commune': ['commune', 'city', 'ville'],
        'appellation': ['appellation', 'aoc', 'igp'],
    }
    mapping = {}
    for h in headers:
        hl = (h or '').strip().lower()
        for field in expected_fields:
            cands = syn.get(field, [field])
            if any(k in hl for k in cands):
                mapping[h] = field
                break
    return mapping


@require_membership(role_min='admin')
@csrf_exempt
@require_http_methods(["POST"])
def import_intake_api(request):
    """Step 1: Secure intake to quarantine, returns batch_id + header/mapping suggestions."""
    org = request.current_org
    up = request.FILES.get('file') or request.FILES.get('csv_file')
    if not up:
        return JsonResponse({'error': 'Aucun fichier transmis'}, status=400)

    if up.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'Fichier trop volumineux (>10 Mo)'}, status=400)

    ext = _guess_ext(getattr(up, 'name', ''))
    if ext not in ALLOWED_IMPORT_EXTS:
        return JsonResponse({'error': f'Type non supporté ({ext}). Utilisez CSV ou JSON.'}, status=400)

    # Read bytes and compute sha256
    try:
        data = up.read()
    except Exception:
        return JsonResponse({'error': 'Lecture du fichier impossible'}, status=400)

    sha = hashlib.sha256(data).hexdigest()
    content_type = up.content_type or mimetypes.guess_type(up.name or '')[0] or 'application/octet-stream'

    # Quarantine store
    batch = ImportBatch.objects.create(
        organization=org,
        user=getattr(request, 'user', None),
        original_name=up.name or 'upload',
        content_type=content_type,
        size=len(data),
        sha256=sha,
        status='quarantine',
    )
    batch.file.save(up.name or 'upload', ContentFile(data), save=True)

    # Decode and parse headers
    from .csv_import import CSVImportService
    svc = CSVImportService(org)
    encoding = svc.detect_encoding(data)
    try:
        text = data.decode(encoding)
    except Exception:
        return JsonResponse({'error': f'Encodage invalide ({encoding})'}, status=400)
    delimiter = svc.detect_delimiter(text)
    try:
        import csv, io
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
    except Exception as e:
        return JsonResponse({'error': f'CSV invalide: {e}'}, status=400)
    if not rows:
        return JsonResponse({'error': 'Fichier vide'}, status=400)
    headers = [h.strip() for h in rows[0]]

    # Determine best entity type by coverage score
    best_type = None
    best_score = -1
    for key, cfg in CSVImportService.SUPPORTED_TYPES.items():
        mm = _auto_mapping(headers, cfg.get('fields', []))
        score = len(mm)
        if score > best_score:
            best_score = score
            best_type = key
            best_mapping = mm

    return JsonResponse({
        'success': True,
        'batch_id': batch.id,
        'encoding': encoding,
        'delimiter': delimiter,
        'headers': headers,
        'entity_type_suggestion': best_type,
        'mapping_suggestions': best_mapping,
        'total_rows': max(0, len(rows) - 1),
    })


@require_membership(role_min='admin')
@csrf_exempt
@require_http_methods(["POST"])
def import_preview_api(request):
    """Step 2-3: Preview + pre-normalization with completeness/confidence and side artifacts suggestions."""
    org = request.current_org
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    batch_id = payload.get('batch_id')
    entity_type = payload.get('entity_type')
    mapping = payload.get('mapping') or {}
    if not batch_id or not entity_type:
        return JsonResponse({'error': 'batch_id et entity_type requis'}, status=400)

    batch = get_object_or_404(ImportBatch, pk=batch_id, organization=org)
    try:
        batch.file.open('rb')
    except Exception:
        pass
    data = batch.file.read()
    from .csv_import import CSVImportService
    svc = CSVImportService(org)
    encoding = svc.detect_encoding(data)
    text = data.decode(encoding)
    delimiter = svc.detect_delimiter(text)
    import csv, io
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    headers = [h.strip() for h in rows[0]]
    sample = rows[1: min(len(rows), 11)]

    exp_fields = CSVImportService.SUPPORTED_TYPES.get(entity_type, {}).get('fields', [])
    if not mapping:
        mapping = _auto_mapping(headers, exp_fields)

    # Build preview with sanitized values and completeness score
    preview = []
    side_missing = {'cepages': set(), 'formats': set(), 'familles': set(), 'appellations': set(), 'parcelles': set(), 'vendanges': set()}
    for idx, row in enumerate(sample, 1):
        data_map = {}
        for i, h in enumerate(headers):
            f = mapping.get(h)
            if not f:
                continue
            val = row[i] if i < len(row) else ''
            data_map[f] = _sanitize_cell(val)
        # completeness: ratio of non-empty over expected fields
        exp_nonempty = [1 for f in exp_fields if data_map.get(f)]
        completeness = int(100 * (sum(exp_nonempty) / max(1, len(exp_fields))))
        preview.append({'line': idx, 'data': data_map, 'completeness': completeness, 'errors': []})

        # Side artifacts quick detection (names present but possibly unknown)
        n = data_map.get('nom')
        app = data_map.get('appellation')
        if n:
            if entity_type == 'grape':
                from .models import Cepage
                if not Cepage.objects.filter(organization=org, name_norm=Cepage.normalize_name(n)).exists():
                    side_missing['cepages'].add(n)
            elif entity_type == 'parcelle':
                from .models import Parcelle
                if not Parcelle.objects.filter(organization=org, nom__iexact=n).exists():
                    side_missing['parcelles'].add(n)
            elif entity_type == 'cuvee' and app:
                from apps.viticulture.models import Appellation
                if not Appellation.objects.filter(organization=org, name_norm=app.lower().strip()).exists():
                    side_missing['appellations'].add(app)

    side_suggestions = {
        'cepages': sorted(list(side_missing['cepages']))[:10],
        'parcelles': sorted(list(side_missing['parcelles']))[:10],
        'appellations': sorted(list(side_missing['appellations']))[:10],
    }

    return JsonResponse({
        'success': True,
        'batch_id': batch.id,
        'entity_type': entity_type,
        'headers': headers,
        'mapping': mapping,
        'preview': preview,
        'side_artifacts_suggestions': {
            'counts': {k: len(v) for k, v in side_missing.items()},
            'examples': side_suggestions,
        }
    })


@require_membership(role_min='admin')
@csrf_exempt
@require_http_methods(["POST"])
def import_execute_api(request):
    """Step 5: Execute with min_confidence and optional side artifacts creation (minimal quick-win)."""
    org = request.current_org
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    batch_id = payload.get('batch_id')
    entity_type = payload.get('entity_type')
    mapping = payload.get('mapping') or {}
    min_conf = float(payload.get('min_confidence') or 0.9)
    create_side = bool(payload.get('create_side_artifacts') or False)
    if not batch_id or not entity_type or not mapping:
        return JsonResponse({'error': 'batch_id, entity_type et mapping requis'}, status=400)

    batch = get_object_or_404(ImportBatch, pk=batch_id, organization=org)
    # Re-parse file
    try:
        batch.file.open('rb')
    except Exception:
        pass
    data = batch.file.read()
    from .csv_import import CSVImportService
    svc = CSVImportService(org)
    encoding = svc.detect_encoding(data)
    text = data.decode(encoding)
    delimiter = svc.detect_delimiter(text)
    import csv, io, uuid
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    headers = [h.strip() for h in rows[0]]
    body_rows = rows[1:]

    # Filter rows by completeness as proxy for confidence
    exp_fields = CSVImportService.SUPPORTED_TYPES.get(entity_type, {}).get('fields', [])
    filtered_rows = []
    for row in body_rows:
        data_map = {}
        for i, h in enumerate(headers):
            f = mapping.get(h)
            if not f:
                continue
            val = row[i] if i < len(row) else ''
            data_map[f] = _sanitize_cell(val)
        completeness = (sum(1 for f in exp_fields if data_map.get(f)) / max(1, len(exp_fields)))
        if completeness >= min_conf:
            # reconstruct row in the same order as headers for service
            # Keep original row but sanitize the used cells only
            filtered_rows.append(row)

    # Execute via service
    try:
        result = svc.execute_import(entity_type, headers, filtered_rows, mapping)
    except Exception as e:
        return JsonResponse({'error': f'Echec import: {e}'}, status=500)

    undo_token = uuid.uuid4().hex
    ImportExecution.objects.create(
        organization=org,
        batch=batch,
        undo_token=undo_token,
        created_objects=[],
    )

    # Quick-win: optionally create missing Appellations referenced by cuvée data
    alerts = []
    if create_side and entity_type == 'cuvee':
        try:
            from apps.viticulture.models import Appellation
            created = 0
            for row in body_rows:
                try:
                    dm = {}
                    for i, h in enumerate(headers):
                        f = mapping.get(h)
                        if f:
                            dm[f] = _sanitize_cell(row[i] if i < len(row) else '')
                    name = (dm.get('appellation') or '').strip()
                    if name and not Appellation.objects.filter(organization=org, name_norm=name.lower().strip()).exists():
                        Appellation.objects.create(organization=org, name=name, type='autre')
                        created += 1
                except Exception:
                    pass
            if created:
                alerts.append(f"{created} appellations créées (quick-win)")
        except Exception:
            pass

    return JsonResponse({
        'success': True,
        'created': result.get('created', 0),
        'updated': result.get('updated', 0),
        'errors': result.get('errors', 0),
        'total_processed': result.get('total_processed', 0),
        'error_details': result.get('error_details', []),
        'undo_token': undo_token,
        'alerts': alerts,
    })


# ===== EXPORT CSV =====

@require_membership(role_min='read_only')
def export_cepages(request):
    """Export CSV des cépages"""
    organization = request.current_org
    
    # Récupérer les mêmes filtres que la liste
    cepages = Cepage.objects.filter(organization=organization, is_active=True)
    
    # Appliquer les filtres de recherche si présents
    search = request.GET.get('search', '').strip()
    if search:
        cepages = cepages.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search) |
            Q(notes__icontains=search)
        )
    
    # Paramètres d'export
    encoding = request.GET.get('encoding', 'utf-8')
    delimiter = request.GET.get('delimiter', ';')
    
    # Exporter
    export_service = CSVExportService(organization)
    return export_service.export_entity('cepages', cepages, encoding=encoding, delimiter=delimiter)

@require_membership(role_min='read_only')
def export_parcelles(request):
    """Export CSV des parcelles"""
    organization = request.current_org
    parcelles = Parcelle.objects.filter(organization=organization)
    
    search = request.GET.get('search', '')
    if search:
        parcelles = parcelles.filter(nom__icontains=search)
    
    encoding = request.GET.get('encoding', 'utf-8')
    delimiter = request.GET.get('delimiter', ';')
    
    export_service = CSVExportService(organization)
    return export_service.export_entity('parcelles', parcelles, encoding=encoding, delimiter=delimiter)

@require_membership(role_min='read_only')
def export_unites(request):
    """Export CSV des unités"""
    organization = request.current_org
    unites = Unite.objects.filter(organization=organization)
    
    search = request.GET.get('search', '')
    if search:
        unites = unites.filter(nom__icontains=search)
    
    encoding = request.GET.get('encoding', 'utf-8')
    delimiter = request.GET.get('delimiter', ';')
    
    export_service = CSVExportService(organization)
    return export_service.export_entity('unites', unites, encoding=encoding, delimiter=delimiter)

@require_membership(role_min='read_only')
def export_cuvees(request):
    """Export CSV des cuvées"""
    organization = request.current_org
    cuvees = Cuvee.objects.filter(organization=organization)
    
    search = request.GET.get('search', '')
    if search:
        cuvees = cuvees.filter(nom__icontains=search)
    
    encoding = request.GET.get('encoding', 'utf-8')
    delimiter = request.GET.get('delimiter', ';')
    
    export_service = CSVExportService(organization)
    return export_service.export_entity('cuvees', cuvees, encoding=encoding, delimiter=delimiter)

@require_membership(role_min='read_only')
def export_entrepots(request):
    """Export CSV des entrepôts"""
    organization = request.current_org
    entrepots = Entrepot.objects.filter(organization=organization)
    
    search = request.GET.get('search', '')
    if search:
        entrepots = entrepots.filter(nom__icontains=search)
    
    encoding = request.GET.get('encoding', 'utf-8')
    delimiter = request.GET.get('delimiter', ';')
    
    export_service = CSVExportService(organization)
    return export_service.export_entity('entrepots', entrepots, encoding=encoding, delimiter=delimiter)


# ===== API CEPAGES PARCELLE =====

@require_membership(role_min='read_only')
def parcelle_cepages_api(request, pk):
    """API JSON: Retourne les cépages d'une parcelle (via encépagement)"""
    organization = request.current_org
    parcelle = get_object_or_404(Parcelle, pk=pk, organization=organization)
    
    # Récupérer les cépages via l'encépagement
    encepagements = parcelle.encepagements.select_related('cepage').order_by('-pourcentage')
    
    cepages = []
    for enc in encepagements:
        cepages.append({
            'id': enc.cepage.pk,
            'nom': enc.cepage.nom,
            'couleur': enc.cepage.couleur,
            'pourcentage': float(enc.pourcentage),
            'rang_debut': enc.rang_debut,
            'rang_fin': enc.rang_fin,
        })
    
    # Si pas d'encépagement, retourner les cépages ManyToMany
    if not cepages:
        for c in parcelle.cepages.all().order_by('nom'):
            cepages.append({
                'id': c.pk,
                'nom': c.nom,
                'couleur': c.couleur,
                'pourcentage': None,
                'rang_debut': None,
                'rang_fin': None,
            })
    
    return JsonResponse({
        'parcelle_id': parcelle.pk,
        'parcelle_nom': parcelle.nom,
        'cepages': cepages,
    })
