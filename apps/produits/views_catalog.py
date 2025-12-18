from __future__ import annotations
from typing import Dict, Any

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models_catalog import Product, SKU, InventoryItem
from apps.viticulture.models import Cuvee
from decimal import Decimal
from .models import LotCommercial
from .forms_catalog import (
    ProductForm, SKUForm, 
    PurchaseArticleForm, SalesArticleForm,
    BridgePurchaseToSalesForm, BridgeSalesToPurchaseForm
)


@method_decorator(login_required, name='dispatch')
class PurchaseArticleCreateView(View):
    """
    Étape 1 Achat : Création d'un article depuis le menu Achats.
    """
    def get(self, request):
        form = PurchaseArticleForm()
        return render(request, 'produits/purchase_article_form.html', {
            'form': form,
            'page_title': 'Nouvel article d\'achat',
            'step': 1
        })

    def post(self, request):
        form = PurchaseArticleForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            org = getattr(request, 'current_org', None)
            if not org and hasattr(request.user, 'get_active_membership'):
                m = request.user.get_active_membership()
                org = getattr(m, 'organization', None)
            product.organization = org
            
            # Using form.save() to handle Profile creation transactionally if possible
            # But we need organization set on product before saving.
            # PurchaseArticleForm.save() does product.save() then profile creation.
            # So we set organization on the instance before calling form.save()
            
            # Re-bind form with instance having org? No, just set it on instance.
            form.instance.organization = org
            try:
                product = form.save()
                messages.success(request, f"Article \"{product.name}\" créé avec succès.")
                return redirect('produits:purchase_success', slug=product.slug)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")
        
        return render(request, 'produits/purchase_article_form.html', {
            'form': form,
            'page_title': 'Nouvel article d\'achat',
            'step': 1
        })


@method_decorator(login_required, name='dispatch')
class PurchaseArticleSuccessView(View):
    """
    Étape 2 Achat : "Et maintenant ?" - Passerelle vers Vente.
    """
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        return render(request, 'produits/purchase_article_success.html', {
            'product': product,
            'page_title': 'Article créé',
            'step': 2
        })


@method_decorator(login_required, name='dispatch')
class BridgePurchaseToSalesView(View):
    """
    Passerelle : Création du profil Vente pour un article Achat existant.
    """
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        form = BridgePurchaseToSalesForm(product=product)
        return render(request, 'produits/bridge_purchase_to_sales.html', {
            'form': form,
            'product': product,
            'page_title': 'Configurer pour la revente'
        })

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        form = BridgePurchaseToSalesForm(request.POST, product=product)
        if form.is_valid():
            form.save(product=product)
            messages.success(request, "Profil de vente activé avec succès.")
            # Redirect to Sales list or Detail? User request: "l’article apparaît immédiatement dans le menu Ventes"
            return redirect('produits:product_detail', slug=product.slug)
        
        return render(request, 'produits/bridge_purchase_to_sales.html', {
            'form': form,
            'product': product,
            'page_title': 'Configurer pour la revente'
        })


@method_decorator(login_required, name='dispatch')
class SalesArticleCreateView(View):
    """
    Étape 1 Vente : Création d'un article depuis le menu Ventes.
    """
    def get(self, request):
        form = SalesArticleForm()
        return render(request, 'produits/sales_article_form.html', {
            'form': form,
            'page_title': 'Nouvel article de vente',
            'step': 1
        })

    def post(self, request):
        form = SalesArticleForm(request.POST)
        if form.is_valid():
            org = getattr(request, 'current_org', None)
            if not org and hasattr(request.user, 'get_active_membership'):
                m = request.user.get_active_membership()
                org = getattr(m, 'organization', None)
            form.instance.organization = org
            
            try:
                product = form.save()
                messages.success(request, f"Article \"{product.name}\" créé avec succès.")
                return redirect('produits:sales_success', slug=product.slug)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")
        
        return render(request, 'produits/sales_article_form.html', {
            'form': form,
            'page_title': 'Nouvel article de vente',
            'step': 1
        })


