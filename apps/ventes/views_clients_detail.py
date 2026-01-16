"""
Vues client pour le workbench VENTES (opérationnel)
Focus : Documents commerciaux (devis, commandes, factures, paiements)
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.accounts.decorators import require_membership
from apps.partners.models import Partner as Customer


@login_required
@require_membership('read_only')
def client_detail_ventes(request, display_id):
    """
    Fiche client orientée VENTES
    Focus : CA, encours, documents commerciaux (devis/commandes/factures)
    """
    organization = request.current_org
    customer = get_object_or_404(
        Customer.objects.select_related('organization'),
        display_id=display_id,
        organization=organization
    )
    
    # Onglet actif
    tab = request.GET.get('tab', 'overview')
    
    # === CALCUL KPIs VENTES ===
    now = timezone.now()
    year_ago = now - timedelta(days=365)
    
    # CA 12 derniers mois (depuis factures validées)
    try:
        from apps.commerce.models import Document
        invoices = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='invoice',
            status__in=['validated', 'paid'],
            date__gte=year_ago
        )
        ca_12m = invoices.aggregate(total=Sum('total_ttc'))['total'] or 0
        nb_factures = invoices.count()
        
        # Encours (factures validées non payées)
        encours = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='invoice',
            status='validated'
        ).aggregate(total=Sum('total_ttc'))['total'] or 0
        
        # Dernière commande
        last_order = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='order'
        ).order_by('-date').first()
        
        # Documents récents par onglet
        if tab == 'quotes':
            documents = Document.objects.filter(
                customer=customer,
                organization=organization,
                type='quote'
            ).order_by('-date')[:20]
        elif tab == 'orders':
            documents = Document.objects.filter(
                customer=customer,
                organization=organization,
                type='order'
            ).order_by('-date')[:20]
        elif tab == 'invoices':
            documents = Document.objects.filter(
                customer=customer,
                organization=organization,
                type='invoice'
            ).order_by('-date')[:20]
        else:
            # Overview : mix des derniers documents
            documents = Document.objects.filter(
                customer=customer,
                organization=organization,
                type__in=['quote', 'order', 'invoice']
            ).order_by('-date')[:15]
        
    except ImportError:
        # Fallback si module commerce pas encore disponible
        ca_12m = 0
        encours = 0
        nb_factures = 0
        last_order = None
        documents = []
    
    # Panier moyen
    panier_moyen = (ca_12m / nb_factures) if nb_factures > 0 else 0
    
    context = {
        'page_title': f'Client - {customer.name} (Ventes)',
        'customer': customer,
        'tab': tab,
        'documents': documents,
        'kpis': {
            'ca_12m': ca_12m,
            'encours': encours,
            'nb_factures': nb_factures,
            'panier_moyen': panier_moyen,
            'last_order_date': last_order.date if last_order else None,
        },
    }
    
    return render(request, 'ventes/client_detail.html', context)


@login_required
@require_membership('read_only')
def client_quotes_ventes(request, display_id):
    """Liste des devis du client (contexte ventes)"""
    organization = request.current_org
    customer = get_object_or_404(Customer, display_id=display_id, organization=organization)
    
    try:
        from apps.commerce.models import Document
        quotes = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='quote'
        ).order_by('-date')
    except ImportError:
        quotes = []
    
    context = {
        'page_title': f'Devis - {customer.name}',
        'customer': customer,
        'quotes': quotes,
    }
    return render(request, 'ventes/client_quotes.html', context)


@login_required
@require_membership('read_only')
def client_orders_ventes(request, display_id):
    """Liste des commandes du client (contexte ventes)"""
    organization = request.current_org
    customer = get_object_or_404(Customer, display_id=display_id, organization=organization)
    
    try:
        from apps.commerce.models import Document
        orders = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='order'
        ).order_by('-date')
    except ImportError:
        orders = []
    
    context = {
        'page_title': f'Commandes - {customer.name}',
        'customer': customer,
        'orders': orders,
    }
    return render(request, 'ventes/client_orders.html', context)


@login_required
@require_membership('read_only')
def client_invoices_ventes(request, display_id):
    """Liste des factures du client (contexte ventes)"""
    organization = request.current_org
    customer = get_object_or_404(Customer, code=code, organization=organization)
    
    try:
        from apps.commerce.models import Document
        invoices = Document.objects.filter(
            customer=customer,
            organization=organization,
            type='invoice'
        ).order_by('-date')
    except ImportError:
        invoices = []
    
    context = {
        'page_title': f'Factures - {customer.name}',
        'customer': customer,
        'invoices': invoices,
    }
    return render(request, 'ventes/client_invoices.html', context)
