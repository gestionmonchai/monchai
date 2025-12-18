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


# ===== LISTE PRODUITS =====

@require_membership(role_min='read_only')
def produit_list(request, usage_filter=None):
    """
    Liste des produits avec recherche, filtres et tags
    GET /referentiels/produits/
    Peut être appelé avec usage_filter='achat' ou 'vente' depuis /achats/articles/ ou /ventes/articles/
    """
    org = request.current_org
    produits = Article.objects.filter(organization=org).select_related('category').prefetch_related('tags')
    
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
            Q(sku__icontains=q) |
            Q(description__icontains=q)
        )
    
    # Filtres
    category = request.GET.get('category')
    if category:
        produits = produits.filter(category_id=category)
    
    article_type = request.GET.get('type')
    if article_type:
        produits = produits.filter(article_type=article_type)
    
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
        'sku': 'sku',
        'category': 'category__name',
        'price': 'price_ht',
        'type': 'article_type',
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
    base_qs = Article.objects.filter(organization=org)
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
    if context_usage == 'achat':
        page_title = 'Articles Achats'
        breadcrumb = [
            {'name': 'Achats', 'url': '/achats/dashboard/'},
            {'name': 'Articles', 'url': None},
        ]
        create_url = '/achats/articles/nouveau/'
    elif context_usage == 'vente':
        page_title = 'Articles Ventes'
        breadcrumb = [
            {'name': 'Ventes', 'url': '/ventes/dashboard/'},
            {'name': 'Articles', 'url': None},
        ]
        create_url = '/ventes/articles/nouveau/'
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
        'type_choices': Article.TYPE_CHOICES,
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
    }
    return render(request, 'referentiels/produits/list.html', context)


@require_membership(role_min='read_only')
def produit_search_ajax(request):
    """Recherche AJAX pour autocomplete"""
    org = request.current_org
    q = request.GET.get('q', '').strip()
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    produits = Article.objects.filter(
        organization=org,
        is_active=True
    ).filter(
        Q(name__icontains=q) | Q(sku__icontains=q)
    )[:10]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku or '',
        'type': p.get_article_type_display(),
        'price_ht': str(p.price_ht),
        'unit': p.unit,
    } for p in produits]
    
    return JsonResponse({'results': results})


# ===== CRÉATION PRODUIT =====

