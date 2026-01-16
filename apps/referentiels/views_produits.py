"""
Vues pour la gestion des produits (base commune)
/referentiels/produits/
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import require_membership
from apps.catalogue.models import Article, ArticleCategory, ArticleStock, ArticleTag
from apps.produits.models_catalog import Product


# ===== LISTE PRODUITS =====

@require_membership(role_min='read_only')
def produit_list(request, usage_filter=None):
    """
    Liste des produits avec recherche, filtres et tags
    GET /referentiels/produits/
    Peut être appelé avec usage_filter='achat' ou 'vente' depuis /achats/articles/ ou /ventes/articles/
    """
    org = request.current_org
    produits = Product.objects.filter(organization=org).select_related('cuvee', 'unit')
    
    # Filtre contextuel (depuis URL achats/ventes)
    context_usage = usage_filter
    if context_usage == 'achat':
        produits = produits.filter(is_buyable=True)
    elif context_usage == 'vente':
        produits = produits.filter(is_sellable=True)
    
    # Recherche texte
    q = request.GET.get('q', '').strip()
    if q:
        produits = produits.filter(
            Q(name__icontains=q) |
            Q(slug__icontains=q) |
            Q(ean__icontains=q) |
            Q(description__icontains=q)
        )
    
    # Filtres
    category = request.GET.get('category')
    if category:
        produits = produits.filter(category_id=category)
    
    article_type = request.GET.get('type')
    if article_type:
        produits = produits.filter(type_code=article_type)
    
    statut = request.GET.get('statut')
    if statut == 'actif':
        produits = produits.filter(is_active=True)
    elif statut == 'archive':
        produits = produits.filter(is_active=False)
    
    # Filtre usage supplémentaire (via GET)
    usage = request.GET.get('usage')
    if usage == 'achat' and not context_usage:
        produits = produits.filter(is_buyable=True)
    elif usage == 'vente' and not context_usage:
        produits = produits.filter(is_sellable=True)
    
    # Tri
    sort = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')
    
    sort_fields = {
        'name': 'name',
        'sku': 'slug',
        'category': 'type_code',
        'price': 'price_eur_u',
        'type': 'type_code',
        'created': 'created_at',
    }
    
    sort_field = sort_fields.get(sort, 'name')
    if order == 'desc':
        sort_field = f'-{sort_field}'
    produits = produits.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(produits, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    # Stats rapides (adaptées au contexte)
    base_qs = Product.objects.filter(organization=org)
    if context_usage == 'achat':
        base_qs = base_qs.filter(is_buyable=True)
    elif context_usage == 'vente':
        base_qs = base_qs.filter(is_sellable=True)
    
    stats = {
        'total': base_qs.count(),
        'actifs': base_qs.filter(is_active=True).count(),
        'achetables': base_qs.filter(is_buyable=True).count(),
        'vendables': base_qs.filter(is_sellable=True).count(),
    }
    
    # Catégories pour filtre
    categories = ArticleCategory.objects.filter(organization=org).order_by('name')
    
    # Titre et breadcrumb selon contexte
    base_template = 'referentiels/base_referentiels.html'
    if context_usage == 'achat':
        page_title = 'Articles Achats'
        breadcrumb = [
            {'name': 'Achats', 'url': '/achats/tableau-de-bord/'},
            {'name': 'Articles', 'url': None},
        ]
        create_url = '/achats/articles/nouveau/'
        base_template = 'commerce/base_commerce.html'
    elif context_usage == 'vente':
        page_title = 'Articles Ventes'
        breadcrumb = [
            {'name': 'Ventes', 'url': '/ventes/tableau-de-bord/'},
            {'name': 'Articles', 'url': None},
        ]
        create_url = '/ventes/articles/nouveau/'
        base_template = 'commerce/base_commerce.html'
    else:
        page_title = 'Produits'
        breadcrumb = [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Produits', 'url': None},
        ]
        create_url = '/referentiels/produits/nouveau/'
    
    context = {
        'page_obj': page_obj,
        'produits': page_obj,
        'stats': stats,
        'categories': categories,
        'type_choices': Product.TYPE_CHOICES,
        'q': q,
        'current_category': category,
        'current_type': article_type,
        'current_statut': statut,
        'current_usage': usage,
        'context_usage': context_usage,
        'sort': sort,
        'order': order,
        'page_title': page_title,
        'breadcrumb_items': breadcrumb,
        'create_url': create_url,
        'base_template': base_template,
    }
    return render(request, 'referentiels/produits/list.html', context)


@require_membership(role_min='read_only')
def produit_search_ajax(request):
    """Recherche AJAX pour autocomplete"""
    org = request.current_org
    q = request.GET.get('q', '').strip()
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    produits = Product.objects.filter(
        organization=org,
        is_active=True
    ).filter(
        Q(name__icontains=q) | Q(slug__icontains=q) | Q(ean__icontains=q)
    ).select_related('unit')[:10]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'sku': p.ean or p.slug or '',
        'type': p.get_type_code_display(),
        'price_ht': str(p.price_eur_u or 0),
        'unit': p.unit.symbole if p.unit else 'u',
    } for p in produits]
    
    return JsonResponse({'results': results})


# ===== CRÉATION PRODUIT =====

@require_membership(role_min='editor')
def produit_create(request, usage_preset=None):
    """
    Création d'un nouveau produit
    GET/POST /referentiels/produits/nouveau/
    Peut être appelé avec usage_preset='achat' ou 'vente' depuis /achats/produits/nouveau/ ou /ventes/produits/nouveau/
    """
    from django.utils.text import slugify
    from apps.referentiels.models import Unite
    
    org = request.current_org
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.POST.get('name', '').strip()
        ean = request.POST.get('sku', '').strip()  # Le champ SKU du form devient EAN
        description = request.POST.get('description', '').strip()
        type_code = request.POST.get('article_type', 'wine')
        price_eur_u = request.POST.get('price_ht') or None
        vat_rate = request.POST.get('vat_rate') or 20
        unit_str = request.POST.get('unit', '').strip()
        stockable = request.POST.get('is_stock_managed') == 'on'
        is_buyable = request.POST.get('is_buyable') == 'on'
        is_sellable = request.POST.get('is_sellable') == 'on'
        
        # Données supplémentaires pour attrs
        attrs = {}
        tasting_notes = request.POST.get('tasting_notes', '').strip()
        if tasting_notes:
            attrs['tasting_notes'] = tasting_notes
        hs_code = request.POST.get('hs_code', '').strip()
        if hs_code:
            attrs['hs_code'] = hs_code
        origin_country = request.POST.get('origin_country', '').strip()
        if origin_country:
            attrs['origin_country'] = origin_country
        alcohol_degree = request.POST.get('alcohol_degree')
        if alcohol_degree:
            attrs['alcohol_degree'] = alcohol_degree
        customs_notes = request.POST.get('customs_notes', '').strip()
        if customs_notes:
            attrs['customs_notes'] = customs_notes
        purchase_price = request.POST.get('purchase_price')
        if purchase_price:
            attrs['purchase_price'] = purchase_price
        
        # Tags (JSONField)
        tags_input = request.POST.get('tags', '').strip()
        tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
        
        # Volume net
        net_volume = request.POST.get('net_volume')
        volume_l = None
        if net_volume:
            try:
                volume_l = float(net_volume)
            except (ValueError, TypeError):
                pass
        
        # Validation basique
        errors = {}
        if not name:
            errors['name'] = "La désignation est obligatoire."
        
        if ean:
            if Product.objects.filter(organization=org, ean=ean).exists():
                errors['sku'] = "Ce code article existe déjà."
        
        # Chercher ou créer une unité
        unit = None
        if unit_str:
            unit = Unite.objects.filter(organization=org, symbole__iexact=unit_str).first()
            if not unit:
                unit = Unite.objects.filter(organization=org, nom__iexact=unit_str).first()
        
        if errors:
            categories = ArticleCategory.objects.filter(organization=org)
            return render(request, 'referentiels/produits/form.html', {
                'errors': errors,
                'data': request.POST,
                'categories': categories,
                'type_choices': Product.TYPE_CHOICES,
                'is_new': True,
                'page_title': 'Nouveau produit',
                'breadcrumb_items': [
                    {'name': 'Référentiels', 'url': '/referentiels/'},
                    {'name': 'Produits', 'url': '/referentiels/produits/'},
                    {'name': 'Nouveau', 'url': None},
                ],
            })
        
        # Générer un slug unique
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Créer le produit
        produit = Product.objects.create(
            organization=org,
            name=name,
            slug=slug,
            ean=ean,
            description=description,
            type_code=type_code,
            price_eur_u=price_eur_u if price_eur_u else None,
            vat_rate=vat_rate,
            unit=unit,
            stockable=stockable,
            is_buyable=is_buyable,
            is_sellable=is_sellable,
            is_active=True,
            volume_l=volume_l,
            tags=tags,
            attrs=attrs,
        )
        
        # Gestion image
        if 'image' in request.FILES:
            produit.image = request.FILES['image']
            produit.save(update_fields=['image'])
        
        messages.success(request, f'Produit "{produit.name}" créé avec succès.')
        
        # Redirection selon contexte
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('referentiels:produit_detail', pk=produit.pk)
    
    # GET: Afficher formulaire vide
    categories = ArticleCategory.objects.filter(organization=org)
    
    # Pré-remplissage selon contexte (URL param ou usage_preset)
    prefill = {'is_stock_managed': True}
    context_usage = usage_preset or request.GET.get('usage')
    
    if context_usage == 'achat':
        prefill.update({'is_buyable': True, 'is_sellable': False})
        page_title = 'Nouveau produit achat'
        breadcrumb = [
            {'name': 'Achats', 'url': '/achats/tableau-de-bord/'},
            {'name': 'Produits', 'url': '/achats/produits/'},
            {'name': 'Nouveau', 'url': None},
        ]
        back_url = '/achats/produits/'
    elif context_usage == 'vente':
        prefill.update({'is_buyable': False, 'is_sellable': True})
        page_title = 'Nouveau produit vente'
        breadcrumb = [
            {'name': 'Ventes', 'url': '/ventes/tableau-de-bord/'},
            {'name': 'Produits', 'url': '/ventes/produits/'},
            {'name': 'Nouveau', 'url': None},
        ]
        back_url = '/ventes/produits/'
    else:
        prefill.update({'is_buyable': True, 'is_sellable': True})
        page_title = 'Nouveau produit'
        breadcrumb = [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Produits', 'url': '/referentiels/produits/'},
            {'name': 'Nouveau', 'url': None},
        ]
        back_url = '/referentiels/produits/'
    
    context = {
        'categories': categories,
        'type_choices': Product.TYPE_CHOICES,
        'is_new': True,
        'data': prefill,
        'context_usage': context_usage,
        'page_title': page_title,
        'breadcrumb_items': breadcrumb,
        'back_url': back_url,
    }
    return render(request, 'referentiels/produits/form.html', context)


# ===== FICHE PRODUIT (DÉTAIL) =====

@require_membership(role_min='read_only')
def produit_detail(request, pk):
    """
    Fiche produit avec onglets
    GET /referentiels/produits/<id>/
    """
    org = request.current_org
    produit = get_object_or_404(Product, pk=pk, organization=org)
    
    # Onglet actif
    tab = request.GET.get('tab', 'general')
    
    # Données selon l'onglet
    context_data = {}
    
    if tab == 'stock':
        # Stock par emplacement
        stocks = ArticleStock.objects.filter(
            article=produit
        ).select_related('location').order_by('location__nom')
        context_data['stocks'] = stocks
        context_data['stock_total'] = stocks.aggregate(total=Sum('quantity'))['total'] or 0
    
    elif tab == 'mouvements':
        # Historique mouvements (à implémenter si besoin)
        from apps.catalogue.models import StockMovement
        mouvements = StockMovement.objects.filter(
            article=produit
        ).select_related('location').order_by('-date')[:50]
        context_data['mouvements'] = mouvements
    
    elif tab == 'ventes':
        # Lignes de documents commerciaux (ventes)
        # TODO: Lier avec CommercialLine quand disponible
        context_data['ventes'] = []
    
    elif tab == 'achats':
        # Lignes de documents commerciaux (achats)
        context_data['achats'] = []
    
    # Permissions
    membership = request.user.get_active_membership()
    can_edit = membership and membership.role in ['admin', 'editor']
    
    context = {
        'produit': produit,
        'tab': tab,
        'can_edit': can_edit,
        **context_data,
        'page_title': produit.name,
        'breadcrumb_items': [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Produits', 'url': '/referentiels/produits/'},
            {'name': produit.name, 'url': None},
        ],
    }
    return render(request, 'referentiels/produits/detail.html', context)


# ===== MODIFICATION PRODUIT =====

@require_membership(role_min='editor')
def produit_update(request, pk):
    """
    Modification d'un produit
    GET/POST /referentiels/produits/<id>/modifier/
    """
    from apps.referentiels.models import Unite
    
    org = request.current_org
    produit = get_object_or_404(Product, pk=pk, organization=org)
    
    if request.method == 'POST':
        # Récupérer les données
        produit.name = request.POST.get('name', '').strip()
        ean = request.POST.get('sku', '').strip()
        produit.ean = ean
        produit.description = request.POST.get('description', '').strip()
        produit.type_code = request.POST.get('article_type', 'wine')
        produit.price_eur_u = request.POST.get('price_ht') or None
        produit.vat_rate = request.POST.get('vat_rate') or 20
        produit.stockable = request.POST.get('is_stock_managed') == 'on'
        produit.is_buyable = request.POST.get('is_buyable') == 'on'
        produit.is_sellable = request.POST.get('is_sellable') == 'on'
        
        # Volume
        net_volume = request.POST.get('net_volume')
        if net_volume:
            try:
                produit.volume_l = float(net_volume)
            except (ValueError, TypeError):
                pass
        
        # Unité
        unit_str = request.POST.get('unit', '').strip()
        if unit_str:
            unit = Unite.objects.filter(organization=org, symbole__iexact=unit_str).first()
            if not unit:
                unit = Unite.objects.filter(organization=org, nom__iexact=unit_str).first()
            produit.unit = unit
        
        # Attrs pour données supplémentaires
        attrs = produit.attrs or {}
        tasting_notes = request.POST.get('tasting_notes', '').strip()
        if tasting_notes:
            attrs['tasting_notes'] = tasting_notes
        hs_code = request.POST.get('hs_code', '').strip()
        if hs_code:
            attrs['hs_code'] = hs_code
        origin_country = request.POST.get('origin_country', '').strip()
        if origin_country:
            attrs['origin_country'] = origin_country
        alcohol_degree = request.POST.get('alcohol_degree')
        if alcohol_degree:
            attrs['alcohol_degree'] = alcohol_degree
        customs_notes = request.POST.get('customs_notes', '').strip()
        if customs_notes:
            attrs['customs_notes'] = customs_notes
        purchase_price = request.POST.get('purchase_price')
        if purchase_price:
            attrs['purchase_price'] = purchase_price
        produit.attrs = attrs
        
        # Tags (JSONField)
        tags_input = request.POST.get('tags', '').strip()
        produit.tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
        
        if 'image' in request.FILES:
            produit.image = request.FILES['image']
        
        # Validation
        errors = {}
        if not produit.name:
            errors['name'] = "La désignation est obligatoire."
        
        if ean:
            if Product.objects.filter(organization=org, ean=ean).exclude(pk=pk).exists():
                errors['sku'] = "Ce code article existe déjà."
        
        if errors:
            categories = ArticleCategory.objects.filter(organization=org)
            return render(request, 'referentiels/produits/form.html', {
                'errors': errors,
                'produit': produit,
                'data': request.POST,
                'categories': categories,
                'type_choices': Product.TYPE_CHOICES,
                'is_new': False,
                'page_title': f'Modifier {produit.name}',
                'breadcrumb_items': [
                    {'name': 'Référentiels', 'url': '/referentiels/'},
                    {'name': 'Produits', 'url': '/referentiels/produits/'},
                    {'name': produit.name, 'url': f'/referentiels/produits/{pk}/'},
                    {'name': 'Modifier', 'url': None},
                ],
            })
        
        produit.save()
        
        messages.success(request, f'Produit "{produit.name}" modifié avec succès.')
        
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('referentiels:produit_detail', pk=produit.pk)
    
    # GET: Afficher formulaire pré-rempli
    categories = ArticleCategory.objects.filter(organization=org)
    attrs = produit.attrs or {}
    
    context = {
        'produit': produit,
        'data': {
            'name': produit.name,
            'sku': produit.ean or '',
            'description': produit.description,
            'article_type': produit.type_code,
            'price_ht': produit.price_eur_u or '',
            'purchase_price': attrs.get('purchase_price', ''),
            'vat_rate': produit.vat_rate,
            'unit': produit.unit.symbole if produit.unit else '',
            'is_stock_managed': produit.stockable,
            'is_buyable': produit.is_buyable,
            'is_sellable': produit.is_sellable,
            'tasting_notes': attrs.get('tasting_notes', ''),
            'hs_code': attrs.get('hs_code', ''),
            'origin_country': attrs.get('origin_country', ''),
            'alcohol_degree': attrs.get('alcohol_degree', ''),
            'net_volume': produit.volume_l or '',
            'customs_notes': attrs.get('customs_notes', ''),
            'tags': ', '.join(produit.tags) if produit.tags else '',
        },
        'categories': categories,
        'type_choices': Product.TYPE_CHOICES,
        'is_new': False,
        'page_title': f'Modifier {produit.name}',
        'breadcrumb_items': [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Produits', 'url': '/referentiels/produits/'},
            {'name': produit.name, 'url': f'/referentiels/produits/{pk}/'},
            {'name': 'Modifier', 'url': None},
        ],
    }
    return render(request, 'referentiels/produits/form.html', context)


# ===== ARCHIVAGE PRODUIT =====

@require_membership(role_min='editor')
@require_POST
def produit_archive(request, pk):
    """
    Archiver/Désarchiver un produit
    POST /referentiels/produits/<id>/archiver/
    """
    org = request.current_org
    produit = get_object_or_404(Product, pk=pk, organization=org)
    
    # Toggle is_active
    produit.is_active = not produit.is_active
    produit.save(update_fields=['is_active'])
    
    if produit.is_active:
        messages.success(request, f'Produit "{produit.name}" réactivé.')
    else:
        messages.success(request, f'Produit "{produit.name}" archivé.')
    
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('referentiels:produit_list')


# ===== CATÉGORIES (CRUD rapide) =====

@require_membership(role_min='editor')
def categorie_create_ajax(request):
    """Création rapide de catégorie via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    org = request.current_org
    name = request.POST.get('name', '').strip()
    
    if not name:
        return JsonResponse({'error': 'Nom requis'}, status=400)
    
    if ArticleCategory.objects.filter(organization=org, name=name).exists():
        return JsonResponse({'error': 'Cette catégorie existe déjà'}, status=400)
    
    cat = ArticleCategory.objects.create(organization=org, name=name)
    return JsonResponse({
        'id': cat.id,
        'name': cat.name,
        'message': f'Catégorie "{name}" créée'
    })
