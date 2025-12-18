"""
Vues pour la gestion des grilles tarifaires
Module ergonomique avec recherche temps réel et import en masse
"""
import csv
import io
import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.views.decorators.http import require_http_methods, require_GET
from django.core.paginator import Paginator
from django.utils import timezone

from apps.accounts.decorators import require_membership
# from apps.stock.models import SKU  <-- Removed
# from apps.viticulture.models import Cuvee <-- Removed
from apps.catalogue.models import Article, ArticleCategory
from .models import PriceList, PriceItem
from .forms_pricelists import PriceListForm, PriceItemForm, PriceListImportForm


# ═══════════════════════════════════════════════
# VUES PRINCIPALES - LISTE & CRUD
# ═══════════════════════════════════════════════

@login_required
@require_membership()
def pricelist_list(request):
    """
    Liste des grilles tarifaires avec recherche temps réel
    Vue classique Mon Chai avec design viticole
    """
    org = request.current_org
    
    # Recherche
    search_query = request.GET.get('q', '').strip()
    
    # Queryset de base
    pricelists = PriceList.objects.filter(organization=org)
    
    # Recherche
    if search_query:
        pricelists = pricelists.filter(
            Q(name__icontains=search_query) |
            Q(currency__icontains=search_query)
        )
    
    # Filtres
    is_active = request.GET.get('is_active')
    if is_active == '1':
        pricelists = pricelists.filter(is_active=True)
    elif is_active == '0':
        pricelists = pricelists.filter(is_active=False)
    
    # Annotation : nombre d'items
    pricelists = pricelists.annotate(
        items_count=Count('items')
    )
    
    # Tri
    sort_by = request.GET.get('sort', '-valid_from')
    pricelists = pricelists.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(pricelists, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pricelists': page_obj.object_list,
        'search_query': search_query,
        'is_active': is_active,
        'sort_by': sort_by,
        'total_count': paginator.count,
    }
    
    return render(request, 'sales/pricelist_list.html', context)


@login_required
@require_membership('admin')
def pricelist_create(request):
    """Création d'une nouvelle grille tarifaire"""
    org = request.current_org
    
    if request.method == 'POST':
        form = PriceListForm(request.POST, organization=org)
        if form.is_valid():
            pricelist = form.save(commit=False)
            pricelist.organization = org
            pricelist.save()
            messages.success(request, f'Grille tarifaire "{pricelist.name}" créée avec succès.')
            return redirect('ventes:pricelist_detail', pk=pricelist.pk)
    else:
        # Date par défaut : aujourd'hui
        initial = {'valid_from': timezone.now().date()}
        form = PriceListForm(organization=org, initial=initial)
    
    context = {
        'form': form,
        'title': 'Créer une grille tarifaire',
        'submit_text': 'Créer la grille',
    }
    
    return render(request, 'sales/pricelist_form.html', context)


@login_required
@require_membership()
def pricelist_detail(request, pk):
    """Détail d'une grille tarifaire avec ses items"""
    org = request.current_org
    
    pricelist = get_object_or_404(
        PriceList.objects.filter(organization=org)
        .prefetch_related(
            Prefetch(
                'items',
                queryset=PriceItem.objects.select_related('article', 'article__category')
                .order_by('article__name', 'min_qty')
            )
        ),
        pk=pk
    )
    
    # Grouper les items par Article pour affichage hiérarchique
    items_by_article = {}
    for item in pricelist.items.all():
        article_id = item.article.id
        if article_id not in items_by_article:
            items_by_article[article_id] = {
                'article': item.article,
                'items': []
            }
        items_by_article[article_id]['items'].append(item)
    
    context = {
        'pricelist': pricelist,
        'items_by_article': items_by_article,
    }
    
    return render(request, 'sales/pricelist_detail.html', context)


@login_required
@require_membership('admin')
def pricelist_edit(request, pk):
    """Édition d'une grille tarifaire"""
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    if request.method == 'POST':
        form = PriceListForm(request.POST, instance=pricelist, organization=org)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grille tarifaire "{pricelist.name}" modifiée avec succès.')
            return redirect('ventes:pricelist_detail', pk=pricelist.pk)
    else:
        form = PriceListForm(instance=pricelist, organization=org)
    
    context = {
        'form': form,
        'pricelist': pricelist,
        'title': f'Modifier "{pricelist.name}"',
        'submit_text': 'Enregistrer les modifications',
    }
    
    return render(request, 'sales/pricelist_form.html', context)


