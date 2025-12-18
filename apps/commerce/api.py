from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.produits.models_catalog import SKU, InventoryItem

@login_required
def get_sku_details(request, pk):
    """
    Renvoie les détails d'un SKU pour remplissage formulaire (AJAX).
    """
    sku = get_object_or_404(SKU, pk=pk, organization=request.user.organization)
    side = request.GET.get('side', 'sale') # 'sale' ou 'purchase'
    
    # Récupérer le stock
    stock_qty = 0
    item = InventoryItem.objects.filter(sku=sku).first()
    if item:
        stock_qty = item.qty
        
    data = {
        'description': str(sku), 
        'tax_rate': sku.product.vat_rate,
        'stock_qty': stock_qty,
        'unit_name': sku.unite.code if sku.unite else 'u'
    }
    
    # Gestion du prix par défaut
    if side == 'purchase':
        # En achat, on ne pré-remplit pas avec le prix de vente !
        # Idéalement on aurait un "last_purchase_price" ou "cost_price"
        data['unit_price'] = 0
    else:
        # En vente, on prend le prix de vente
        price = sku.default_price_ht
        if not price and sku.product.price_eur_u:
             price = sku.product.price_eur_u
        data['unit_price'] = price
    
    return JsonResponse(data)
