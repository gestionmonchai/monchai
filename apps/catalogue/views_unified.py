"""
Vue unifiée pour la gestion des produits avec ergonomie similaire aux clients
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Case, When, Value, IntegerField
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
from datetime import date as dt_date
import uuid as _uuid

from apps.accounts.decorators import require_membership
from apps.referentiels.models import Cepage, Parcelle, Unite, Entrepot
from apps.viticulture.models import (
    Lot,
    Cuvee as ViticultureCuvee,
    Appellation,
    Vintage,
    UnitOfMeasure,
    VineyardPlot,
    GrapeVariety,
    CuveeDetail,
    CuveeParcelleRatio,
    CuveeCepageRatio,
)
from apps.viticulture.models import Warehouse
from apps.viticulture.models_extended import (
    LotDetail,
    LotContainer,
    LotSourceCuvee,
    LotSourceLot,
    LotDocument,
)
from apps.stock.models import SKU, StockSKUBalance, StockVracBalance

# Utiliser le modèle Cuvee de viticulture qui a les bonnes relations
Cuvee = ViticultureCuvee


@login_required
@require_membership()
@require_http_methods(["GET"])
def skus_search_ajax(request):
    """
    Recherche AJAX en temps réel pour les SKUs (produits finis)
    Retourne table_html + pagination_html + stats
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)

    organization = request.current_org
    skus = SKU.objects.filter(organization=organization)

    # Filtres
    from django.db.models import Q
    import uuid as _uuid

    search = (request.GET.get('search') or '').strip()
    if search:
        skus = skus.filter(
            Q(label__icontains=search) |
            Q(code_barres__icontains=search) |
            Q(cuvee__name__icontains=search)
        )

    cuvee_val = (request.GET.get('cuvee') or '').strip()
    if cuvee_val:
        try:
            _ = _uuid.UUID(cuvee_val)
            skus = skus.filter(cuvee_id=cuvee_val)
        except Exception:
            skus = skus.filter(cuvee__name__icontains=cuvee_val)

    uom_val = (request.GET.get('uom') or '').strip()
    if uom_val:
        try:
            _ = _uuid.UUID(uom_val)
            skus = skus.filter(uom_id=uom_val)
        except Exception:
            skus = skus.filter(uom__code__icontains=uom_val)

    is_active = (request.GET.get('is_active') or '').strip()
    if is_active:
        skus = skus.filter(is_active=is_active.lower() in ['true', '1', 'yes'])

    # Tri
    sort_by = (request.GET.get('sort') or 'label').strip()
    sort_order = (request.GET.get('order') or 'asc').strip()
    try:
        skus = skus.annotate(stock_total=Sum('stockskubalance__qty_units'))
    except Exception:
        pass
    sort_map = {
        'label': 'label',
        'cuvee': 'cuvee__name',
        'uom': 'uom__code',
        'volume': 'volume_by_uom_to_l',
        'barcode': 'code_barres',
        'stock': 'stock_total',
        'status': 'is_active',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }
    order_field = sort_map.get(sort_by, 'label')
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    skus = skus.select_related('cuvee', 'uom').order_by(order_field)

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(skus, 25)
    page_obj = paginator.get_page(page_number)

    # Rendus partiels
    from django.template.loader import render_to_string
    table_html = render_to_string(
        'catalogue/partials/sku_table_rows.html',
        {'skus': page_obj, 'page_obj': page_obj},
        request=request,
    )
    pagination_html = render_to_string(
        'catalogue/partials/sku_pagination.html',
        {'page_obj': page_obj},
        request=request,
    )

    total_count = SKU.objects.filter(organization=organization).count()
    filtered_count = skus.count()

    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': total_count,
            'filtered': filtered_count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
        }
    })