@login_required
@require_membership('admin')
@require_http_methods(['POST'])
def pricelist_delete(request, pk):
    """Suppression d'une grille tarifaire"""
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    name = pricelist.name
    pricelist.delete()
    
    messages.success(request, f'Grille tarifaire "{name}" supprimée avec succès.')
    return redirect('ventes:pricelist_list')


# ═══════════════════════════════════════════════
# ÉDITION EN GRILLE (TABLEAU INTERACTIF)
# ═══════════════════════════════════════════════

@login_required
@require_membership('admin')
def pricelist_grid_edit(request, pk):
    """
    Édition en grille de tous les items
    Interface tableau interactif avec AJAX
    """
    org = request.current_org
    
    pricelist = get_object_or_404(
        PriceList.objects.filter(organization=org),
        pk=pk
    )
    
    # Tous les Articles vendables de l'organisation
    articles = Article.objects.filter(organization=org, is_active=True, is_sellable=True)\
        .select_related('category')\
        .order_by('category__name', 'name')
    
    # Données pour les filtres
    category_ids = articles.values_list('category_id', flat=True).distinct()
    filter_categories = ArticleCategory.objects.filter(id__in=category_ids).order_by('name')
    
    # Types d'articles
    type_choices = dict(Article.TYPE_CHOICES)
    filter_types = []
    
    # Récupérer les types utilisés
    used_types = set(articles.values_list('article_type', flat=True).distinct())
            
    # Construire la liste filtrée avec labels
    for type_code in used_types:
        if type_code in type_choices:
            filter_types.append({
                'code': type_code,
                'label': type_choices[type_code]
            })
    filter_types.sort(key=lambda x: x['label'])

    # Items existants
    existing_items = {
        (item.article_id, item.min_qty or 0): item
        for item in pricelist.items.select_related('article').all()
    }
    
    # Construire la grille
    grid_data = []
    for article in articles:
        # Chercher les items existants pour cet article
        item_unit = existing_items.get((article.id, 0))
        item_carton6 = existing_items.get((article.id, 6))
        item_carton12 = existing_items.get((article.id, 12))
        
        grid_data.append({
            'article': article,
            'item_unit': item_unit,
            'item_carton6': item_carton6,
            'item_carton12': item_carton12,
        })
    
    context = {
        'pricelist': pricelist,
        'grid_data': grid_data,
        'filter_categories': filter_categories,
        'filter_types': filter_types,
    }
    
    return render(request, 'sales/pricelist_grid_edit.html', context)


# ═══════════════════════════════════════════════
# IMPORT TARIFAIRE CSV/EXCEL
# ═══════════════════════════════════════════════

