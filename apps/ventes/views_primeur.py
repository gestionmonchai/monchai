"""Vues pour la vente en primeur"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.accounts.decorators import require_membership
from apps.sales.models import Quote, QuoteLine, Customer as SalesCustomer
from decimal import Decimal
from datetime import date, timedelta


@login_required
@require_membership('read_only')
def primeur_list(request):
    """Liste des ventes en primeur"""
    org = request.current_org
    
    # Pour l'instant, on liste tous les devis
    # TODO: Ajouter champ is_primeur au modèle Quote
    qs = Quote.objects.filter(
        organization=org
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Filtres
    search = request.GET.get('search', '').strip()
    vintage = request.GET.get('vintage', '').strip()
    
    if search:
        qs = qs.filter(Q(customer__legal_name__icontains=search))
    if vintage:
        qs = qs.filter(vintage_year=vintage)
    
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Millésimes disponibles pour filtre
    # TODO: Ajouter champ vintage_year au modèle Quote
    vintages = []
    
    return render(request, 'ventes/primeur_list.html', {
        'page_obj': page_obj,
        'search': search,
        'vintage': vintage,
        'vintages': vintages,
    })


@login_required
@require_membership('editor')
def primeur_create(request):
    """Création d'une vente en primeur"""
    org = request.current_org
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        vintage_year = request.POST.get('vintage_year')
        primeur_campaign = request.POST.get('primeur_campaign', '')
        expected_delivery = request.POST.get('expected_delivery')
        
        try:
            customer = SalesCustomer.objects.get(id=customer_id, organization=org)
            
            # Créer le devis primeur
            # TODO: Ajouter champs spécifiques primeur au modèle
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
            
            messages.success(request, f'Vente en primeur créée avec succès (Millésime {vintage_year}).')
            return redirect('ventes:primeur_detail', pk=quote.id)
            
        except SalesCustomer.DoesNotExist:
            messages.error(request, 'Client introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    
    customers = SalesCustomer.objects.filter(organization=org, is_active=True).order_by('legal_name')
    
    # Années disponibles (année courante + 2 années suivantes)
    current_year = date.today().year
    years = [current_year, current_year + 1, current_year + 2]
    
    return render(request, 'ventes/primeur_form.html', {
        'customers': customers,
        'years': years,
        'mode': 'create',
    })


@login_required
@require_membership('read_only')
def primeur_detail(request, pk):
    """Détail d'une vente en primeur"""
    org = request.current_org
    quote = get_object_or_404(Quote, id=pk, organization=org)
    lines = quote.lines.all().select_related('sku')
    
    return render(request, 'ventes/primeur_detail.html', {
        'quote': quote,
        'lines': lines,
    })
