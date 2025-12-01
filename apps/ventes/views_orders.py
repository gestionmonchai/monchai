"""Vues pour la gestion des commandes"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.accounts.decorators import require_membership
from apps.sales.models import Order, OrderLine, Customer as SalesCustomer
from decimal import Decimal


@login_required
@require_membership('read_only')
def orders_list(request):
    """Liste des commandes"""
    org = request.current_org
    qs = Order.objects.filter(organization=org).select_related('customer').order_by('-created_at')
    
    # Filtres
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '').strip()
    
    if search:
        qs = qs.filter(Q(customer__legal_name__icontains=search))
    if status:
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'ventes/orders_list.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    })


@login_required
@require_membership('editor')
def order_create(request):
    """Création d'une commande"""
    org = request.current_org
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        
        try:
            customer = SalesCustomer.objects.get(id=customer_id, organization=org)
            
            # Créer la commande
            order = Order.objects.create(
                organization=org,
                customer=customer,
                currency='EUR',
                status='draft',
                payment_status='unpaid',
                total_ht=Decimal('0'),
                total_tax=Decimal('0'),
                total_ttc=Decimal('0')
            )
            
            messages.success(request, f'Commande créée avec succès.')
            return redirect('ventes:cmd_detail', pk=order.id)
            
        except SalesCustomer.DoesNotExist:
            messages.error(request, 'Client introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    
    customers = SalesCustomer.objects.filter(organization=org, is_active=True).order_by('legal_name')
    
    return render(request, 'ventes/order_form.html', {
        'customers': customers,
        'mode': 'create',
    })


@login_required
@require_membership('read_only')
def order_detail(request, pk):
    """Détail d'une commande"""
    org = request.current_org
    order = get_object_or_404(Order, id=pk, organization=org)
    lines = order.lines.all().select_related('sku')
    
    return render(request, 'ventes/order_detail.html', {
        'order': order,
        'lines': lines,
    })
