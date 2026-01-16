from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from apps.produits.models_catalog import SKU, InventoryItem
from apps.partners.models import Partner as Customer

@login_required
def get_sku_details(request, pk):
    """
    Renvoie les détails d'un SKU pour remplissage formulaire (AJAX).
    """
    sku = get_object_or_404(SKU, pk=pk, organization=request.current_org)
    side = request.GET.get('side', 'sale')
    
    stock_qty = 0
    item = InventoryItem.objects.filter(sku=sku).first()
    if item:
        stock_qty = item.qty
        
    data = {
        'id': sku.pk,
        'name': str(sku),
        'description': str(sku), 
        'tax_rate': sku.product.vat_rate if sku.product else 20,
        'stock_qty': stock_qty,
        'stock': stock_qty,
        'unit_name': sku.unite.code if sku.unite else 'u'
    }
    
    if side == 'purchase':
        data['unit_price'] = 0
        data['price'] = 0
    else:
        price = sku.default_price_ht
        if not price and sku.product and sku.product.price_eur_u:
             price = sku.product.price_eur_u
        data['unit_price'] = float(price) if price else 0
        data['price'] = data['unit_price']
    
    return JsonResponse(data)


@login_required
def search_skus(request):
    """
    Recherche de produits pour l'autocomplétion dans l'éditeur de facture.
    Cherche dans Product (is_sellable=True) puis dans SKU.
    """
    from apps.produits.models_catalog import Product
    
    q = request.GET.get('q', '').strip()
    org = request.current_org
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Chercher d'abord dans les Products vendables
    products = Product.objects.filter(
        organization=org,
        is_active=True,
        is_sellable=True
    ).filter(
        Q(name__icontains=q) | 
        Q(slug__icontains=q) |
        Q(ean__icontains=q)
    ).select_related('unit')[:10]
    
    for p in products:
        results.append({
            'id': p.pk,
            'name': p.name,
            'code': p.ean or p.slug or '',
            'price': float(p.price_eur_u or 0),
            'tax_rate': float(p.vat_rate or 20),
            'stock': 0,  # TODO: récupérer stock réel
            'unit': p.unit.symbole if p.unit else 'u'
        })
    
    # Si pas assez de résultats, chercher aussi dans les SKUs
    if len(results) < 10:
        remaining = 10 - len(results)
        skus = SKU.objects.filter(
            organization=org,
            is_active=True
        ).filter(
            Q(name__icontains=q) | 
            Q(barcode__icontains=q) |
            Q(internal_ref__icontains=q) |
            Q(product__name__icontains=q)
        ).select_related('product', 'unite')[:remaining]
        
        for sku in skus:
            stock_qty = 0
            item = InventoryItem.objects.filter(sku=sku).first()
            if item:
                stock_qty = float(item.qty)
                
            results.append({
                'id': sku.pk,
                'name': str(sku),
                'code': sku.barcode or sku.internal_ref or '',
                'price': float(sku.default_price_ht or 0) if sku.default_price_ht else (float(sku.product.price_eur_u or 0) if sku.product else 0),
                'tax_rate': float(sku.product.vat_rate) if sku.product else 20,
                'stock': stock_qty,
                'unit': sku.unite.symbole if sku.unite else 'u'
            })
    
    return JsonResponse({'results': results})


@login_required
def search_clients(request):
    """
    Recherche de clients pour l'autocomplétion dans l'éditeur de facture.
    """
    q = request.GET.get('q', '').strip()
    org = request.current_org
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    clients = Customer.objects.filter(
        organization=org,
        is_active=True
    ).exclude(segment='supplier').filter(
        Q(name__icontains=q) | 
        Q(code__icontains=q) |
        Q(email__icontains=q)
    )[:10]
    
    results = []
    for client in clients:
        # Build initials from name
        initials = '?'
        if client.name:
            words = client.name.split()[:2]
            initials = ''.join([w[0].upper() for w in words if w])
        
        results.append({
            'id': str(client.pk),
            'name': client.name or '',
            'code': client.code or '',
            'email': client.email or '',
            'phone': client.phone or '',
            'address': getattr(client, 'country_code', '') or '',
            'segment': client.get_segment_display() if hasattr(client, 'get_segment_display') else client.segment,
            'initials': initials
        })
    
    return JsonResponse({'results': results})


@login_required
def get_client_details(request, pk):
    """
    Renvoie les détails d'un client avec son adresse de facturation.
    """
    client = get_object_or_404(Customer, pk=pk, organization=request.current_org)
    
    # Build initials from name
    initials = '?'
    if client.name:
        words = client.name.split()[:2]
        initials = ''.join([w[0].upper() for w in words if w])
    
    # Get billing address
    address_str = ''
    billing_addr = client.addresses.filter(address_type='billing', is_default=True).first()
    if not billing_addr:
        billing_addr = client.addresses.filter(address_type='billing').first()
    if not billing_addr:
        billing_addr = client.addresses.first()
    
    if billing_addr:
        parts = [billing_addr.street]
        if billing_addr.street2:
            parts.append(billing_addr.street2)
        parts.append(f"{billing_addr.postal_code} {billing_addr.city}")
        if billing_addr.country and billing_addr.country != 'FR':
            parts.append(billing_addr.country)
        address_str = ', '.join(parts)
    
    return JsonResponse({
        'id': str(client.pk),
        'name': client.name or '',
        'code': client.code or '',
        'email': client.email or '',
        'phone': client.phone or '',
        'address': address_str,
        'country': getattr(client, 'country_code', 'FR') or 'FR',
        'segment': client.segment or '',
        'vat_number': client.vat_number or '',
        'initials': initials
    })
