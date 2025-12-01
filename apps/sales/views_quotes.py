from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages

from apps.accounts.decorators import require_membership
from apps.sales.models import Quote, QuoteLine, TaxCode, Customer as SalesCustomer
from django.views.decorators.http import require_http_methods
from django.forms.models import model_to_dict
import json
from .forms_quotes import QuoteForm, QuoteLineFormSet


def _ensure_default_tax_codes(organization):
    if not TaxCode.objects.filter(organization=organization).exists():
        TaxCode.objects.create(
            organization=organization,
            code='TVA20', name='TVA 20%', rate_pct='20.00', country='FR', is_active=True
        )
        TaxCode.objects.create(
            organization=organization,
            code='TVA10', name='TVA 10%', rate_pct='10.00', country='FR', is_active=True
        )
        TaxCode.objects.create(
            organization=organization,
            code='TVA0', name='TVA 0%', rate_pct='0.00', country='FR', is_active=True
        )


@login_required
@require_membership('read_only')
def quotes_list(request):
    org = request.current_org
    base_qs = Quote.objects.filter(organization=org).select_related('customer')
    total_count = base_qs.count()
    qs = base_qs

    # Filters
    search = (request.GET.get('search') or '').strip()
    status = (request.GET.get('status') or '').strip()
    date_from = (request.GET.get('date_from') or '').strip()
    date_to = (request.GET.get('date_to') or '').strip()

    if search:
        qs = qs.filter(
            Q(customer__legal_name__icontains=search) |
            Q(id__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    qs = qs.order_by('-created_at', '-id')

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'filters': {
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        },
        'stats': {
            'total': total_count,
            'filtered': qs.count(),
        },
    }
    return render(request, 'ventes/devis_list.html', context)


@login_required
@require_membership('read_only')
def quotes_search_ajax(request):
    if request.method != 'GET' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    org = request.current_org
    base_qs = Quote.objects.filter(organization=org).select_related('customer')
    total_count = base_qs.count()
    qs = base_qs

    search = (request.GET.get('search') or '').strip()
    status = (request.GET.get('status') or '').strip()
    date_from = (request.GET.get('date_from') or '').strip()
    date_to = (request.GET.get('date_to') or '').strip()

    if search:
        qs = qs.filter(
            Q(customer__legal_name__icontains=search) |
            Q(id__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    qs = qs.order_by('-created_at', '-id')

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    table_html = render(request, 'ventes/partials/quote_table_rows.html', {
        'quotes': page_obj,
    }).content.decode('utf-8')

    pagination_html = render(request, 'ventes/partials/quote_pagination.html', {
        'page_obj': page_obj,
    }).content.decode('utf-8')

    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': total_count,
            'filtered': qs.count(),
        }
    })


@login_required
@require_membership('editor')
def quote_create(request):
    org = request.current_org
    _ensure_default_tax_codes(org)

    if request.method == 'POST':
        form = QuoteForm(request.POST, organization=org)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.organization = org
            quote.save()

            formset = QuoteLineFormSet(request.POST, instance=quote, form_kwargs={'organization': org})
            if formset.is_valid():
                lines = formset.save(commit=False)
                for line in lines:
                    line.organization = org
                    line.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                quote.calculate_totals()
                quote.save()
                messages.success(request, 'Devis créé avec succès.')
                return redirect('ventes:devis_detail', quote_id=quote.id)
            else:
                # If lines invalid, re-render with errors
                messages.error(request, 'Veuillez corriger les erreurs dans les lignes du devis.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire du devis.')
    else:
        form = QuoteForm(organization=org)
        formset = QuoteLineFormSet(instance=Quote(organization=org), form_kwargs={'organization': org})

    return render(request, 'ventes/devis_form.html', {
        'form': form,
        'formset': formset,
        'mode': 'create',
    })


@login_required
@require_membership('read_only')
def quote_detail(request, quote_id):
    org = request.current_org
    quote = get_object_or_404(Quote.objects.select_related('customer'), id=quote_id, organization=org)
    lines = quote.lines.all().select_related('sku', 'tax_code')
    return render(request, 'ventes/devis_detail.html', {
        'quote': quote,
        'lines': lines,
    })