@login_required
@require_membership('admin')
def pricelist_import(request, pk):
    """
    Import en masse depuis CSV/Excel
    Étape 1 : Upload du fichier
    """
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    if request.method == 'POST':
        form = PriceListImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Lire et parser le fichier
            file = request.FILES['file']
            
            try:
                # Décoder le CSV
                decoded_file = file.read().decode('utf-8-sig')
                csv_data = csv.DictReader(io.StringIO(decoded_file), delimiter=';')
                
                # Parser les lignes
                preview_data = []
                errors = []
                
                for row_num, row in enumerate(csv_data, start=2):
                    try:
                        sku_code = row.get('code_sku', '').strip()
                        unit_price = row.get('prix_unitaire', '').strip()
                        min_qty = row.get('qte_min', '0').strip() or '0'
                        discount = row.get('remise_pct', '0').strip() or '0'
                        
                        if not sku_code or not unit_price:
                            continue
                        
                        # Valider les données
                        try:
                            unit_price_decimal = Decimal(unit_price.replace(',', '.'))
                            min_qty_int = int(min_qty)
                            discount_decimal = Decimal(discount.replace(',', '.'))
                        except (ValueError, InvalidOperation) as e:
                            errors.append(f"Ligne {row_num}: Erreur de format - {e}")
                            continue
                        
                        # Chercher l'Article
                        try:
                            article = Article.objects.get(sku=sku_code, organization=org)
                        except Article.DoesNotExist:
                            errors.append(f"Ligne {row_num}: Article avec code '{sku_code}' introuvable")
                            continue
                        
                        preview_data.append({
                            'row_num': row_num,
                            'article': article,
                            'sku_code': sku_code,
                            'unit_price': unit_price_decimal,
                            'min_qty': min_qty_int,
                            'discount_pct': discount_decimal,
                        })
                    
                    except Exception as e:
                        errors.append(f"Ligne {row_num}: Erreur inattendue - {e}")
                
                # Stocker en session pour confirmation
                request.session['import_preview_data'] = [
                    {
                        'article_id': str(item['article'].id),
                        'sku_code': item['sku_code'],
                        'article_name': item['article'].name,
                        'unit_price': str(item['unit_price']),
                        'min_qty': item['min_qty'],
                        'discount_pct': str(item['discount_pct']),
                    }
                    for item in preview_data
                ]
                request.session['import_errors'] = errors
                request.session['import_pricelist_id'] = str(pricelist.id)
                
                return redirect('ventes:pricelist_import_preview', pk=pricelist.pk)
            
            except Exception as e:
                messages.error(request, f'Erreur lors de la lecture du fichier : {e}')
    
    else:
        form = PriceListImportForm()
    
    context = {
        'form': form,
        'pricelist': pricelist,
    }
    
    return render(request, 'sales/pricelist_import.html', context)


@login_required
@require_membership('admin')
def pricelist_import_preview(request, pk):
    """
    Import en masse - Étape 2 : Prévisualisation
    """
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    # Récupérer les données de session
    preview_data = request.session.get('import_preview_data', [])
    errors = request.session.get('import_errors', [])
    
    if not preview_data and not errors:
        messages.warning(request, 'Aucune donnée à importer.')
        return redirect('ventes:pricelist_import', pk=pricelist.pk)
    
    context = {
        'pricelist': pricelist,
        'preview_data': preview_data,
        'errors': errors,
        'valid_count': len(preview_data),
        'error_count': len(errors),
    }
    
    return render(request, 'sales/pricelist_import_preview.html', context)


@login_required
@require_membership('admin')
@require_http_methods(['POST'])
def pricelist_import_confirm(request, pk):
    """
    Import en masse - Étape 3 : Confirmation et import
    """
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    # Récupérer les données
    preview_data = request.session.get('import_preview_data', [])
    
    if not preview_data:
        messages.error(request, 'Aucune donnée à importer.')
        return redirect('ventes:pricelist_import', pk=pricelist.pk)
    
    # Mode d'import
    import_mode = request.POST.get('mode', 'replace')  # replace ou merge
    
    # Supprimer les items existants si mode replace
    if import_mode == 'replace':
        deleted_count = pricelist.items.all().delete()[0]
        messages.info(request, f'{deleted_count} prix existants supprimés.')
    
    # Créer les items
    created_count = 0
    updated_count = 0
    
    for item_data in preview_data:
        article_id = item_data['article_id']
        unit_price = Decimal(item_data['unit_price'])
        min_qty = item_data['min_qty']
        discount_pct = Decimal(item_data['discount_pct'])
        
        # Vérifier si existe déjà (mode merge)
        existing_item = PriceItem.objects.filter(
            price_list=pricelist,
            article_id=article_id,
            min_qty=min_qty if min_qty > 0 else None
        ).first()
        
        if existing_item and import_mode == 'merge':
            # Mettre à jour
            existing_item.unit_price = unit_price
            existing_item.discount_pct = discount_pct
            existing_item.save()
            updated_count += 1
        else:
            # Créer
            PriceItem.objects.create(
                price_list=pricelist,
                article_id=article_id,
                unit_price=unit_price,
                min_qty=min_qty if min_qty > 0 else None,
                discount_pct=discount_pct,
                organization=org
            )
            created_count += 1
    
    # Nettoyer la session
    del request.session['import_preview_data']
    del request.session['import_errors']
    del request.session['import_pricelist_id']
    
    messages.success(
        request,
        f'Import terminé : {created_count} prix créés, {updated_count} prix mis à jour.'
    )
    
    return redirect('ventes:pricelist_detail', pk=pricelist.pk)