@require_membership(role_min='editor')
def produit_create(request, usage_preset=None):
    """
    Création d'un nouveau produit
    GET/POST /referentiels/produits/nouveau/
    Peut être appelé avec usage_preset='achat' ou 'vente' depuis /achats/articles/nouveau/ ou /ventes/articles/nouveau/
    """
    org = request.current_org
    
    if request.method == 'POST':
        # Récupérer les données
        data = {
            'name': request.POST.get('name', '').strip(),
            'sku': request.POST.get('sku', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'article_type': request.POST.get('article_type', 'product'),
            'category_id': request.POST.get('category') or None,
            'price_ht': request.POST.get('price_ht') or 0,
            'purchase_price': request.POST.get('purchase_price') or 0,
            'vat_rate': request.POST.get('vat_rate') or 20,
            'unit': request.POST.get('unit', 'PCE').strip(),
            'is_stock_managed': request.POST.get('is_stock_managed') == 'on',
            'is_buyable': request.POST.get('is_buyable') == 'on',
            'is_sellable': request.POST.get('is_sellable') == 'on',
            'is_active': True,
            'tasting_notes': request.POST.get('tasting_notes', '').strip(),
            # Douane
            'hs_code': request.POST.get('hs_code', '').strip(),
            'origin_country': request.POST.get('origin_country', 'France').strip(),
            'alcohol_degree': request.POST.get('alcohol_degree') or None,
            'net_volume': request.POST.get('net_volume') or None,
            'customs_notes': request.POST.get('customs_notes', '').strip(),
        }
        
        # Gestion image
        if 'image' in request.FILES:
            data['image'] = request.FILES['image']
        
        # Validation basique
        errors = {}
        if not data['name']:
            errors['name'] = "La désignation est obligatoire."
        
        if data['sku']:
            if Article.objects.filter(organization=org, sku=data['sku']).exists():
                errors['sku'] = "Ce code article existe déjà."
        
        if errors:
            categories = ArticleCategory.objects.filter(organization=org)
            return render(request, 'referentiels/produits/form.html', {
                'errors': errors,
                'data': data,
                'categories': categories,
                'type_choices': Article.TYPE_CHOICES,
                'is_new': True,
                'page_title': 'Nouveau produit',
                'breadcrumb_items': [
                    {'name': 'Référentiels', 'url': '/referentiels/'},
                    {'name': 'Produits', 'url': '/referentiels/produits/'},
                    {'name': 'Nouveau', 'url': None},
                ],
            })
        
        # Créer le produit
        produit = Article.objects.create(organization=org, **data)
        
        # Gestion des tags
        tags_input = request.POST.get('tags', '').strip()
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag, _ = ArticleTag.objects.get_or_create(
                    organization=org, 
                    name=tag_name
                )
                produit.tags.add(tag)
        
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
        page_title = 'Nouvel article achat'
        breadcrumb = [
            {'name': 'Achats', 'url': '/achats/dashboard/'},
            {'name': 'Articles', 'url': '/achats/articles/'},
            {'name': 'Nouveau', 'url': None},
        ]
        back_url = '/achats/articles/'
    elif context_usage == 'vente':
        prefill.update({'is_buyable': False, 'is_sellable': True})
        page_title = 'Nouvel article vente'
        breadcrumb = [
            {'name': 'Ventes', 'url': '/ventes/dashboard/'},
            {'name': 'Articles', 'url': '/ventes/articles/'},
            {'name': 'Nouveau', 'url': None},
        ]
        back_url = '/ventes/articles/'
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
        'type_choices': Article.TYPE_CHOICES,
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
    produit = get_object_or_404(Article, pk=pk, organization=org)
    
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
    org = request.current_org
    produit = get_object_or_404(Article, pk=pk, organization=org)
    
    if request.method == 'POST':
        # Récupérer les données
        produit.name = request.POST.get('name', '').strip()
        produit.sku = request.POST.get('sku', '').strip()
        produit.description = request.POST.get('description', '').strip()
        produit.article_type = request.POST.get('article_type', 'product')
        produit.category_id = request.POST.get('category') or None
        produit.price_ht = request.POST.get('price_ht') or 0
        produit.purchase_price = request.POST.get('purchase_price') or 0
        produit.vat_rate = request.POST.get('vat_rate') or 20
        produit.unit = request.POST.get('unit', 'PCE').strip()
        produit.is_stock_managed = request.POST.get('is_stock_managed') == 'on'
        produit.is_buyable = request.POST.get('is_buyable') == 'on'
        produit.is_sellable = request.POST.get('is_sellable') == 'on'
        produit.tasting_notes = request.POST.get('tasting_notes', '').strip()
        
        # Douane
        produit.hs_code = request.POST.get('hs_code', '').strip()
        produit.origin_country = request.POST.get('origin_country', 'France').strip()
        produit.alcohol_degree = request.POST.get('alcohol_degree') or None
        produit.net_volume = request.POST.get('net_volume') or None
        produit.customs_notes = request.POST.get('customs_notes', '').strip()
        
        if 'image' in request.FILES:
            produit.image = request.FILES['image']
        
        # Validation
        errors = {}
        if not produit.name:
            errors['name'] = "La désignation est obligatoire."
        
        if produit.sku:
            if Article.objects.filter(organization=org, sku=produit.sku).exclude(pk=pk).exists():
                errors['sku'] = "Ce code article existe déjà."
        
        if errors:
            categories = ArticleCategory.objects.filter(organization=org)
            return render(request, 'referentiels/produits/form.html', {
                'errors': errors,
                'produit': produit,
                'data': {
                    'name': produit.name,
                    'sku': produit.sku,
                    'description': produit.description,
                    'article_type': produit.article_type,
                    'category': produit.category_id,
                    'price_ht': produit.price_ht,
                    'purchase_price': produit.purchase_price,
                    'vat_rate': produit.vat_rate,
                    'unit': produit.unit,
                    'is_stock_managed': produit.is_stock_managed,
                    'is_buyable': produit.is_buyable,
                    'is_sellable': produit.is_sellable,
                    'tasting_notes': produit.tasting_notes,
                    'hs_code': produit.hs_code,
                    'origin_country': produit.origin_country,
                    'alcohol_degree': produit.alcohol_degree,
                    'net_volume': produit.net_volume,
                    'customs_notes': produit.customs_notes,
                    'tags': ', '.join([t.name for t in produit.tags.all()]),
                },
                'categories': categories,
                'type_choices': Article.TYPE_CHOICES,
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
        
        # Mise à jour des tags
        tags_input = request.POST.get('tags', '').strip()
        produit.tags.clear()
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag, _ = ArticleTag.objects.get_or_create(
                    organization=org, 
                    name=tag_name
                )
                produit.tags.add(tag)
        
        messages.success(request, f'Produit "{produit.name}" modifié avec succès.')
        
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('referentiels:produit_detail', pk=produit.pk)
    
    # GET: Afficher formulaire pré-rempli
    categories = ArticleCategory.objects.filter(organization=org)
    
    context = {
        'produit': produit,
        'data': {
            'name': produit.name,
            'sku': produit.sku,
            'description': produit.description,
            'article_type': produit.article_type,
            'category': produit.category_id,
            'price_ht': produit.price_ht,
            'purchase_price': produit.purchase_price,
            'vat_rate': produit.vat_rate,
            'unit': produit.unit,
            'is_stock_managed': produit.is_stock_managed,
            'is_buyable': produit.is_buyable,
            'is_sellable': produit.is_sellable,
            'tasting_notes': produit.tasting_notes,
            'hs_code': produit.hs_code,
            'origin_country': produit.origin_country,
            'alcohol_degree': produit.alcohol_degree,
            'net_volume': produit.net_volume,
            'customs_notes': produit.customs_notes,
            'tags': ', '.join([t.name for t in produit.tags.all()]),
        },
        'categories': categories,
        'type_choices': Article.TYPE_CHOICES,
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
    produit = get_object_or_404(Article, pk=pk, organization=org)
    
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