@require_http_methods(["GET"])
def cuvees_search_ajax(request):
    """
    Recherche AJAX en temps réel pour les cuvées (même principe que clients)
    Retourne table_html + pagination_html + stats
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)

    organization = request.current_org
    cuvees = Cuvee.objects.filter(organization=organization)

    # Filtres
    from django.db.models import Q
    import uuid as _uuid

    search = (request.GET.get('search') or '').strip()
    if search:
        cuvees = cuvees.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    appellation_val = (request.GET.get('appellation') or '').strip()
    if appellation_val:
        try:
            _ = _uuid.UUID(appellation_val)
            cuvees = cuvees.filter(appellation_id=appellation_val)
        except Exception:
            cuvees = cuvees.filter(appellation__name__icontains=appellation_val)

    vintage_val = (request.GET.get('vintage') or '').strip()
    if vintage_val:
        try:
            _ = _uuid.UUID(vintage_val)
            cuvees = cuvees.filter(vintage_id=vintage_val)
        except Exception:
            # autoriser recherche rapide sur l'année
            try:
                year = int(vintage_val)
                cuvees = cuvees.filter(vintage__year=year)
            except Exception:
                pass

    is_active = (request.GET.get('is_active') or '').strip()
    if is_active:
        cuvees = cuvees.filter(is_active=is_active.lower() in ['true', '1', 'yes'])

    # Tri
    sort_by = (request.GET.get('sort') or 'name').strip()
    sort_order = (request.GET.get('order') or 'asc').strip()
    # Annoter lots_count pour tri
    cuvees = cuvees.annotate(lots_count=Count('lots'))
    sort_map = {
        'name': 'name',
        'appellation': 'appellation__name',
        'vintage': 'vintage__year',
        'uom': 'default_uom__code',
        'lots': 'lots_count',
        'status': 'is_active',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }
    order_field = sort_map.get(sort_by, 'name')
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    cuvees = cuvees.select_related('appellation', 'vintage', 'default_uom').order_by(order_field)

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(cuvees, 25)
    page_obj = paginator.get_page(page_number)

    # Rendus partiels
    from django.template.loader import render_to_string
    table_html = render_to_string(
        'catalogue/partials/cuvee_table_rows.html',
        {'cuvees': page_obj, 'page_obj': page_obj},
        request=request,
    )
    pagination_html = render_to_string(
        'catalogue/partials/cuvee_pagination.html',
        {'page_obj': page_obj},
        request=request,
    )

    total_count = Cuvee.objects.filter(organization=organization).count()
    filtered_count = cuvees.count()

    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': total_count,
            'filtered': filtered_count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
        }
    })
def products_dashboard(request):
    """
    Dashboard unifié pour la gestion des produits
    Même ergonomie que l'interface clients
    """
    organization = request.current_org
    
    # Statistiques rapides
    stats = {
        'cuvees_count': Cuvee.objects.filter(organization=organization, is_active=True).count(),
        'lots_count': Lot.objects.filter(organization=organization, is_active=True).count(),
        'sku_count': SKU.objects.filter(organization=organization).count(),
        'cepages_count': Cepage.objects.filter(organization=organization).count(),
        'parcelles_count': Parcelle.objects.filter(organization=organization).count(),
        'entrepots_count': Entrepot.objects.filter(organization=organization).count(),
    }
    
    # Données récentes pour aperçu
    recent_cuvees = Cuvee.objects.filter(organization=organization, is_active=True).order_by('-created_at')[:5]
    recent_lots = Lot.objects.filter(organization=organization, is_active=True).order_by('-created_at')[:5]
    
    # Alertes stock (optionnel)
    try:
        low_stock_skus = SKU.objects.filter(
            organization=organization
        ).annotate(
            total_stock=Sum('stockskubalance__qty_units')
        ).filter(
            total_stock__lt=10
        ).distinct()[:3]
    except Exception:
        # Si erreur de relation, on ignore les alertes stock pour l'instant
        low_stock_skus = []
    
    context = {
        'stats': stats,
        'recent_cuvees': recent_cuvees,
        'recent_lots': recent_lots,
        'low_stock_skus': low_stock_skus,
        'active_tab': 'dashboard'
    }
    
    return render(request, 'catalogue/products_unified.html', context)


@login_required
@require_membership()
def products_cuvees(request):
    """
    Gestion des cuvées avec filtres et recherche - INTERFACE ADMIN EXACTE
    """
    organization = request.current_org
    
    # Paramètres de recherche et filtrage (format admin)
    search_query = request.GET.get('q', '')  # 'q' comme dans admin
    appellation_filter = request.GET.get('appellation__id__exact', '')
    vintage_filter = request.GET.get('vintage__id__exact', '')
    is_active_filter = request.GET.get('is_active__exact', '')
    org_filter = request.GET.get('organization__id__exact', '')
    
    # Requête de base - TOUTES les cuvées pour admin
    cuvees = Cuvee.objects.filter(organization=organization)
    
    # Recherche (format admin)
    if search_query:
        cuvees = cuvees.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # Filtres admin exacts
    if appellation_filter:
        cuvees = cuvees.filter(appellation__id=appellation_filter)
    
    if vintage_filter:
        cuvees = cuvees.filter(vintage__id=vintage_filter)
        
    if is_active_filter:
        cuvees = cuvees.filter(is_active=(is_active_filter == '1'))
        
    if org_filter:
        cuvees = cuvees.filter(organization__id=org_filter)
    
    # Annotations pour statistiques
    cuvees = cuvees.select_related('appellation', 'vintage', 'default_uom', 'organization').annotate(
        lots_count=Count('lots')
    ).order_by('name')
    
    # Données pour filtres admin
    from apps.viticulture.models import Appellation, Vintage
    from apps.accounts.models import Organization
    
    appellations = Appellation.objects.filter(organization=organization).distinct()
    vintages = Vintage.objects.filter(organization=organization).distinct().order_by('-year')
    organizations = Organization.objects.all()  # Pour admin
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(cuvees, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'appellations': appellations,
        'vintages': vintages,
        'organizations': organizations,
        'active_tab': 'cuvees'
    }
    
    return render(request, 'catalogue/products_cuvees.html', context)


@login_required
@require_membership()
def products_lots(request):
    """
    Gestion des lots avec filtres et recherche - INTERFACE ADMIN EXACTE
    """
    organization = request.current_org
    
    # Paramètres de recherche et filtrage (format admin)
    search_query = request.GET.get('q', '')  # 'q' comme dans admin
    cuvee_filter = request.GET.get('cuvee__id__exact', '')
    status_filter = request.GET.get('status__exact', '')
    is_active_filter = request.GET.get('is_active__exact', '')
    org_filter = request.GET.get('organization__id__exact', '')
    
    # Requête de base - TOUS les lots pour admin
    lots = Lot.objects.filter(organization=organization)
    
    # Recherche (format admin)
    if search_query:
        lots = lots.filter(
            Q(code__icontains=search_query) |
            Q(cuvee__name__icontains=search_query)
        )
    
    # Filtres admin exacts
    if cuvee_filter:
        lots = lots.filter(cuvee__id=cuvee_filter)
    
    if status_filter:
        lots = lots.filter(status=status_filter)
        
    if is_active_filter:
        lots = lots.filter(is_active=(is_active_filter == '1'))
        
    if org_filter:
        lots = lots.filter(organization__id=org_filter)
    
    # Annotations pour stock
    lots = lots.select_related('cuvee', 'warehouse', 'organization').annotate(
        stock_total=Sum('stockvracbalance__qty_l')
    ).order_by('-created_at')
    
    # Données pour filtres admin
    from apps.accounts.models import Organization
    
    cuvees = Cuvee.objects.filter(organization=organization).distinct()
    organizations = Organization.objects.all()  # Pour admin
    warehouses = Warehouse.objects.filter(organization=organization).distinct()

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(lots, 25)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'cuvees': cuvees,
        'warehouses': warehouses,
        'organizations': organizations,
        'active_tab': 'lots'
    }
    
    return render(request, 'catalogue/products_lots.html', context)


@login_required
@require_membership()
def products_skus(request):
    """
    Gestion des SKU avec filtres et recherche - INTERFACE ADMIN EXACTE
    """
    organization = request.current_org
    
    # Paramètres de recherche et filtrage (format admin)
    search_query = request.GET.get('q', '')  # 'q' comme dans admin
    cuvee_filter = request.GET.get('cuvee__id__exact', '')
    uom_filter = request.GET.get('uom__id__exact', '')
    is_active_filter = request.GET.get('is_active__exact', '')
    org_filter = request.GET.get('organization__id__exact', '')
    
    # Requête de base - TOUS les SKUs pour admin
    skus = SKU.objects.filter(organization=organization)
    
    # Recherche (format admin)
    if search_query:
        skus = skus.filter(
            Q(label__icontains=search_query) |
            Q(code_barres__icontains=search_query) |
            Q(cuvee__name__icontains=search_query)
        )
    
    # Filtres admin exacts
    if cuvee_filter:
        skus = skus.filter(cuvee__id=cuvee_filter)
    
    if uom_filter:
        skus = skus.filter(uom__id=uom_filter)
        
    if is_active_filter:
        skus = skus.filter(is_active=(is_active_filter == '1'))
        
    if org_filter:
        skus = skus.filter(organization__id=org_filter)
    
    # Annotations pour stock
    try:
        skus = skus.select_related('cuvee', 'uom', 'organization').annotate(
            stock_total=Sum('stockskubalance__qty_units')
        ).order_by('label')
    except Exception:
        skus = skus.select_related('cuvee', 'uom', 'organization').order_by('label')
    
    # Données pour filtres admin
    from apps.viticulture.models import UnitOfMeasure
    from apps.accounts.models import Organization
    
    cuvees = Cuvee.objects.filter(organization=organization).distinct()
    uoms = UnitOfMeasure.objects.filter(organization=organization).distinct()
    organizations = Organization.objects.all()  # Pour admin
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(skus, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'cuvees': cuvees,
        'uoms': uoms,
        'organizations': organizations,
        'active_tab': 'skus'
    }
    
    return render(request, 'catalogue/products_skus.html', context)


@login_required
@require_membership()
def products_referentiels(request):
    """
    Gestion des référentiels - INTERFACE ADMIN EXACTE
    """
    organization = request.current_org
    
    # Données pour affichage admin exact
    from apps.referentiels.models import Cepage, Parcelle, Unite, Entrepot
    
    cepages = Cepage.objects.filter(organization=organization).order_by('nom')[:10]
    parcelles = Parcelle.objects.filter(organization=organization).order_by('nom')[:10]
    unites = Unite.objects.filter(organization=organization).order_by('nom')[:10]
    entrepots = Entrepot.objects.filter(organization=organization).order_by('nom')[:10]
    
    context = {
        'cepages': cepages,
        'parcelles': parcelles,
        'unites': unites,
        'entrepots': entrepots,
        'active_tab': 'referentiels'
    }
    
    return render(request, 'catalogue/products_referentiels.html', context)


@login_required
@require_membership()
def products_search_ajax(request):
    """
    Recherche AJAX pour l'interface unifiée
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    organization = request.current_org
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    if search_type in ['all', 'cuvees']:
        cuvees = Cuvee.objects.filter(
            organization=organization,
            is_active=True,
            name__icontains=query
        ).select_related('appellation', 'vintage')[:5]
        
        for cuvee in cuvees:
            subtitle = f"{cuvee.appellation.name if cuvee.appellation else 'Sans appellation'}"
            if cuvee.vintage:
                subtitle += f" - {cuvee.vintage.year}"
            results.append({
                'type': 'cuvee',
                'id': cuvee.id,
                'title': cuvee.name,
                'subtitle': subtitle,
                'url': f'/viticulture/cuvee/{cuvee.id}/change/'
            })
    
    if search_type in ['all', 'lots']:
        lots = Lot.objects.filter(
            organization=organization,
            is_active=True,
            code__icontains=query
        ).select_related('cuvee')[:5]
        
        for lot in lots:
            results.append({
                'type': 'lot',
                'id': lot.id,
                'title': lot.code,
                'subtitle': f"{lot.cuvee.name} - {lot.volume_l}L",
                'url': f'/catalogue/produits/lots/{lot.id}/'
            })
    
    return JsonResponse({'results': results})


