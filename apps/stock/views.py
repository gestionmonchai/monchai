from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction

from apps.accounts.decorators import require_membership
from apps.viticulture.models import Lot, Warehouse
from .models import StockTransfer

@login_required
@require_membership(role_min='read_only')
def mouvements_view(request):
    """
    Journal des mouvements (placeholder): affiche les 50 derniers mouvements vrac et SKU
    /stocks/mouvements/
    """
    organization = request.current_org
    from .models import StockVracMove, StockSKUMove

    vrac = list(StockVracMove.objects.filter(organization=organization).select_related('lot', 'src_warehouse', 'dst_warehouse').order_by('-created_at')[:50])
    sku = list(StockSKUMove.objects.filter(organization=organization).select_related('sku', 'src_warehouse', 'dst_warehouse').order_by('-created_at')[:50])

    context = {
        'page_title': 'Mouvements de stock',
        'vrac_moves': vrac,
        'sku_moves': sku,
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Mouvements', 'url': None},
        ]
    }
    return render(request, 'stock/mouvements.html', context)


@login_required
@require_membership(role_min='read_only')
def inventaire_list(request):
    """
    Liste des inventaires (placeholder)
    /stocks/inventaires/
    """
    context = {
        'page_title': 'Inventaires',
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Inventaires', 'url': None},
        ]
    }
    return render(request, 'stock/inventaires_list.html', context)


@login_required
@require_membership(role_min='editor')
def inventaire_new(request):
    """
    Démarrer un nouvel inventaire (placeholder)
    /stocks/inventaires/nouveau/
    """
    warehouses = Warehouse.objects.filter(organization=request.current_org).order_by('name')
    context = {
        'page_title': 'Nouvel inventaire',
        'warehouses': warehouses,
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Inventaires', 'url': '/stocks/inventaires/'},
            {'name': 'Nouveau', 'url': None},
        ]
    }
    return render(request, 'stock/inventaire_form.html', context)


@login_required
@require_membership(role_min='read_only')
def inventaire_detail(request, pk):
    """
    Détail d'inventaire (placeholder)
    /stocks/inventaires/<id>/
    """
    context = {
        'page_title': 'Détail inventaire',
        'inventaire_id': pk,
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Inventaires', 'url': '/stocks/inventaires/'},
            {'name': str(pk), 'url': None},
        ]
    }
    return render(request, 'stock/inventaire_detail.html', context)


@login_required
@require_membership(role_min='read_only')
def entrepots_list(request):
    """
    Liste des entrepôts
    /stocks/entrepots/
    """
    warehouses = Warehouse.objects.filter(organization=request.current_org).order_by('name')
    context = {
        'page_title': 'Entrepôts',
        'warehouses': warehouses,
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Entrepôts', 'url': None},
        ]
    }
    return render(request, 'stock/entrepots.html', context)


@login_required
@require_membership(role_min='read_only')
def emplacements_list(request):
    """
    Emplacements (placeholder)
    /stocks/emplacements/
    """
    context = {
        'page_title': 'Emplacements',
        'breadcrumb_items': [
            {'name': 'Stocks', 'url': '/stocks/'},
            {'name': 'Emplacements', 'url': None},
        ]
    }
    return render(request, 'stock/emplacements.html', context)


@login_required
@require_membership(role_min='read_only')
def stock_dashboard(request):
    """
    Dashboard principal des stocks
    """
    organization = request.current_org
    
    # Résumé global des stocks
    stock_summary = StockService.get_organization_stock_summary(organization)
    
    context = {
        'stock_summary': stock_summary,
        'page_title': 'Dashboard Stocks',
    }
    
    return render(request, 'stock/dashboard.html', context)


@login_required
@require_membership(role_min='read_only')
def transferts_list(request):
    """
    Liste des transferts avec filtres - Roadmap 32
    """
    organization = request.current_org
    
    # Filtres
    lot_id = request.GET.get('lot')
    warehouse_id = request.GET.get('warehouse')
    
    lot = None
    warehouse = None
    
    if lot_id:
        try:
            lot = Lot.objects.get(id=lot_id, organization=organization)
        except (Lot.DoesNotExist, ValueError):
            pass
    
    if warehouse_id:
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, organization=organization)
        except (Warehouse.DoesNotExist, ValueError):
            pass
    
    # Historique des transferts
    transfers = StockService.get_transfer_history(
        organization=organization,
        lot=lot,
        warehouse=warehouse,
        limit=100
    )
    
    # Données pour les filtres
    lots = Lot.objects.filter(organization=organization).order_by('code')
    warehouses = Warehouse.objects.filter(
        organization=organization, 
        is_active=True
    ).order_by('name')
    
    context = {
        'transfers': transfers,
        'lots': lots,
        'warehouses': warehouses,
        'selected_lot': lot,
        'selected_warehouse': warehouse,
        'page_title': 'Transferts entre entrepôts',
    }
    
    return render(request, 'stock/transferts_list.html', context)


