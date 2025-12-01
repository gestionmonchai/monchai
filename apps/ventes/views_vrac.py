"""Vues pour la vente en vrac"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.accounts.decorators import require_membership
from apps.sales.models import Quote, QuoteLine, Customer as SalesCustomer
from apps.viticulture.models import Lot
from decimal import Decimal
from datetime import date, timedelta


@login_required
@require_membership('read_only')
def vrac_list(request):
    """Liste des ventes en vrac"""
    org = request.current_org
    
    # Pour l'instant, on liste tous les devis
    # TODO: Ajouter champ is_vrac ou notes au modèle Quote
    qs = Quote.objects.filter(
        organization=org
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Filtres
    search = request.GET.get('search', '').strip()
    
    if search:
        qs = qs.filter(Q(customer__legal_name__icontains=search))
    
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'ventes/vrac_list.html', {
        'page_obj': page_obj,
        'search': search,
    })


@login_required
@require_membership('editor')
def vrac_create(request):
    """Création d'une vente en vrac"""
    org = request.current_org
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        lot_id = request.POST.get('lot')
        volume_l = request.POST.get('volume_l')
        
        try:
            customer = SalesCustomer.objects.get(id=customer_id, organization=org)
            
            # Créer le devis vrac
            # TODO: Ajouter champs notes au modèle Quote
            quote = Quote.objects.create(
                organization=org,
                customer=customer,
                currency='EUR',
                status='draft',
                valid_until=date.today() + timedelta(days=30),
                total_ht=Decimal('0'),
                total_tax=Decimal('0'),
                total_ttc=Decimal('0')
            )
            
            messages.success(request, f'Vente en vrac créée avec succès.')
            return redirect('ventes:vrac_detail', pk=quote.id)
            
        except SalesCustomer.DoesNotExist:
            messages.error(request, 'Client introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    
    customers = SalesCustomer.objects.filter(organization=org, is_active=True).order_by('legal_name')
    lots = Lot.objects.filter(organization=org).order_by('-created_at')[:50]
    
    return render(request, 'ventes/vrac_form.html', {
        'customers': customers,
        'lots': lots,
        'mode': 'create',
    })


@login_required
@require_membership('read_only')
def vrac_detail(request, pk):
    """Détail d'une vente en vrac"""
    org = request.current_org
    quote = get_object_or_404(Quote, id=pk, organization=org)
    lines = quote.lines.all().select_related('sku')
    
    return render(request, 'ventes/vrac_detail.html', {
        'quote': quote,
        'lines': lines,
    })