@login_required
@require_membership('editor')
def quote_edit(request, quote_id):
    org = request.current_org
    quote = get_object_or_404(Quote, id=quote_id, organization=org)
    _ensure_default_tax_codes(org)

    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote, organization=org)
        formset = QuoteLineFormSet(request.POST, instance=quote, form_kwargs={'organization': org})
        if form.is_valid() and formset.is_valid():
            form.save()
            lines = formset.save(commit=False)
            for line in lines:
                line.organization = org
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            quote.calculate_totals()
            quote.save()
            messages.success(request, 'Devis mis à jour avec succès.')
            return redirect('ventes:devis_detail', quote_id=quote.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = QuoteForm(instance=quote, organization=org)
        formset = QuoteLineFormSet(instance=quote, form_kwargs={'organization': org})

    return render(request, 'ventes/devis_form.html', {
        'form': form,
        'formset': formset,
        'mode': 'edit',
        'quote': quote,
    })


@login_required
@require_membership('read_only')
@require_http_methods(["GET"])
def sales_customers_suggestions_api(request):
    """Suggestions pour les clients (modèle SalesCustomer) pour autocomplétion Devis."""
    org = request.current_org
    q = (request.GET.get('q') or '').strip()
    try:
        limit = min(int(request.GET.get('limit', 10)), 50)
    except Exception:
        limit = 10

    qs = SalesCustomer.objects.filter(organization=org, is_active=True)
    if q:
        qs = qs.filter(
            Q(legal_name__icontains=q) |
            Q(billing_city__icontains=q) |
            Q(billing_postal_code__icontains=q)
        )
    qs = qs.order_by('legal_name')[:limit]
    
    # Enrichir les données retournées
    items = []
    for c in qs:
        type_display = dict(SalesCustomer.CUSTOMER_TYPES).get(c.type, c.type)
        items.append({
            'id': str(c.id),
            'name': c.legal_name,
            'type': type_display,
            'city': c.billing_city or '',
            'postal_code': c.billing_postal_code or '',
        })
    
    return JsonResponse({'success': True, 'suggestions': items, 'query': q})


@login_required
@require_membership('editor')
@require_http_methods(["POST"])
def sales_customers_quick_create_api(request):
    """Création rapide d'un client (SalesCustomer) depuis une modale du Devis."""
    org = request.current_org
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': {'__all__': 'JSON invalide'}}, status=400)

    legal_name = (payload.get('legal_name') or '').strip()
    ctype = (payload.get('type') or 'part').strip()
    billing_address = (payload.get('billing_address') or '').strip()
    billing_postal_code = (payload.get('billing_postal_code') or '').strip()
    billing_city = (payload.get('billing_city') or '').strip()
    billing_country = (payload.get('billing_country') or 'FR').strip()

    errors = {}
    if not legal_name:
        errors['legal_name'] = 'Nom requis'
    if not billing_address:
        errors['billing_address'] = 'Adresse requise'
    if not billing_postal_code:
        errors['billing_postal_code'] = 'Code postal requis'
    if not billing_city:
        errors['billing_city'] = 'Ville requise'
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    customer = SalesCustomer(
        organization=org,
        type=ctype if ctype in dict(SalesCustomer.CUSTOMER_TYPES) else 'part',
        legal_name=legal_name,
        billing_address=billing_address,
        billing_postal_code=billing_postal_code,
        billing_city=billing_city,
        billing_country=billing_country or 'FR',
        shipping_address='',
        shipping_postal_code='',
        shipping_city='',
        shipping_country='',
        payment_terms='30j',
        currency='EUR',
        is_active=True,
    )
    try:
        customer.full_clean()
        customer.save()
        return JsonResponse({'success': True, 'customer': {'id': str(customer.id), 'name': customer.legal_name}})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'__all__': str(e)}}, status=400)