@method_decorator(login_required, name='dispatch')
class SalesArticleSuccessView(View):
    """
    Étape 2 Vente : "Source de cet article" - Passerelle vers Achat.
    """
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        # Determine logic based on product properties set in step 1
        needs_purchase_profile = (product.source_mode in ['negoce_bout', 'negoce_vrac'])
        
        return render(request, 'produits/sales_article_success.html', {
            'product': product,
            'needs_purchase_profile': needs_purchase_profile,
            'page_title': 'Article créé',
            'step': 2
        })


@method_decorator(login_required, name='dispatch')
class BridgeSalesToPurchaseView(View):
    """
    Passerelle : Création du profil Achat pour un article Vente existant.
    """
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        form = BridgeSalesToPurchaseForm(product=product)
        return render(request, 'produits/bridge_sales_to_purchase.html', {
            'form': form,
            'product': product,
            'page_title': 'Configurer l\'approvisionnement'
        })

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        form = BridgeSalesToPurchaseForm(request.POST, product=product)
        if form.is_valid():
            form.save(product=product)
            messages.success(request, "Profil d'achat activé avec succès.")
            return redirect('produits:product_detail', slug=product.slug)
        
        return render(request, 'produits/bridge_sales_to_purchase.html', {
            'form': form,
            'product': product,
            'page_title': 'Configurer l\'approvisionnement'
        })


@method_decorator(login_required, name='dispatch')
class ProductListView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        type_code = request.GET.get('type', '').strip()
        qs = Product.objects.all().select_related('cuvee').only(
            'id', 'name', 'brand', 'slug', 'type_code', 'is_active', 'cuvee__name'
        )
        # Multi-tenant isolation when available
        org = getattr(request, 'current_org', None)
        if org:
            qs = qs.filter(organization=org)
        if q:
            qs = qs.filter(name__icontains=q)
        if type_code:
            qs = qs.filter(type_code=type_code)
        qs = qs.order_by('name')
        paginator = Paginator(qs, 50)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'produits/catalog_list.html', {
            'page_title': 'Catalogue produits',
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': None},
            ],
            'products': page_obj,
            'q': q,
            'type': type_code,
        })


@method_decorator(login_required, name='dispatch')
class ProductCreateView(View):
    def get(self, request):
        form = ProductForm()
        return render(request, 'produits/product_form.html', {
            'form': form,
            'page_title': 'Nouveau produit',
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': '/produits/catalogue/'},
                {'name': 'Nouveau', 'url': None},
            ],
        })

    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        # Soft validation for Domaine sourcing: at least one cuvée and ~100% sum
        source_mode = (request.POST.get('source_mode') or '').strip()
        sc_cuvees = request.POST.getlist('sc_cuvee')
        sc_ratios = request.POST.getlist('sc_ratio')
        domain_ok = True
        if source_mode == 'domaine':
            if not sc_cuvees:
                domain_ok = False
                messages.error(request, "Au moins une ligne de cuvée est requise pour le sourcing Domaine.")
            # Sum ratios tolerance ±0.5
            total = Decimal('0')
            for r in sc_ratios:
                try:
                    total += Decimal(str(r or '0'))
                except Exception:
                    pass
            if total and (total < Decimal('99.5') or total > Decimal('100.5')):
                domain_ok = False
                messages.error(request, f"La somme des ratios doit être ~100% (actuel: {total}%).")

        if form.is_valid() and domain_ok:
            product: Product = form.save(commit=False)
            # Assign organization from context
            org = getattr(request, 'current_org', None)
            if not org and hasattr(request.user, 'get_active_membership'):
                m = request.user.get_active_membership()
                org = getattr(m, 'organization', None)
            product.organization = org
            # Server-side validation per model clean()
            try:
                product.full_clean()
            except ValidationError as e:
                for field, errs in getattr(e, 'message_dict', {}).items():
                    for msg in (errs if isinstance(errs, (list, tuple)) else [errs]):
                        form.add_error(field, msg)
                return render(request, 'produits/product_form.html', {
                    'form': form,
                    'page_title': 'Nouveau produit',
                })
            product.save()

            # Persist Domaine sourcing lines if any
            if source_mode == 'domaine' and sc_cuvees:
                from .models import ProductSourcingCuvee
                for cuv_id, ratio in zip(sc_cuvees, sc_ratios):
                    cuv_id = (cuv_id or '').strip()
                    if not cuv_id:
                        continue
                    try:
                        c = Cuvee.objects.get(id=cuv_id, organization=org)
                    except Cuvee.DoesNotExist:
                        continue
                    try:
                        ratio_d = Decimal(str(ratio or '0'))
                    except Exception:
                        ratio_d = Decimal('0')
                    ProductSourcingCuvee.objects.create(product=product, cuvee=c, ratio_pct=ratio_d)

            messages.success(request, 'Produit créé')
            return redirect('produits:product_detail', slug=product.slug)
        return render(request, 'produits/product_form.html', {
            'form': form,
            'page_title': 'Nouveau produit',
        })