# ═══════════════════════════════════════════════
# API RECHERCHE TEMPS RÉEL
# ═══════════════════════════════════════════════

@login_required
@require_membership()
@require_GET
def pricelist_search_api(request):
    """
    API recherche temps réel pour grilles tarifaires
    Format JSON compatible avec autocomplete
    """
    org = request.current_org
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Recherche
    pricelists = PriceList.objects.filter(
        organization=org
    ).filter(
        Q(name__icontains=query) |
        Q(currency__icontains=query)
    ).annotate(
        items_count=Count('items')
    )[:10]
    
    results = [
        {
            'id': str(pricelist.id),
            'name': pricelist.name,
            'currency': pricelist.currency,
            'valid_from': pricelist.valid_from.strftime('%d/%m/%Y'),
            'valid_to': pricelist.valid_to.strftime('%d/%m/%Y') if pricelist.valid_to else None,
            'is_active': pricelist.is_active,
            'items_count': pricelist.items_count,
        }
        for pricelist in pricelists
    ]
    
    return JsonResponse({'results': results})


# ═══════════════════════════════════════════════
# API ITEMS (POUR ÉDITION GRILLE AJAX)
# ═══════════════════════════════════════════════

@login_required
@require_membership('admin')
@require_http_methods(['GET', 'POST'])
def pricelist_items_api(request, pk):
    """
    API pour récupérer/créer les items d'une grille
    Utilisé par l'édition en grille
    """
    org = request.current_org
    pricelist = get_object_or_404(PriceList, pk=pk, organization=org)
    
    if request.method == 'GET':
        # Retourner tous les items
        items = pricelist.items.select_related('article').all()
        
        results = [
            {
                'id': str(item.id),
                'article_id': str(item.article.id),
                'article_name': item.article.name,
                'unit_price': str(item.unit_price),
                'min_qty': item.min_qty,
                'discount_pct': str(item.discount_pct),
            }
            for item in items
        ]
        
        return JsonResponse({'items': results})
    
    elif request.method == 'POST':
        # Créer/Mettre à jour un item
        try:
            data = json.loads(request.body)
            article_id = data.get('article_id') or data.get('sku_id') # Fallback for old frontend code
            unit_price = Decimal(data.get('unit_price', '0'))
            min_qty = data.get('min_qty')
            discount_pct = Decimal(data.get('discount_pct', '0'))
            
            # Vérifier l'Article
            article = get_object_or_404(Article, id=article_id, organization=org)
            
            # Créer ou mettre à jour
            item, created = PriceItem.objects.update_or_create(
                price_list=pricelist,
                article=article,
                min_qty=min_qty if min_qty else None,
                defaults={
                    'unit_price': unit_price,
                    'discount_pct': discount_pct,
                    'organization': org
                }
            )
            
            return JsonResponse({
                'success': True,
                'created': created,
                'item': {
                    'id': str(item.id),
                    'article_id': str(item.article.id),
                    'unit_price': str(item.unit_price),
                    'min_qty': item.min_qty,
                    'discount_pct': str(item.discount_pct),
                }
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_membership('admin')
@require_http_methods(['PUT', 'DELETE'])
def priceitem_update_api(request, item_id):
    """
    API pour mettre à jour/supprimer un item spécifique
    """
    org = request.current_org
    item = get_object_or_404(PriceItem, id=item_id, organization=org)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            if 'unit_price' in data:
                item.unit_price = Decimal(data['unit_price'])
            if 'discount_pct' in data:
                item.discount_pct = Decimal(data['discount_pct'])
            
            item.save()
            
            return JsonResponse({
                'success': True,
                'item': {
                    'id': str(item.id),
                    'unit_price': str(item.unit_price),
                    'discount_pct': str(item.discount_pct),
                }
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        item.delete()
        return JsonResponse({'success': True})