@login_required
@require_membership()
@require_http_methods(["GET"])
def lots_search_ajax(request):
    """
    Recherche AJAX en temps réel pour les lots (même principe que clients)
    Retourne table_html + pagination_html + stats
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)

    organization = request.current_org
    lots = Lot.objects.filter(organization=organization)

    # Filtres
    from django.db.models import Q
    import uuid as _uuid

    search = (request.GET.get('search') or '').strip()
    if search:
        lots = lots.filter(
            Q(code__icontains=search) |
            Q(cuvee__name__icontains=search) |
            Q(warehouse__name__icontains=search)
        )

    cuvee_val = (request.GET.get('cuvee') or '').strip()
    if cuvee_val:
        try:
            _ = _uuid.UUID(cuvee_val)
            lots = lots.filter(cuvee_id=cuvee_val)
        except Exception:
            lots = lots.filter(cuvee__name__icontains=cuvee_val)

    status_val = (request.GET.get('status') or '').strip()
    if status_val:
        lots = lots.filter(status=status_val)

    warehouse_val = (request.GET.get('warehouse') or '').strip()
    if warehouse_val:
        try:
            _ = _uuid.UUID(warehouse_val)
            lots = lots.filter(warehouse_id=warehouse_val)
        except Exception:
            lots = lots.filter(warehouse__name__icontains=warehouse_val)

    is_active = (request.GET.get('is_active') or '').strip()
    if is_active:
        lots = lots.filter(is_active=is_active.lower() in ['true', '1', 'yes'])

    # Plages numériques (optionnelles)
    def _as_float(val):
        try:
            return float(val)
        except Exception:
            return None

    vmin = _as_float((request.GET.get('volume_min') or '').strip())
    if vmin is not None:
        lots = lots.filter(volume_l__gte=vmin)
    vmax = _as_float((request.GET.get('volume_max') or '').strip())
    if vmax is not None:
        lots = lots.filter(volume_l__lte=vmax)

    abv_min = _as_float((request.GET.get('alcohol_min') or '').strip())
    if abv_min is not None:
        lots = lots.filter(alcohol_pct__gte=abv_min)
    abv_max = _as_float((request.GET.get('alcohol_max') or '').strip())
    if abv_max is not None:
        lots = lots.filter(alcohol_pct__lte=abv_max)

    # Tri
    sort_by = (request.GET.get('sort') or 'created_at').strip()
    sort_order = (request.GET.get('order') or 'desc').strip()
    sort_map = {
        'code': 'code',
        'cuvee': 'cuvee__name',
        'volume_l': 'volume_l',
        'status': 'status',
        'warehouse': 'warehouse__name',
        'alcohol_pct': 'alcohol_pct',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }
    order_field = sort_map.get(sort_by, 'created_at')
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    lots = lots.select_related('cuvee', 'warehouse').order_by(order_field)

    # Pagination
    from django.core.paginator import Paginator
    page_number = request.GET.get('page', 1)
    paginator = Paginator(lots, 25)
    page_obj = paginator.get_page(page_number)

    # Rendus partiels
    from django.template.loader import render_to_string
    table_html = render_to_string(
        'catalogue/partials/lot_table_rows.html',
        {'lots': page_obj, 'page_obj': page_obj},
        request=request,
    )
    pagination_html = render_to_string(
        'catalogue/partials/lot_pagination.html',
        {'page_obj': page_obj},
        request=request,
    )

    total_count = Lot.objects.filter(organization=organization).count()
    filtered_count = lots.count()

    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': total_count,
            'filtered': filtered_count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
        }
    })


# ============================================================================
# VUES DE CRÉATION ET DÉTAIL
# ============================================================================

@login_required
@require_membership()
def cuvee_create(request):
    """
    Création d'une nouvelle cuvée
    Inspiré du modèle client pour la mise en page
    """
    organization = request.current_org
    
    # Données référentiels
    appellations = Appellation.objects.filter(organization=organization, is_active=True)
    vintages = Vintage.objects.filter(organization=organization, is_active=True)
    # Suggestions millésimes (10 dernières années + prochaine)
    current_year = dt_date.today().year
    suggested_vintages = [y for y in range(current_year + 1, current_year - 10, -1)]
    # Suggestions appellations (top existantes + baseline)
    baseline_appellations = [
        'Bordeaux AOC', 'Côtes du Rhône AOC', 'IGP Pays d\'Oc', 'VSIG',
    ]
    existing_names = list(appellations.values_list('name', flat=True)[:10])
    appellation_suggestions = list(dict.fromkeys(existing_names + baseline_appellations))
    # Unités affichées: SOURCER depuis referentiels.Unite (type volume) et mapper vers viticulture.UnitOfMeasure pour l'ID
    legacy_units = Unite.objects.filter(organization=organization, type_unite='volume').order_by('nom')
    uom_options = []
    for lu in legacy_units:
        code = (lu.symbole or (lu.nom or '')[:10]).strip().upper()[:10]
        if not code:
            continue
        # Trouver ou créer l'UoM viticulture correspondante par code (insensible à la casse)
        existing = UnitOfMeasure.objects.filter(organization=organization, code__iexact=code).first()
        if not existing:
            try:
                ratio = Decimal(str(lu.facteur_conversion)) if lu.facteur_conversion is not None else None
            except Exception:
                ratio = None
            # Si ratio invalide, ignorer l'unité car cuvée attend des unités de volume en L
            if ratio is None:
                continue
            existing = UnitOfMeasure.objects.create(
                organization=organization,
                code=code,
                name=(lu.nom or code)[:50],
                base_ratio_to_l=ratio,
                is_default=False,
            )
        # Libellé ergonomique: Nom (Symbole) — Type — Facteur
        try:
            type_label = lu.get_type_unite_display()
        except Exception:
            type_label = lu.type_unite
        facteur_txt = f"{lu.facteur_conversion}"
        label = f"{lu.nom} ({lu.symbole}) — {type_label} — {facteur_txt}"
        uom_options.append({
            'id': str(existing.id),
            'label': label,
            'code': existing.code or code,
            'is_default': bool(getattr(existing, 'is_default', False)),
        })
    # Trier: défaut d'abord, puis L, hL, puis libellé
    def _pref(c):
        c = (c or '').upper()
        if c == 'L':
            return 0
        if c in ('HL', 'H L'):
            return 1
        return 2
    uom_options.sort(key=lambda x: (
        0 if x['is_default'] else 1,
        _pref(x['code']),
        x['label'].lower()
    ))
    parcelles = VineyardPlot.objects.filter(organization=organization, is_active=True)
    cepages = GrapeVariety.objects.filter(organization=organization)

    # Pré-remplissage duplication
    initial = {}
    duplicate_from = request.GET.get('duplicate_from', '').strip()
    if duplicate_from:
        try:
            source = ViticultureCuvee.objects.get(id=duplicate_from, organization=organization)
            initial = {
                'name': source.name,
                'code': source.code,
                'appellation_name': source.appellation.name if source.appellation else '',
                'vintage_year': str(source.vintage.year) if source.vintage else '',
                'default_uom_id': str(source.default_uom.id) if source.default_uom else '',
                'is_active': source.is_active,
            }
        except ViticultureCuvee.DoesNotExist:
            initial = {}
    # Préselection UoM par défaut si non défini
    if not initial.get('default_uom_id'):
        default_uom = UnitOfMeasure.objects.filter(organization=organization, is_default=True).first()
        if default_uom:
            initial['default_uom_id'] = str(default_uom.id)
        else:
            # Fallback par code L/hL si présent côté viticulture
            uom_fallback = (
                UnitOfMeasure.objects.filter(organization=organization, code__iexact='L').first()
                or UnitOfMeasure.objects.filter(organization=organization, code__iexact='HL').first()
            )
            if uom_fallback:
                initial['default_uom_id'] = str(uom_fallback.id)
    # Déduire l'ID legacy (referentiels.Unite) pour pré-sélection front si possible
    try:
        if initial.get('default_uom_id'):
            uom_for_map = UnitOfMeasure.objects.filter(organization=organization, id=initial['default_uom_id']).first()
            if uom_for_map and uom_for_map.code:
                lu_match = Unite.objects.filter(organization=organization, symbole__iexact=uom_for_map.code).first()
                if lu_match:
                    initial['default_unit_id'] = str(lu_match.id)
    except Exception:
        pass
    # Préremplir millésime par l'année courante si vide
    if not initial.get('vintage_year'):
        initial['vintage_year'] = str(current_year)
    
    if request.method == 'POST':
        # Récupération des champs de base
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        appellation_name = (request.POST.get('appellation_name') or '').strip()
        vintage_year = (request.POST.get('vintage_year') or '').strip()
        default_uom_id = (request.POST.get('default_uom') or request.POST.get('default_unit') or None)
        is_active = bool(request.POST.get('is_active'))
        
        # Champs détail
        type_vin = request.POST.get('type_vin') or 'rouge'
        statut = request.POST.get('statut') or 'en_cours'
        volume_total_hl = request.POST.get('volume_total_hl') or None
        date_vendange_debut = request.POST.get('date_vendange_debut') or None
        date_vendange_fin = request.POST.get('date_vendange_fin') or None
        methode_vendange = request.POST.get('methode_vendange') or ''
        methode_vinification = request.POST.get('methode_vinification') or ''
        duree_elevage_mois = request.POST.get('duree_elevage_mois') or None
        contenant_elevage = request.POST.get('contenant_elevage') or ''
        degre_alcool_potentiel = request.POST.get('degre_alcool_potentiel') or None
        degre_alcool_final = request.POST.get('degre_alcool_final') or None
        sucres_residuels = request.POST.get('sucres_residuels') or None
        ph = request.POST.get('ph') or None
        acidite_totale = request.POST.get('acidite_totale') or None
        so2_libre = request.POST.get('so2_libre') or None
        so2_total = request.POST.get('so2_total') or None
        prix_revient_estime = request.POST.get('prix_revient_estime') or None
        certifications = request.POST.get('certifications', '').strip()
        notes_internes = request.POST.get('notes_internes', '').strip()
        notes_degustation = request.POST.get('notes_degustation', '').strip()
        etiquette_image = request.FILES.get('etiquette_image')
        
        # Validation minimale
        errors = []
        if not name:
            errors.append("Le nom de la cuvée est obligatoire.")
        if not vintage_year:
            errors.append("Le millésime est obligatoire.")
        if not default_uom_id:
            errors.append("L'unité par défaut est obligatoire.")
        
        if errors:
            for e in errors:
                messages.error(request, e)
            # Construire un initial cohérent avec le template pour pré-remplir
            initial_error = {
                'name': name,
                'code': code,
                'appellation_name': appellation_name,
                'vintage_year': vintage_year,
                'default_uom_id': default_uom_id or '',
                'default_unit_id': default_uom_id or '',
                'is_active': is_active,
                'type_vin': type_vin,
                'statut': statut,
            }
            context = {
                'page_title': 'Nouvelle Cuvée',
                'appellations': appellations,
                'vintages': vintages,
                'suggested_vintages': suggested_vintages,
                'appellation_suggestions': appellation_suggestions,
                'uom_options': uom_options,
                'parcelles': parcelles,
                'cepages': cepages,
                'type_vin_choices': CuveeDetail.TYPE_VIN_CHOICES,
                'statut_choices': CuveeDetail.STATUT_CHOICES,
                'vendange_choices': getattr(CuveeDetail, 'VENDANGE_CHOICES', []),
                'vinification_choices': getattr(CuveeDetail, 'VINIFICATION_CHOICES', []),
                'elevage_choices': getattr(CuveeDetail, 'ELEVAGE_CHOICES', []),
                'initial': initial_error,
                'breadcrumb_items': [
                    {'name': 'Produits', 'url': '/produits/cuvees/'},
                    {'name': 'Cuvées', 'url': '/produits/cuvees/'},
                    {'name': 'Nouvelle Cuvée', 'url': None}
                ]
            }
            return render(request, 'catalogue/cuvee_form.html', context)
        else:
            try:
                with transaction.atomic():
                    # Récupérer les FKs
                    # Millésime: get_or_create par année
                    vintage = None
                    if vintage_year:
                        try:
                            y = int(vintage_year)
                            vintage, _ = Vintage.objects.get_or_create(
                                organization=organization, year=y
                            )
                        except Exception:
                            vintage = None
                    # Appellation: optionnelle, get_or_create par nom
                    appellation = None
                    if appellation_name:
                        # Chercher par nom insensible à la casse
                        appellation = Appellation.objects.filter(
                            organization=organization, name__iexact=appellation_name
                        ).first()
                        if not appellation:
                            appellation = Appellation.objects.create(
                                organization=organization,
                                name=appellation_name,
                                type='autre',
                            )
                    # Résoudre l'unité: accepter un UUID de UnitOfMeasure ou un ID legacy de referentiels.Unite
                    uom = None
                    # Essayer comme UUID de UnitOfMeasure
                    try:
                        uom = UnitOfMeasure.objects.get(id=default_uom_id, organization=organization)
                    except Exception:
                        uom = None
                    # Si non trouvé, interpréter comme ID d'Unite (legacy)
                    if uom is None:
                        try:
                            rid = int(default_uom_id)
                            lu = Unite.objects.get(id=rid, organization=organization)
                            code = (lu.symbole or (lu.nom or '')[:10]).strip().upper()[:10]
                            ratio = Decimal(str(lu.facteur_conversion)) if lu.facteur_conversion is not None else None
                            if not code or ratio is None:
                                raise ValueError('Unité legacy invalide')
                            uom = UnitOfMeasure.objects.filter(organization=organization, code__iexact=code).first()
                            if not uom:
                                uom = UnitOfMeasure.objects.create(
                                    organization=organization,
                                    code=code,
                                    name=(lu.nom or code)[:50],
                                    base_ratio_to_l=ratio,
                                )
                        except Exception:
                            uom = None
                    if uom is None:
                        raise ValueError('Unité introuvable')
                    
                    # Créer la cuvée
                    cuvee = ViticultureCuvee.objects.create(
                        organization=organization,
                        name=name,
                        code=code,
                        default_uom=uom,
                        appellation=appellation,
                        vintage=vintage,
                        is_active=is_active,
                    )
                    
                    # Créer le détail
                    # Parse dates (format YYYY-MM-DD)
                    dv_debut = None
                    dv_fin = None
                    try:
                        dv_debut = dt_date.fromisoformat(date_vendange_debut) if date_vendange_debut else None
                    except Exception:
                        dv_debut = None
                    try:
                        dv_fin = dt_date.fromisoformat(date_vendange_fin) if date_vendange_fin else None
                    except Exception:
                        dv_fin = None

                    detail = CuveeDetail.objects.create(
                        organization=organization,
                        cuvee=cuvee,
                        type_vin=type_vin,
                        statut=statut,
                        volume_total_hl=Decimal(volume_total_hl) if volume_total_hl else None,
                        date_vendange_debut=dv_debut,
                        date_vendange_fin=dv_fin,
                        methode_vendange=methode_vendange,
                        methode_vinification=methode_vinification,
                        duree_elevage_mois=int(duree_elevage_mois) if duree_elevage_mois else None,
                        contenant_elevage=contenant_elevage,
                        degre_alcool_potentiel=Decimal(degre_alcool_potentiel) if degre_alcool_potentiel else None,
                        degre_alcool_final=Decimal(degre_alcool_final) if degre_alcool_final else None,
                        sucres_residuels=Decimal(sucres_residuels) if sucres_residuels else None,
                        ph=Decimal(ph) if ph else None,
                        acidite_totale=Decimal(acidite_totale) if acidite_totale else None,
                        so2_libre=Decimal(so2_libre) if so2_libre else None,
                        so2_total=Decimal(so2_total) if so2_total else None,
                        prix_revient_estime=Decimal(prix_revient_estime) if prix_revient_estime else None,
                        certifications=certifications,
                        notes_internes=notes_internes,
                        notes_degustation=notes_degustation,
                    )
                    
                    # Gérer l'image d'étiquette si fournie
                    if etiquette_image:
                        detail.etiquette_image = etiquette_image
                        detail.save(update_fields=['etiquette_image'])
                    
                    # Parcelles ratios (facultatif)
                    parcelle_ids = request.POST.getlist('parcelle_id[]')
                    parcelle_pcts = request.POST.getlist('parcelle_pct[]')
                    for pid, pct in zip(parcelle_ids, parcelle_pcts):
                        if pid and pct:
                            try:
                                p = VineyardPlot.objects.get(id=pid, organization=organization)
                                CuveeParcelleRatio.objects.create(
                                    cuvee_detail=detail,
                                    parcelle=p,
                                    pourcentage=Decimal(pct)
                                )
                            except VineyardPlot.DoesNotExist:
                                continue
                    
                    # Cépages ratios (facultatif)
                    cepage_ids = request.POST.getlist('cepage_id[]')
                    cepage_pcts = request.POST.getlist('cepage_pct[]')
                    for cid, pct in zip(cepage_ids, cepage_pcts):
                        if cid and pct:
                            try:
                                c = GrapeVariety.objects.get(id=cid, organization=organization)
                                CuveeCepageRatio.objects.create(
                                    cuvee_detail=detail,
                                    cepage=c,
                                    pourcentage=Decimal(pct)
                                )
                            except GrapeVariety.DoesNotExist:
                                continue
                messages.success(request, "Cuvée créée avec succès !")
                return redirect('catalogue:cuvee_detail', pk=cuvee.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la cuvée: {e}")

    context = {
        'page_title': 'Nouvelle Cuvée',
        'appellations': appellations,
        'vintages': vintages,
        'suggested_vintages': suggested_vintages,
        'appellation_suggestions': appellation_suggestions,
        'uom_options': uom_options,
        'parcelles': parcelles,
        'cepages': cepages,
        'type_vin_choices': CuveeDetail.TYPE_VIN_CHOICES,
        'statut_choices': CuveeDetail.STATUT_CHOICES,
        'vendange_choices': getattr(CuveeDetail, 'VENDANGE_CHOICES', []),
        'vinification_choices': getattr(CuveeDetail, 'VINIFICATION_CHOICES', []),
        'elevage_choices': getattr(CuveeDetail, 'ELEVAGE_CHOICES', []),
        'initial': initial,
        'breadcrumb_items': [
            {'name': 'Produits', 'url': '/produits/cuvees/'},
            {'name': 'Cuvées', 'url': '/produits/cuvees/'},
            {'name': 'Nouvelle Cuvée', 'url': None}
        ]
    }
    
    return render(request, 'catalogue/cuvee_form.html', context)


@login_required
@require_membership()
def cuvee_detail(request, pk):
    """
    Page de détail d'une cuvée avec fiche technique complète
    """
    cuvee = get_object_or_404(Cuvee, pk=pk, organization=request.user.get_active_membership().organization)
    
    # Récupérer ou créer les détails étendus
    try:
        from apps.viticulture.models import CuveeDetail
        cuvee_detail, created = CuveeDetail.objects.get_or_create(
            cuvee=cuvee,
            defaults={'organization': cuvee.organization}
        )
    except ImportError:
        cuvee_detail = None
    
    # Récupérer les lots associés (optimisé)
    lots = cuvee.lots.filter(is_active=True).select_related('warehouse')
    
    # Récupérer les SKUs associés (optimisé)
    skus = SKU.objects.filter(cuvee=cuvee, is_active=True).select_related('uom')
    
    # Liste des certifications pour le template (évite l'usage d'un filtre split custom)
    certifications_list = []
    if cuvee_detail and getattr(cuvee_detail, 'certifications', None):
        certifications_list = [c.strip() for c in cuvee_detail.certifications.split(',') if c.strip()]
    
    # Statistiques
    stats = {
        'total_lots': lots.count(),
        'volume_total': sum(lot.volume_l for lot in lots) if lots else 0,
        'total_skus': skus.count(),
    }
    
    context = {
        'cuvee': cuvee,
        'cuvee_detail': cuvee_detail,
        'lots': lots,
        'skus': skus,
        'stats': stats,
        'certifications_list': certifications_list,
        'page_title': f'Fiche Cuvée - {cuvee.name}',
        'breadcrumb_items': [
            {'name': 'Produits', 'url': '/produits/cuvees/'},
            {'name': 'Cuvées', 'url': '/produits/cuvees/'},
            {'name': cuvee.name, 'url': None},
        ]
    }
    
    return render(request, 'catalogue/cuvee_detail.html', context)

# Removed stray template artifact
@login_required
@require_membership()
def lot_create(request):
    """
    Création d'un nouveau lot
    """
    organization = request.current_org
    
    # Référentiels et listes
    cuvees = Cuvee.objects.filter(organization=organization, is_active=True)
    entrepots = Warehouse.objects.filter(organization=organization)
    lots = Lot.objects.filter(organization=organization, is_active=True)
    vintages = Vintage.objects.filter(organization=organization)
    # Suggestions pour millésimes et entrepôts
    current_year = dt_date.today().year
    suggested_vintages = [y for y in range(current_year + 1, current_year - 10, -1)]
    warehouse_suggestions = list(entrepots.values_list('name', flat=True)[:10])
    for baseline in ['Chai principal', 'Chai vieillissement', 'Bouteilles']:
        if baseline not in warehouse_suggestions:
            warehouse_suggestions.append(baseline)
    lot_status_choices = Lot._meta.get_field('status').choices
    container_type_choices = getattr(LotContainer, 'CONTAINER_CHOICES', [])
    valorisation_choices = getattr(LotDetail, 'VALORISATION_CHOICES', [])
    etat_microbio_choices = getattr(LotDetail, 'ETAT_MICROBIO_CHOICES', [])
    doc_type_choices = getattr(LotDocument, 'DOC_CHOICES', [])

    if request.method == 'POST':
        # Champs base Lot
        code = request.POST.get('code', '').strip()
        cuvee_id = request.POST.get('cuvee') or None
        warehouse_name = (request.POST.get('warehouse_name') or '').strip()
        volume_l = request.POST.get('volume_l') or None
        alcohol_pct = request.POST.get('alcohol_pct') or None
        status_posted = request.POST.get('status') or 'en_cours'
        is_active = bool(request.POST.get('is_active'))

        # Détail Lot
        vintage_majoritaire_year = (request.POST.get('millesime_majoritaire_year') or '').strip()
        emplacement_rangee = request.POST.get('emplacement_rangee', '').strip()
        emplacement_travee = request.POST.get('emplacement_travee', '').strip()
        emplacement_niveau = request.POST.get('emplacement_niveau', '').strip()
        temperature_cible_c = request.POST.get('temperature_cible_c') or None
        ouillage_requis = bool(request.POST.get('ouillage_requis'))
        ouillage_periodicite_jours = request.POST.get('ouillage_periodicite_jours') or None
        ouillage_dernier_controle = request.POST.get('ouillage_dernier_controle') or None

        volume_brut_l = request.POST.get('volume_brut_l') or None
        volume_net_l = request.POST.get('volume_net_l') or None
        titre_alcoolique_pct = request.POST.get('titre_alcoolique_pct') or None
        sr_g_l = request.POST.get('sr_g_l') or None
        ph = request.POST.get('ph') or None
        at_g_l = request.POST.get('at_g_l') or None
        so2_libre_mg_l = request.POST.get('so2_libre_mg_l') or None
        so2_total_mg_l = request.POST.get('so2_total_mg_l') or None

        etat_microbio = request.POST.get('etat_microbio') or ''
        clarification_technique = request.POST.get('clarification_technique', '').strip()
        clarification_details = request.POST.get('clarification_details', '').strip()
        elevage_type = request.POST.get('elevage_type', '').strip()
        elevage_duree_mois = request.POST.get('elevage_duree_mois') or None

        cout_matieres_eur = request.POST.get('cout_matieres_eur') or None
        cout_main_oeuvre_eur = request.POST.get('cout_main_oeuvre_eur') or None
        cout_unitaire_eur_l = request.POST.get('cout_unitaire_eur_l') or None
        valorisation_methode = request.POST.get('valorisation_methode') or 'cmp'

        destinations = request.POST.get('destinations', '').strip()
        drm_categorie = request.POST.get('drm_categorie', '').strip()
        certifications = request.POST.get('certifications', '').strip()
        etiquetage_mentions = request.POST.get('etiquetage_mentions', '').strip()
        etiquetage_allergenes = request.POST.get('etiquetage_allergenes', '').strip()
        observations = request.POST.get('observations', '').strip()

        # Validation minimale
        errors = []
        if not code:
            errors.append("Le code du lot est obligatoire.")
        if not cuvee_id:
            errors.append("La cuvée est obligatoire.")
        if not volume_l:
            errors.append("Le volume (L) est obligatoire.")

        # Vérifier status valide
        allowed_status = {s for s, _ in lot_status_choices}
        if status_posted not in allowed_status:
            status_posted = 'en_cours'

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                with transaction.atomic():
                    cuvee = Cuvee.objects.get(id=cuvee_id, organization=organization)
                    # Entrepôt: optionnel, get_or_create par nom saisi
                    warehouse = None
                    if warehouse_name:
                        warehouse = Warehouse.objects.filter(
                            organization=organization, name__iexact=warehouse_name
                        ).first()
                        if not warehouse:
                            warehouse = Warehouse.objects.create(
                                organization=organization,
                                name=warehouse_name,
                            )
                    lot = Lot.objects.create(
                        organization=organization,
                        code=code,
                        cuvee=cuvee,
                        warehouse=warehouse,
                        volume_l=Decimal(volume_l),
                        alcohol_pct=Decimal(alcohol_pct) if alcohol_pct else None,
                        status=status_posted,
                        is_active=is_active,
                    )

                    # Parse dates
                    ouillage_date = None
                    try:
                        ouillage_date = dt_date.fromisoformat(ouillage_dernier_controle) if ouillage_dernier_controle else None
                    except Exception:
                        ouillage_date = None

                    vintage_majoritaire = None
                    if vintage_majoritaire_year:
                        try:
                            vy = int(vintage_majoritaire_year)
                            vintage_majoritaire, _ = Vintage.objects.get_or_create(
                                organization=organization, year=vy
                            )
                        except Exception:
                            vintage_majoritaire = None

                    detail = LotDetail.objects.create(
                        organization=organization,
                        lot=lot,
                        millesime_majoritaire=vintage_majoritaire,
                        emplacement_rangee=emplacement_rangee,
                        emplacement_travee=emplacement_travee,
                        emplacement_niveau=emplacement_niveau,
                        temperature_cible_c=Decimal(temperature_cible_c) if temperature_cible_c else None,
                        ouillage_requis=ouillage_requis,
                        ouillage_periodicite_jours=int(ouillage_periodicite_jours) if ouillage_periodicite_jours else None,
                        ouillage_dernier_controle=ouillage_date,
                        volume_brut_l=Decimal(volume_brut_l) if volume_brut_l else None,
                        volume_net_l=Decimal(volume_net_l) if volume_net_l else None,
                        titre_alcoolique_pct=Decimal(titre_alcoolique_pct) if titre_alcoolique_pct else None,
                        sr_g_l=Decimal(sr_g_l) if sr_g_l else None,
                        ph=Decimal(ph) if ph else None,
                        at_g_l=Decimal(at_g_l) if at_g_l else None,
                        so2_libre_mg_l=Decimal(so2_libre_mg_l) if so2_libre_mg_l else None,
                        so2_total_mg_l=Decimal(so2_total_mg_l) if so2_total_mg_l else None,
                        etat_microbio=etat_microbio,
                        clarification_technique=clarification_technique,
                        clarification_details=clarification_details,
                        elevage_type=elevage_type,
                        elevage_duree_mois=int(elevage_duree_mois) if elevage_duree_mois else None,
                        cout_matieres_eur=Decimal(cout_matieres_eur) if cout_matieres_eur else None,
                        cout_main_oeuvre_eur=Decimal(cout_main_oeuvre_eur) if cout_main_oeuvre_eur else None,
                        cout_unitaire_eur_l=Decimal(cout_unitaire_eur_l) if cout_unitaire_eur_l else None,
                        valorisation_methode=valorisation_methode,
                        destinations=destinations,
                        drm_categorie=drm_categorie,
                        certifications=certifications,
                        etiquetage_mentions=etiquetage_mentions,
                        etiquetage_allergenes=etiquetage_allergenes,
                        observations=observations,
                    )

                    # Contenants
                    c_types = request.POST.getlist('container_type[]')
                    c_caps = request.POST.getlist('container_capacite[]')
                    c_vols = request.POST.getlist('container_volume[]')
                    c_ids = request.POST.getlist('container_identifiant[]')
                    total_container_vol = Decimal('0')
                    for t, cap, vol, ident in zip(c_types, c_caps, c_vols, c_ids):
                        if t and vol:
                            lc = LotContainer.objects.create(
                                organization=organization,
                                lot=lot,
                                type=t,
                                capacite_l=Decimal(cap) if cap else Decimal('0'),
                                volume_occupe_l=Decimal(vol),
                                identifiant=ident.strip() if ident else '',
                            )
                            total_container_vol += lc.volume_occupe_l
                    # Si contenants remplis, aligner volumes
                    if total_container_vol > 0:
                        lot.volume_l = total_container_vol
                        lot.save(update_fields=['volume_l'])
                        if not detail.volume_net_l:
                            detail.volume_net_l = total_container_vol
                            detail.save(update_fields=['volume_net_l'])

                    # Sources cuvées
                    s_cuvee_ids = request.POST.getlist('source_cuvee_id[]')
                    s_cuvee_vols = request.POST.getlist('source_cuvee_volume[]')
                    s_cuvee_pcts = request.POST.getlist('source_cuvee_pct[]')
                    for sid, svol, spct in zip(s_cuvee_ids, s_cuvee_vols, s_cuvee_pcts):
                        if sid:
                            try:
                                src = Cuvee.objects.get(id=sid, organization=organization)
                                LotSourceCuvee.objects.create(
                                    lot=lot,
                                    cuvee=src,
                                    volume_l=Decimal(svol) if svol else None,
                                    pourcentage=Decimal(spct) if spct else None,
                                )
                            except Cuvee.DoesNotExist:
                                continue

                    # Sources lots
                    s_lot_ids = request.POST.getlist('source_lot_id[]')
                    s_lot_vols = request.POST.getlist('source_lot_volume[]')
                    s_lot_pcts = request.POST.getlist('source_lot_pct[]')
                    for lid, lvol, lpct in zip(s_lot_ids, s_lot_vols, s_lot_pcts):
                        if lid:
                            try:
                                src_lot = Lot.objects.get(id=lid, organization=organization)
                                LotSourceLot.objects.create(
                                    lot=lot,
                                    source_lot=src_lot,
                                    volume_l=Decimal(lvol) if lvol else None,
                                    pourcentage=Decimal(lpct) if lpct else None,
                                )
                            except Lot.DoesNotExist:
                                continue

                    # Documents (pièces jointes)
                    doc_files = request.FILES.getlist('doc_file[]')
                    doc_types = request.POST.getlist('doc_type[]')
                    doc_descs = request.POST.getlist('doc_desc[]')
                    for f, dt, dd in zip(doc_files, doc_types, doc_descs):
                        if f:
                            LotDocument.objects.create(
                                organization=organization,
                                lot=lot,
                                document=f,
                                type=dt or 'autre',
                                description=(dd or '').strip(),
                            )

                messages.success(request, "Lot créé avec succès !")
                return redirect('catalogue:lot_detail', pk=lot.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du lot: {e}")

    context = {
        'page_title': 'Nouveau Lot',
        'cuvees': cuvees,
        'entrepots': entrepots,
        'lots': lots,
        'vintages': vintages,
        'suggested_vintages': suggested_vintages,
        'warehouse_suggestions': warehouse_suggestions,
        'lot_status_choices': lot_status_choices,
        'container_type_choices': container_type_choices,
        'valorisation_choices': valorisation_choices,
        'etat_microbio_choices': etat_microbio_choices,
        'doc_type_choices': doc_type_choices,
        'breadcrumb_items': [
            {'name': 'Dashboard Produits', 'url': reverse('catalogue:products_dashboard')},
            {'name': 'Lots', 'url': reverse('catalogue:products_lots')},
            {'name': 'Nouveau Lot', 'url': None}
        ]
    }
    
    return render(request, 'catalogue/lot_form.html', context)


@login_required
@require_membership()
def lot_detail(request, pk):
    """
    Détail d'un lot
    """
    organization = request.current_org
    lot = get_object_or_404(Lot, pk=pk, organization=organization)
    # Détails étendus
    lot_detail = None
    containers = []
    sources_cuvees = []
    sources_lots = []
    documents = []
    try:
        lot_detail = LotDetail.objects.get(lot=lot)
        containers = list(lot.contenants.all())
        sources_cuvees = list(lot.sources_cuvees.select_related('cuvee'))
        sources_lots = list(lot.sources_lots.select_related('source_lot'))
        documents = list(lot.documents.all())
    except Exception:
        lot_detail = None

    context = {
        'lot': lot,
        'lot_detail': lot_detail,
        'containers': containers,
        'sources_cuvees': sources_cuvees,
        'sources_lots': sources_lots,
        'documents': documents,
        'page_title': f'Lot {lot.code}',
        'breadcrumb_items': [
            {'name': 'Dashboard Produits', 'url': reverse('catalogue:products_dashboard')},
            {'name': 'Lots', 'url': reverse('catalogue:products_lots')},
            {'name': lot.code, 'url': None}
        ]
    }
    
    return render(request, 'catalogue/lot_detail.html', context)


@login_required
@require_membership()
def sku_create(request):
    """
    Création d'un nouveau produit fini
    """
    organization = request.current_org
    
    if request.method == 'POST':
        def _clean_id(val: str) -> str:
            return (val or '').replace('\xa0', '').strip()

        label = (request.POST.get('label') or '').strip()
        cuvee_id = _clean_id(request.POST.get('cuvee'))
        uom_id = _clean_id(request.POST.get('uom'))
        volume_str = (request.POST.get('volume_by_uom_to_l') or '').replace('\xa0', '').replace(',', '.').strip()
        ean_code = (request.POST.get('ean_code') or '').strip()
        is_active = bool(request.POST.get('is_active'))

        errors = []
        if not label:
            errors.append("L'étiquette est obligatoire.")
        if not cuvee_id:
            errors.append("La cuvée est obligatoire.")
        if not uom_id:
            errors.append("L'unité de mesure est obligatoire.")
        try:
            volume = Decimal(volume_str) if volume_str else None
        except Exception:
            volume = None
        if not volume or volume <= 0:
            errors.append("Le volume par unité (L) doit être > 0.")

        cuvee = None
        uom = None
        # Résolution cuvée (UUID only)
        if cuvee_id:
            cuvee_uuid = None
            try:
                cuvee_uuid = _uuid.UUID(cuvee_id)
            except Exception:
                cuvee_uuid = None
            if cuvee_uuid:
                cuvee = Cuvee.objects.filter(id=cuvee_uuid, organization=organization).first()
            if not cuvee:
                errors.append("Cuvée introuvable.")

        # Résolution UoM: accepter UUID (viticulture.UnitOfMeasure) ou fallback ID entier (referentiels.Unite)
        if uom_id:
            uom_uuid = None
            try:
                uom_uuid = _uuid.UUID(uom_id)
            except Exception:
                uom_uuid = None
            if uom_uuid:
                uom = UnitOfMeasure.objects.filter(id=uom_uuid, organization=organization).first()
            if not uom:
                # Fallback legacy referentiels.Unite (int PK)
                try:
                    legacy_id = int(uom_id)
                    legacy_u = Unite.objects.filter(id=legacy_id, organization=organization).first()
                except Exception:
                    legacy_u = None
                if legacy_u:
                    code = (getattr(legacy_u, 'symbole', None) or (getattr(legacy_u, 'nom', '') or '')[:10]).strip().upper()[:10]
                    if not code:
                        code = 'U'
                    uom = UnitOfMeasure.objects.filter(organization=organization, code__iexact=code).first()
                    if not uom:
                        # Créer l'UoM si absente: utiliser facteur_conversion legacy si dispo, sinon volume, sinon 1.0
                        try:
                            fx_legacy = getattr(legacy_u, 'facteur_conversion', None)
                            ratio = Decimal(str(fx_legacy)) if fx_legacy is not None else None
                        except Exception:
                            ratio = None
                        if ratio is None:
                            ratio = volume if (volume and volume > 0) else Decimal('1.0')
                        uom = UnitOfMeasure.objects.create(
                            organization=organization,
                            code=code,
                            name=(getattr(legacy_u, 'nom', '') or code)[:50],
                            base_ratio_to_l=ratio,
                            is_default=False,
                        )
                if not uom:
                    errors.append("Unité de mesure introuvable.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                sku = SKU.objects.create(
                    organization=organization,
                    cuvee=cuvee,
                    uom=uom,
                    volume_by_uom_to_l=volume,
                    label=label,
                    code_barres=ean_code,
                    is_active=is_active,
                )
                messages.success(request, "Produit fini créé avec succès !")
                return redirect('catalogue:sku_detail', pk=sku.id)
            except Exception as e:
                messages.error(request, str(e))
    
    # Données pour le formulaire
    cuvees = Cuvee.objects.filter(organization=organization, is_active=True)
    uoms = UnitOfMeasure.objects.filter(organization=organization, is_active=True)
    
    context = {
        'page_title': 'Nouveau produit fini',
        'cuvees': cuvees,
        'uoms': uoms,
        'breadcrumb_items': [
            {'name': 'Dashboard Produits', 'url': reverse('catalogue:products_dashboard')},
            {'name': 'Produits finis', 'url': reverse('catalogue:products_skus')},
            {'name': 'Nouveau produit fini', 'url': None}
        ]
    }
    
    return render(request, 'catalogue/sku_form.html', context)


@login_required
@require_membership()
def sku_detail(request, pk):
    """
    Détail d'un produit fini
    """
    organization = request.current_org
    sku = get_object_or_404(SKU, pk=pk, organization=organization)
    
    context = {
        'sku': sku,
        'page_title': f'Produit fini {sku.label}',
        'breadcrumb_items': [
            {'name': 'Dashboard Produits', 'url': reverse('catalogue:products_dashboard')},
            {'name': 'Produits finis', 'url': reverse('catalogue:products_skus')},
            {'name': sku.label, 'url': None}
        ]
    }
    
    return render(request, 'catalogue/sku_detail.html', context)