@login_required
def product_panels_partial(request):
    """HTMX partial: render type-specific panels based on product_type."""
    # Determine selected type from POST (form include)
    form = ProductForm(request.POST or None)
    ptype = (request.POST.get('product_type') or getattr(form.instance, 'product_type', None) or 'vin')
    return render(request, 'produits/_product_panels.html', {
        'form': form,
        'ptype': ptype,
    })


@login_required
def product_source_partial(request):
    """HTMX partial: render source panel by mode."""
    mode = (request.GET.get('mode') or request.POST.get('source_mode') or 'domaine').strip()
    org = getattr(request, 'current_org', None)
    if mode == 'domaine':
        cuvees = Cuvee.objects.filter(organization=org, is_active=True).order_by('name')[:500]
        # Derive next index from posted rows count
        next_idx = max(0, len(request.POST.getlist('sc_cuvee')))
        return render(request, 'produits/_product_source_domaine.html', {
            'cuvees': cuvees,
            'next_idx': next_idx,
        })
    elif mode == 'negoce_vrac':
        return render(request, 'produits/_product_source_vrac.html')
    elif mode == 'negoce_bout':
        return render(request, 'produits/_product_source_bottle.html')
    else:
        return render(request, 'produits/_product_source_libre.html')


@login_required
def product_source_cuvee_add(request):
    """Return one Domaine source row for HTMX append."""
    org = getattr(request, 'current_org', None)
    cuvees = Cuvee.objects.filter(organization=org, is_active=True).order_by('name')[:500]
    try:
        idx = int(request.GET.get('idx', '0'))
    except Exception:
        idx = 0
    return render(request, 'produits/partials/_source_cuvee_row.html', {
        'cuvees': cuvees,
        'idx': idx,
    })


@login_required
def product_source_cuvee_del(request, row_id: int):
    """Placeholder endpoint if needed; client-side removal preferred."""
    # Return 204 No Content so HTMX can remove the element if configured
    return redirect('produits:source_partial')


@method_decorator(login_required, name='dispatch')
class ProductUpdateView(View):
    def get(self, request, slug: str):
        product = get_object_or_404(Product, slug=slug)
        form = ProductForm(instance=product)
        return render(request, 'produits/product_form.html', {
            'form': form,
            'product': product,
            'page_title': f"Modifier {product.name}",
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': '/produits/catalogue/'},
                {'name': product.name, 'url': f"/produits/catalogue/{product.slug}/"},
                {'name': 'Modifier', 'url': None},
            ],
        })

    def post(self, request, slug: str):
        product = get_object_or_404(Product, slug=slug)
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit mis à jour')
            return redirect('produits:product_detail', slug=product.slug)
        return render(request, 'produits/product_form.html', {'form': form, 'product': product})


