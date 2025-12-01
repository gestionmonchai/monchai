"""
Vues pour le catalogue et la gestion des lots
Roadmap Cut #4 : Catalogue & lots
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Min, Max
from django.db import models

from apps.accounts.decorators import require_membership
from apps.viticulture.models import Cuvee
from .models import Lot, MouvementLot
from .forms import LotForm, MouvementLotForm


# ===== CATALOGUE =====

@require_membership(role_min='read_only')
def catalogue_home(request):
    """
    Page d'accueil du catalogue - Roadmap item 19
    Grille des cuvées avec recherche avancée et tri
    """
    organization = request.current_org
    cuvees = Cuvee.objects.filter(organization=organization).select_related().prefetch_related('cepages', 'lots')
    
    # Recherche avancée
    search = request.GET.get('search', '')
    if search:
        cuvees = cuvees.filter(
            Q(nom__icontains=search) |
            Q(appellation__icontains=search) |
            Q(description__icontains=search) |
            Q(notes_degustation__icontains=search) |
            Q(cepages__nom__icontains=search)
        ).distinct()
    
    # Filtres avancés
    couleur = request.GET.get('couleur', '')
    if couleur:
        cuvees = cuvees.filter(couleur=couleur)
    
    classification = request.GET.get('classification', '')
    if classification:
        cuvees = cuvees.filter(classification=classification)
    
    # Filtre par degré d'alcool
    degre_min = request.GET.get('degre_min', '')
    degre_max = request.GET.get('degre_max', '')
    if degre_min:
        try:
            cuvees = cuvees.filter(degre_alcool__gte=float(degre_min))
        except ValueError:
            pass
    if degre_max:
        try:
            cuvees = cuvees.filter(degre_alcool__lte=float(degre_max))
        except ValueError:
            pass
    
    # Filtre par appellation
    appellation = request.GET.get('appellation', '')
    if appellation:
        cuvees = cuvees.filter(appellation__icontains=appellation)
    
    # Filtre par cépage
    cepage = request.GET.get('cepage', '')
    if cepage:
        cuvees = cuvees.filter(cepages__nom__icontains=cepage)
    
    # Filtre par présence de lots
    has_lots = request.GET.get('has_lots', '')
    if has_lots == 'yes':
        cuvees = cuvees.filter(lots__isnull=False).distinct()
    elif has_lots == 'no':
        cuvees = cuvees.filter(lots__isnull=True)
    
    # Tri intelligent
    sort_by = request.GET.get('sort', 'nom')
    sort_order = request.GET.get('order', '')
    
    # Configuration des champs de tri avec ordre par défaut
    sort_config = {
        'nom': {'field': 'nom', 'default_order': 'asc', 'type': 'text'},
        'couleur': {'field': 'couleur', 'default_order': 'asc', 'type': 'text'},
        'classification': {'field': 'classification', 'default_order': 'asc', 'type': 'text'},
        'appellation': {'field': 'appellation', 'default_order': 'asc', 'type': 'text'},
        'degre_alcool': {'field': 'degre_alcool', 'default_order': 'desc', 'type': 'number'},
        'created_at': {'field': 'created_at', 'default_order': 'desc', 'type': 'date'},
        'updated_at': {'field': 'updated_at', 'default_order': 'desc', 'type': 'date'},
    }
    
    if sort_by in sort_config:
        config = sort_config[sort_by]
        # Si pas d'ordre spécifié, utiliser l'ordre par défaut
        if not sort_order:
            sort_order = config['default_order']
        
        order_field = config['field']
        if sort_order == 'desc':
            order_field = f'-{order_field}'
        cuvees = cuvees.order_by(order_field)
    else:
        cuvees = cuvees.order_by('nom')
        sort_by = 'nom'
        sort_order = 'asc'
    
    # Pagination
    paginator = Paginator(cuvees, 12)  # 12 cartes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour les filtres
    all_cuvees = Cuvee.objects.filter(organization=organization)
    stats = {
        'total': all_cuvees.count(),
        'filtered': cuvees.count(),
        'couleurs': all_cuvees.values_list('couleur', flat=True).distinct().order_by('couleur'),
        'classifications': all_cuvees.values_list('classification', flat=True).distinct().order_by('classification'),
        'appellations': all_cuvees.exclude(appellation__isnull=True).exclude(appellation='').values_list('appellation', flat=True).distinct().order_by('appellation')[:20],
        'cepages': organization.cepages.values_list('nom', flat=True).distinct().order_by('nom')[:20],
        'degre_range': {
            'min': all_cuvees.aggregate(min_degre=models.Min('degre_alcool'))['min_degre'] or 0,
            'max': all_cuvees.aggregate(max_degre=models.Max('degre_alcool'))['max_degre'] or 20,
        }
    }
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'couleur_filter': couleur,
        'classification_filter': classification,
        'degre_min_filter': degre_min,
        'degre_max_filter': degre_max,
        'appellation_filter': appellation,
        'cepage_filter': cepage,
        'has_lots_filter': has_lots,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'stats': stats,
        'organization': organization,
        'page_title': 'Catalogue'
    }
    
    return render(request, 'catalogue/catalogue_home.html', context)


@require_membership(role_min='read_only')
def catalogue_cuvee_detail(request, pk):
    """
    Fiche détaillée d'une cuvée - Roadmap 26
    Page de détail avec infos générales, médias et liens vers lots/SKUs
    """
    organization = request.current_org
    cuvee = get_object_or_404(
        Cuvee.objects.select_related('appellation', 'vintage', 'default_uom'),
        pk=pk, 
        organization=organization,
        is_active=True
    )
    
    # Statistiques des lots (TODO: intégrer avec le système de lots)
    # lots = Lot.objects.filter(cuvee=cuvee).select_related('entrepot', 'unite_volume')
    lots_stats = {
        'total': 0,  # À implémenter avec le modèle Lot
        'en_stock': 0,
        'en_production': 0,
        'vendus': 0,
    }
    
    # Médias (TODO: intégrer avec le système de médias)
    media_info = {
        'main_image': None,  # À implémenter avec le système de médias
        'gallery': []
    }
    
    # Permissions utilisateur
    membership = request.user.get_active_membership()
    user_permissions = {
        'can_edit': membership and membership.role in ['admin', 'editor'],
        'can_delete': membership and membership.role == 'admin'
    }
    
    context = {
        'cuvee': cuvee,
        'lots_stats': lots_stats,
        'media_info': media_info,
        'user_permissions': user_permissions,
        'organization': organization,
        'page_title': f'Catalogue : {cuvee.name}'
    }
    
    return render(request, 'catalogue/cuvee_detail.html', context)


# ===== LOTS =====

@require_membership(role_min='read_only')
def lot_list(request):
    """
    Liste des lots - Roadmap item 21
    Liste lots avec recherche avancée et tri
    """
    organization = request.current_org
    lots = Lot.objects.filter(organization=organization).select_related('cuvee', 'entrepot', 'unite_volume')
    
    # Recherche avancée
    search = request.GET.get('search', '')
    if search:
        lots = lots.filter(
            Q(numero_lot__icontains=search) |
            Q(cuvee__nom__icontains=search) |
            Q(cuvee__appellation__icontains=search) |
            Q(entrepot__nom__icontains=search) |
            Q(notes__icontains=search)
        )
    
    # Filtres avancés
    statut = request.GET.get('statut', '')
    if statut:
        lots = lots.filter(statut=statut)
    
    millesime = request.GET.get('millesime', '')
    if millesime:
        lots = lots.filter(millesime=millesime)
    
    # Filtre par cuvée
    cuvee = request.GET.get('cuvee', '')
    if cuvee:
        lots = lots.filter(cuvee__nom__icontains=cuvee)
    
    # Filtre par entrepôt
    entrepot = request.GET.get('entrepot', '')
    if entrepot:
        lots = lots.filter(entrepot__nom__icontains=entrepot)
    
    # Filtre par volume
    volume_min = request.GET.get('volume_min', '')
    volume_max = request.GET.get('volume_max', '')
    if volume_min:
        try:
            lots = lots.filter(volume_actuel__gte=float(volume_min))
        except ValueError:
            pass
    if volume_max:
        try:
            lots = lots.filter(volume_actuel__lte=float(volume_max))
        except ValueError:
            pass
    
    # Filtre par degré d'alcool
    degre_min = request.GET.get('degre_min', '')
    degre_max = request.GET.get('degre_max', '')
    if degre_min:
        try:
            lots = lots.filter(degre_alcool__gte=float(degre_min))
        except ValueError:
            pass
    if degre_max:
        try:
            lots = lots.filter(degre_alcool__lte=float(degre_max))
        except ValueError:
            pass
    
    # Filtre par état du stock
    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'epuise':
        lots = lots.filter(volume_actuel=0)
    elif stock_status == 'faible':
        # Lots avec moins de 20% de volume restant
        lots = lots.extra(where=["volume_actuel / volume_initial < 0.2"])
    elif stock_status == 'plein':
        # Lots avec plus de 80% de volume restant
        lots = lots.extra(where=["volume_actuel / volume_initial > 0.8"])
    
    # Tri
    sort_by = request.GET.get('sort', 'numero_lot')
    sort_order = request.GET.get('order', 'asc')
    
    valid_sorts = {
        'numero_lot': 'numero_lot',
        'cuvee': 'cuvee__nom',
        'millesime': 'millesime',
        'volume_initial': 'volume_initial',
        'volume_actuel': 'volume_actuel',
        'statut': 'statut',
        'entrepot': 'entrepot__nom',
        'degre_alcool': 'degre_alcool',
        'date_creation': 'date_creation',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }
    
    if sort_by in valid_sorts:
        order_field = valid_sorts[sort_by]
        if sort_order == 'desc':
            order_field = f'-{order_field}'
        lots = lots.order_by(order_field)
    else:
        lots = lots.order_by('numero_lot')
    
    # Pagination
    paginator = Paginator(lots, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour les filtres
    all_lots = Lot.objects.filter(organization=organization)
    stats = {
        'total': all_lots.count(),
        'filtered': lots.count(),
        'statuts': all_lots.values_list('statut', flat=True).distinct().order_by('statut'),
        'millesimes': all_lots.values_list('millesime', flat=True).distinct().order_by('-millesime'),
        'cuvees': organization.cuvees.values_list('nom', flat=True).distinct().order_by('nom')[:20],
        'entrepots': organization.entrepots.values_list('nom', flat=True).distinct().order_by('nom'),
        'volume_range': {
            'min': all_lots.aggregate(min_vol=Min('volume_actuel'))['min_vol'] or 0,
            'max': all_lots.aggregate(max_vol=Max('volume_actuel'))['max_vol'] or 1000,
        },
        'degre_range': {
            'min': all_lots.aggregate(min_degre=Min('degre_alcool'))['min_degre'] or 0,
            'max': all_lots.aggregate(max_degre=Max('degre_alcool'))['max_degre'] or 20,
        }
    }
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'statut_filter': statut,
        'millesime_filter': millesime,
        'cuvee_filter': cuvee,
        'entrepot_filter': entrepot,
        'volume_min_filter': volume_min,
        'volume_max_filter': volume_max,
        'degre_min_filter': degre_min,
        'degre_max_filter': degre_max,
        'stock_status_filter': stock_status,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'stats': stats,
        'organization': organization,
        'page_title': 'Lots'
    }
    
    return render(request, 'catalogue/lot_list.html', context)


@require_membership(role_min='editor')
def lot_create(request):
    """
    Création d'un nouveau lot - Roadmap item 22
    /lots/new – Création lot (source, volume, degré)
    """
    organization = request.current_org
    
    if request.method == 'POST':
        form = LotForm(request.POST, organization=organization)
        form.organization = organization  # Pour la validation
        
        if form.is_valid():
            lot = form.save(commit=False)
            lot.organization = organization
            lot.save()
            
            # Créer le mouvement initial de création
            MouvementLot.objects.create(
                lot=lot,
                type_mouvement='creation',
                description=f'Création du lot {lot.numero_lot}',
                volume_avant=0,
                volume_mouvement=lot.volume_initial,
                volume_apres=lot.volume_initial,
                date_mouvement=lot.created_at,
                notes=f'Lot créé avec {lot.volume_initial} {lot.unite_volume.symbole} de {lot.cuvee.nom}'
            )
            
            messages.success(request, f'Le lot "{lot.numero_lot}" a été créé avec succès.')
            return redirect('catalogue:lot_detail', pk=lot.pk)
    else:
        form = LotForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': 'Nouveau lot'
    }
    
    return render(request, 'catalogue/lot_form.html', context)


@require_membership(role_min='read_only')
def lot_detail(request, pk):
    """
    Détail d'un lot - Roadmap item 23
    /lots/:id – Détail lot (historique mouvements)
    """
    organization = request.current_org
    lot = get_object_or_404(Lot, pk=pk, organization=organization)
    
    # Historique des mouvements
    mouvements = lot.mouvements.all()
    
    # Statistiques du lot
    lot_stats = {
        'volume_consomme': lot.volume_consomme,
        'pourcentage_restant': lot.pourcentage_restant,
        'nb_mouvements': mouvements.count(),
        'est_epuise': lot.est_epuise,
    }
    
    context = {
        'lot': lot,
        'mouvements': mouvements,
        'lot_stats': lot_stats,
        'organization': organization,
        'page_title': f'Lot : {lot.numero_lot}'
    }
    
    return render(request, 'catalogue/lot_detail.html', context)


@require_membership(role_min='editor')
def lot_update(request, pk):
    """Modification d'un lot"""
    organization = request.current_org
    lot = get_object_or_404(Lot, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = LotForm(request.POST, instance=lot, organization=organization)
        form.organization = organization
        
        if form.is_valid():
            lot = form.save()
            messages.success(request, f'Le lot "{lot.numero_lot}" a été modifié avec succès.')
            return redirect('catalogue:lot_detail', pk=lot.pk)
    else:
        form = LotForm(instance=lot, organization=organization)
    
    context = {
        'form': form,
        'lot': lot,
        'organization': organization,
        'page_title': f'Modifier : {lot.numero_lot}'
    }
    
    return render(request, 'catalogue/lot_form.html', context)


@require_membership(role_min='admin')
@require_http_methods(["POST"])
def lot_delete(request, pk):
    """Suppression d'un lot"""
    organization = request.current_org
    lot = get_object_or_404(Lot, pk=pk, organization=organization)
    
    numero_lot = lot.numero_lot
    lot.delete()
    
    messages.success(request, f'Le lot "{numero_lot}" a été supprimé avec succès.')
    return redirect('catalogue:lot_list')


@require_membership(role_min='editor')
def lot_add_mouvement(request, pk):
    """Ajouter un mouvement à un lot"""
    organization = request.current_org
    lot = get_object_or_404(Lot, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = MouvementLotForm(request.POST, lot=lot, organization=organization)
        
        if form.is_valid():
            mouvement = form.save()
            messages.success(request, f'Mouvement "{mouvement.get_type_mouvement_display()}" ajouté avec succès.')
            return redirect('catalogue:lot_detail', pk=lot.pk)
    else:
        form = MouvementLotForm(lot=lot, organization=organization)
    
    context = {
        'form': form,
        'lot': lot,
        'organization': organization,
        'page_title': f'Nouveau mouvement - {lot.numero_lot}'
    }
    
    return render(request, 'catalogue/mouvement_form.html', context)
