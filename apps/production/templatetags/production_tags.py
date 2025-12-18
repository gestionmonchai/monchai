"""
Template tags for production module sidebar stats.
"""
from django import template
from django.db.models import Sum, Count
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.simple_tag(takes_context=True)
def get_lots_fermentation_count(context):
    """
    Count of lots in fermentation stages.
    """
    from ..models import LotTechnique
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    fermenting_statuses = [
        'MOUT_ENCUVE', 'MOUT_PRESSE', 'MOUT_DEBOURBE', 
        'VIN_EN_FA', 'VIN_POST_FA', 'VIN_EN_FML', 'VIN_POST_FML'
    ]
    return LotTechnique.objects.filter(
        cuvee__organization=org, 
        statut__in=fermenting_statuses
    ).count()


@register.simple_tag(takes_context=True)
def get_lots_elevage_count(context):
    """
    Count of lots in élevage stages.
    """
    from ..models import LotTechnique
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    elevage_statuses = [
        'VIN_ELEVAGE', 'VIN_STABILISE', 'VIN_FILTRATION_STERILE', 
        'VIN_PRET_MISE', 'stabilise', 'pret_mise', 'en_cours'
    ]
    return LotTechnique.objects.filter(
        cuvee__organization=org, 
        statut__in=elevage_statuses
    ).count()


@register.simple_tag(takes_context=True)
def get_lots_total_count(context):
    """
    Count of all active lots.
    """
    from ..models import LotTechnique
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    active_statuses = [
        'en_cours', 'stabilise', 'pret_mise', 'MOUT_ENCUVE', 'MOUT_PRESSE', 
        'MOUT_DEBOURBE', 'VIN_EN_FA', 'VIN_POST_FA', 'VIN_EN_FML', 
        'VIN_POST_FML', 'VIN_ELEVAGE', 'VIN_STABILISE', 'VIN_FILTRATION_STERILE', 
        'VIN_PRET_MISE', 'BASE_EFF', 'SUR_LATTES', 'DEGORGEMENT'
    ]
    return LotTechnique.objects.filter(
        cuvee__organization=org, 
        statut__in=active_statuses
    ).count()


@register.simple_tag(takes_context=True)
def get_vendanges_count(context):
    """
    Count of active vendanges (not closed).
    """
    from ..models import VendangeReception
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return VendangeReception.objects.filter(
        organization=org
    ).exclude(statut='close').count()


# ============================================================
# ALERT COUNTS
# ============================================================

@register.simple_tag(takes_context=True)
def get_alerts_count(context):
    """
    Count of active alerts (not completed/dismissed).
    This is the main badge count for the Production menu.
    """
    from ..models_alerts import Alert
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return Alert.objects.filter(
        organization=org,
        status='active'
    ).count()


@register.simple_tag(takes_context=True)
def get_alerts_urgent_count(context):
    """
    Count of urgent/high priority active alerts.
    """
    from ..models_alerts import Alert
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return Alert.objects.filter(
        organization=org,
        status='active',
        priority__in=['urgent', 'high']
    ).count()


@register.simple_tag(takes_context=True)
def get_drafts_count(context):
    """
    Count of drafts (brouillons) to finalize.
    """
    from ..models_alerts import Alert
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return Alert.objects.filter(
        organization=org,
        status='active',
        alert_type='draft'
    ).count()


@register.simple_tag(takes_context=True)
def get_alerts_by_category(context, category):
    """
    Count of active alerts for a specific category.
    Usage: {% get_alerts_by_category 'vendange' as vendange_alerts %}
    """
    from ..models_alerts import Alert
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return Alert.objects.filter(
        organization=org,
        status='active',
        category=category
    ).count()


@register.simple_tag(takes_context=True)
def get_overdue_alerts_count(context):
    """
    Count of overdue alerts.
    """
    from ..models_alerts import Alert
    from django.utils import timezone
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    if not org:
        return 0
    
    return Alert.objects.filter(
        organization=org,
        status='active',
        due_date__lt=timezone.now().date()
    ).count()


@register.inclusion_tag('production/_alerts_badge.html', takes_context=True)
def alerts_badge(context, size='sm'):
    """
    Render an alert badge with count and tooltip.
    Usage: {% alerts_badge %} or {% alerts_badge 'lg' %}
    """
    from ..models_alerts import Alert
    from django.utils import timezone
    
    request = context.get('request')
    org = getattr(request, 'current_org', None) if request else None
    
    if not org:
        return {'count': 0, 'urgent': 0, 'overdue': 0, 'size': size}
    
    alerts = Alert.objects.filter(organization=org, status='active')
    count = alerts.count()
    urgent = alerts.filter(priority__in=['urgent', 'high']).count()
    overdue = alerts.filter(due_date__lt=timezone.now().date()).count()
    
    return {
        'count': count,
        'urgent': urgent,
        'overdue': overdue,
        'size': size,
    }


@register.filter
def liters_to_hl(value):
    """
    Convert liters to hectoliters.
    Usage: {{ volume_l|liters_to_hl }}
    """
    try:
        return Decimal(str(value)) / Decimal('100')
    except (TypeError, ValueError, InvalidOperation):
        return value


@register.filter
def format_volume_dual(value):
    """
    Format volume with both L and hL display.
    Usage: {{ volume_l|format_volume_dual }}
    Returns: "2250 L (22.5 hL)"
    """
    try:
        liters = Decimal(str(value))
        hl = liters / Decimal('100')
        return f"{liters:.0f} L ({hl:.2f} hL)"
    except (TypeError, ValueError, InvalidOperation):
        return str(value)