@method_decorator(login_required, name='dispatch')
class SKUUpdateView(View):
    def get(self, request, pk):
        sku = get_object_or_404(SKU, pk=pk)
        form = SKUForm(instance=sku)
        return render(request, 'produits/sku_form.html', {
            'form': form,
            'sku': sku,
            'page_title': f"Modifier SKU {sku.name}",
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': '/produits/catalogue/'},
                {'name': sku.product.name, 'url': f"/produits/catalogue/{sku.product.slug}/"},
                {'name': 'Modifier SKU', 'url': None},
            ],
        })

    def post(self, request, pk):
        sku = get_object_or_404(SKU, pk=pk)
        form = SKUForm(request.POST, instance=sku)
        if form.is_valid():
            form.save()
            messages.success(request, 'SKU mis à jour')
            return redirect('produits:product_detail', slug=sku.product.slug)
        return render(request, 'produits/sku_form.html', {'form': form, 'sku': sku})


@method_decorator(login_required, name='dispatch')
class ProductDetailView(View):
    def get(self, request, slug: str):
        org = getattr(request, 'current_org', None)
        base_qs = Product.objects.select_related('cuvee')
        if org:
            base_qs = base_qs.filter(organization=org)
        product = get_object_or_404(base_qs, slug=slug)
        skus_qs = SKU.objects.filter(product=product).select_related('unite')
        if org:
            skus_qs = skus_qs.filter(organization=org)
        skus = list(skus_qs)

        stock_by_sku: Dict[str, int] = {}
        if product.type_code == 'wine' and product.cuvee_id:
            # Aggregate LotCommercial per format_ml then map to SKU.normalized_ml
            agg = (
                LotCommercial.objects
                .filter(cuvee_id=product.cuvee_id)
                .values('format_ml')
                .annotate(total=Sum('stock_disponible'))
            )
            by_format = {row['format_ml']: int(row['total'] or 0) for row in agg}
            for sku in skus:
                key = sku.normalized_ml
                val = by_format.get(key or -1, 0)
                stock_by_sku[str(sku.id)] = val
                setattr(sku, 'stock', val)
        else:
            # Sum InventoryItem.qty by SKU
            inv_qs = InventoryItem.objects.filter(sku__in=skus)
            if org:
                inv_qs = inv_qs.filter(organization=org)
            inv = inv_qs.values('sku_id').annotate(total=Sum('qty'))
            inv_map = {str(row['sku_id']): int(row['total'] or 0) for row in inv}
            for sku in skus:
                val = inv_map.get(str(sku.id), 0)
                stock_by_sku[str(sku.id)] = val
                setattr(sku, 'stock', val)

        return render(request, 'produits/product_detail.html', {
            'product': product,
            'skus': skus,
            'stock_by_sku': stock_by_sku,
            'sku_form': SKUForm(),
            'page_title': product.name,
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': '/produits/catalogue/'},
                {'name': product.name, 'url': None},
            ],
        })

    def post(self, request, slug: str):
        """Quick add SKU from product detail."""
        org = getattr(request, 'current_org', None)
        base_qs = Product.objects
        if org:
            base_qs = base_qs.filter(organization=org)
        product = get_object_or_404(base_qs, slug=slug)

        form = SKUForm(request.POST)
        if form.is_valid():
            sku: SKU = form.save(commit=False)
            # Assign org and product
            if not org and hasattr(request.user, 'get_active_membership'):
                m = request.user.get_active_membership()
                org = getattr(m, 'organization', None)
            sku.organization = org
            sku.product = product
            sku.save()
            messages.success(request, 'SKU ajouté')
            return redirect('produits:product_detail', slug=product.slug)

        # If invalid, re-render with errors
        skus = list(SKU.objects.filter(product=product).select_related('unite'))
        stock_by_sku: Dict[str, int] = {}
        # Keep stock computation simple on error page (no aggregation to avoid duplication)
        return render(request, 'produits/product_detail.html', {
            'product': product,
            'skus': skus,
            'stock_by_sku': stock_by_sku,
            'sku_form': form,
            'page_title': product.name,
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Catalogue', 'url': '/produits/catalogue/'},
                {'name': product.name, 'url': None},
            ],
        })
