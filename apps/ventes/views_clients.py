"""Vues client pour l'espace Ventes"""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import require_membership
from apps.partners.models import Partner as Customer


@login_required
@require_membership('read_only')
def clients_dashboard(request):
    """Vue principale clients côté Ventes"""
    organization = request.current_org

    query = request.GET.get('q', '').strip()
    segment = request.GET.get('segment', '').strip()
    status = request.GET.get('status', 'active').strip()
    sort = request.GET.get('sort', 'name_asc').strip() or 'name_asc'

    base_qs = Customer.objects.filter(organization=organization)

    customers_qs = base_qs
    if status == 'active':
        customers_qs = customers_qs.filter(is_active=True)
    elif status == 'inactive':
        customers_qs = customers_qs.filter(is_active=False)

    if segment and segment in dict(Customer.SEGMENT_CHOICES):
        customers_qs = customers_qs.filter(segment=segment)

    if query:
        customers_qs = customers_qs.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(vat_number__icontains=query)
        )

    if sort == 'name_desc':
        customers_qs = customers_qs.order_by('-name')
    elif sort == 'created_desc':
        customers_qs = customers_qs.order_by('-created_at')
    elif sort == 'created_asc':
        customers_qs = customers_qs.order_by('created_at')
    elif sort == 'recent_update':
        customers_qs = customers_qs.order_by('-updated_at')
    else:
        customers_qs = customers_qs.order_by('name')

    paginator = Paginator(customers_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Stats
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_clients = base_qs.count()
    active_clients = base_qs.filter(is_active=True).count()
    new_this_month = base_qs.filter(created_at__gte=month_start).count()

    segment_breakdown = (
        base_qs.values('segment')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    # Map choices for display
    segment_labels = dict(Customer.SEGMENT_CHOICES)
    segment_data = [
        {
            'key': entry['segment'],
            'label': segment_labels.get(entry['segment'], entry['segment']),
            'count': entry['count'],
            'percent': round(
                (entry['count'] / total_clients * 100) if total_clients else 0
            ),
        }
        for entry in segment_breakdown
    ]

    recent_updates = base_qs.order_by('-updated_at')[:5]

    active_percent = round(
        (active_clients / total_clients * 100) if total_clients else 0
    )

    context = {
        'page_title': 'Clients Ventes',
        'page_obj': page_obj,
        'filters': {
            'query': query,
            'segment': segment,
            'status': status,
            'sort': sort,
        },
        'stats': {
            'total': total_clients,
            'active': active_clients,
            'new_this_month': new_this_month,
            'active_percent': active_percent,
            'segments_count': len(segment_data),
        },
        'segments': segment_data,
        'recent_updates': recent_updates,
        'segment_choices': Customer.SEGMENT_CHOICES,
        'now': now,
    }

    return render(request, 'ventes/clients_dashboard.html', context)
