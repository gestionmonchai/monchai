"""Vues pour la gestion des factures"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.accounts.decorators import require_membership
from apps.billing.models import Invoice, InvoiceLine
from apps.sales.models import Customer as SalesCustomer
from decimal import Decimal
from datetime import date, timedelta


@login_required
@require_membership('read_only')
def invoices_list(request):
    """Liste des factures"""
    org = request.current_org
    qs = Invoice.objects.filter(organization=org).select_related('customer').order_by('-date_issue')
    
    # Filtres
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '').strip()
    
    if search:
        qs = qs.filter(Q(number__icontains=search) | Q(customer__legal_name__icontains=search))
    if status:
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'ventes/invoices_list.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    })


@login_required
@require_membership('editor')
def invoice_create(request):
    """Création d'une facture"""
    org = request.current_org
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        
        try:
            customer = SalesCustomer.objects.get(id=customer_id, organization=org)
            
            # Générer le numéro de facture
            from apps.billing.managers import BillingManager
            number = BillingManager.generate_invoice_number(org)
            
            # Créer la facture
            invoice = Invoice.objects.create(
                organization=org,
                customer=customer,
                number=number,
                date_issue=date.today(),
                due_date=date.today() + timedelta(days=30),
                currency='EUR',
                status='draft',
                total_ht=Decimal('0'),
                total_tax=Decimal('0'),
                total_ttc=Decimal('0')
            )
            
            messages.success(request, f'Facture {number} créée avec succès.')
            return redirect('ventes:facture_detail', pk=invoice.id)
            
        except SalesCustomer.DoesNotExist:
            messages.error(request, 'Client introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    
    customers = SalesCustomer.objects.filter(organization=org, is_active=True).order_by('legal_name')
    
    return render(request, 'ventes/invoice_form.html', {
        'customers': customers,
        'mode': 'create',
    })


@login_required
@require_membership('read_only')
def invoice_detail(request, pk):
    """Détail d'une facture"""
    org = request.current_org
    invoice = get_object_or_404(Invoice, id=pk, organization=org)
    lines = invoice.lines.all().select_related('sku')
    
    return render(request, 'ventes/invoice_detail.html', {
        'invoice': invoice,
        'lines': lines,
    })