@login_required
@require_membership(role_min='editor')
def transfert_create(request):
    """
    Formulaire de création de transfert - Roadmap 32
    """
    organization = request.current_org
    
    if request.method == 'POST':
        try:
            # Récupération des données
            lot_id = request.POST.get('lot')
            from_warehouse_id = request.POST.get('from_warehouse')
            to_warehouse_id = request.POST.get('to_warehouse')
            volume_l = request.POST.get('volume_l')
            notes = request.POST.get('notes', '')
            
            # Validation des données
            if not all([lot_id, from_warehouse_id, to_warehouse_id, volume_l]):
                raise ValidationError("Tous les champs obligatoires doivent être remplis")
            
            # Récupération des objets
            lot = get_object_or_404(Lot, id=lot_id, organization=organization)
            from_warehouse = get_object_or_404(Warehouse, id=from_warehouse_id, organization=organization)
            to_warehouse = get_object_or_404(Warehouse, id=to_warehouse_id, organization=organization)
            
            volume_l = float(volume_l)
            
            # Validation métier
            validation_errors = StockService.validate_transfer_request(
                organization, lot, from_warehouse, to_warehouse, volume_l
            )
            
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                raise ValidationError("Erreurs de validation")
            
            # Génération token client pour idempotence
            client_token = f"web_{request.user.id}_{uuid.uuid4().hex[:8]}"
            
            # Création du transfert
            transfer, created = StockTransfer.create_transfer(
                organization=organization,
                lot=lot,
                from_warehouse=from_warehouse,
                to_warehouse=to_warehouse,
                volume_l=volume_l,
                user=request.user,
                client_token=client_token,
                notes=notes
            )
            
            if created:
                messages.success(
                    request, 
                    f"Transfert créé avec succès: {volume_l}L de {lot.code} "
                    f"de {from_warehouse.name} vers {to_warehouse.name}"
                )
            else:
                messages.info(request, "Ce transfert a déjà été effectué")
            
            return redirect('stock:transferts_list')
            
        except ValidationError as e:
            # Les erreurs individuelles ont déjà été ajoutées via messages.error
            pass
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du transfert: {str(e)}")
    
    # GET - Affichage du formulaire
    lots_with_stock = []
    lots = Lot.objects.filter(organization=organization).select_related('cuvee')
    
    for lot in lots:
        balances = StockService.get_lot_balances_by_warehouse(organization, lot)
        if balances:  # Seulement les lots avec du stock
            lots_with_stock.append({
                'lot': lot,
                'balances': balances,
                'total_volume': sum(balances.values())
            })
    
    warehouses = Warehouse.objects.filter(organization=organization).order_by('name')
    
    context = {
        'lots_with_stock': lots_with_stock,
        'warehouses': warehouses,
        'page_title': 'Nouveau transfert',
    }
    
    return render(request, 'stock/transfert_create.html', context)


@login_required
@require_membership(role_min='read_only')
def inventaire_view(request):
    """
    Vue principale de l'inventaire - Roadmap 33
    /stocks/inventaire/
    """
    organization = request.current_org
    
    # Récupérer les données pour les filtres
    from apps.viticulture.models import Cuvee, Warehouse, Vintage
    
    cuvees = Cuvee.objects.filter(organization=organization).order_by('name')
    warehouses = Warehouse.objects.filter(organization=organization).order_by('name')
    vintages = Vintage.objects.filter(organization=organization).order_by('-year')
    
    context = {
        'page_title': 'Inventaire des stocks',
        'cuvees': cuvees,
        'warehouses': warehouses,
        'vintages': vintages,
    }
    
    return render(request, 'stock/inventaire.html', context)


@login_required
@require_membership(role_min='editor')
def inventaire_counting_view(request, warehouse_id):
    """
    Vue pour le comptage physique d'un entrepôt - Roadmap 33
    /stocks/inventaire/counting/<warehouse_id>/
    """
    organization = request.current_org
    
    try:
        from apps.viticulture.models import Warehouse
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, organization=organization)
        
        context = {
            'page_title': f'Comptage physique - {warehouse.name}',
            'warehouse': warehouse,
        }
        
        return render(request, 'stock/inventaire_counting.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement: {str(e)}")
        return redirect('stock:inventaire_view')


@login_required
@require_membership(role_min='read_only')
def alertes_view(request):
    """
    Vue principale des alertes de stock - Roadmap 34
    /stocks/alertes/
    """
    organization = request.current_org
    
    # Récupérer les données pour les filtres
    from apps.viticulture.models import Cuvee, Warehouse
    from .services import StockAlertService
    
    cuvees = Cuvee.objects.filter(organization=organization).order_by('name')
    warehouses = Warehouse.objects.filter(organization=organization).order_by('name')
    
    # Paramètres de filtrage
    filters = {}
    if request.GET.get('status'):
        filters['status'] = request.GET.get('status')
    if request.GET.get('cuvee_id'):
        filters['cuvee_id'] = request.GET.get('cuvee_id')
    if request.GET.get('warehouse_id'):
        filters['warehouse_id'] = request.GET.get('warehouse_id')
    if request.GET.get('criticality'):
        filters['criticality'] = request.GET.get('criticality')
    
    # Tri
    sort_by = request.GET.get('sort', 'criticality')
    
    # Récupérer les alertes
    alerts = StockAlertService.get_alerts_list(organization, filters, sort_by)
    
    # Statistiques
    active_count = StockAlertService.get_active_alerts_count(organization)
    
    context = {
        'page_title': 'Alertes de stock',
        'alerts': alerts,
        'active_count': active_count,
        'cuvees': cuvees,
        'warehouses': warehouses,
        'current_filters': filters,
        'current_sort': sort_by,
    }
    
    return render(request, 'stock/alertes.html', context)


@login_required
@require_membership(role_min='read_only')
def seuils_view(request):
    """
    Vue de paramétrage des seuils de stock - Roadmap 34
    /stocks/seuils/
    """
    organization = request.current_org
    
    from .models import StockThreshold
    from apps.viticulture.models import Cuvee, Warehouse
    
    # Récupérer les seuils existants
    thresholds = StockThreshold.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('created_by').order_by('scope', 'threshold_l')
    
    # Données pour les formulaires
    cuvees = Cuvee.objects.filter(organization=organization).order_by('name')
    warehouses = Warehouse.objects.filter(organization=organization).order_by('name')
    
    context = {
        'page_title': 'Seuils de stock',
        'thresholds': thresholds,
        'cuvees': cuvees,
        'warehouses': warehouses,
    }
    
    return render(request, 'stock/seuils.html', context)
