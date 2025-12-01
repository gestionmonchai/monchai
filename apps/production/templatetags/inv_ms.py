from django import template
from decimal import Decimal
from django.db import models
from ..models_ms import MSMove, MSMoveNature, MSReservation

register = template.Library()


@register.filter
def get_ms_stock(item, request):
    org = getattr(request, 'current_org', None) or getattr(getattr(request, 'user', None), 'organization', None)
    if not org:
        return Decimal('0')
    qs = MSMove.objects.filter(organization=org, item=item)
    plus = qs.filter(nature__in=[MSMoveNature.MS_IN, MSMoveNature.TRANSFER_IN, MSMoveNature.ADJUST_POS]).aggregate(s=models.Sum('qty'))['s'] or Decimal('0')
    minus = qs.filter(nature__in=[MSMoveNature.TRANSFER_OUT, MSMoveNature.MS_OUT, MSMoveNature.ADJUST_NEG, MSMoveNature.SCRAP_OUT]).aggregate(s=models.Sum('qty'))['s'] or Decimal('0')
    return (plus - minus) or Decimal('0')


@register.filter
def get_ms_reserved(item, request):
    org = getattr(request, 'current_org', None) or getattr(getattr(request, 'user', None), 'organization', None)
    if not org:
        return Decimal('0')
    return MSReservation.objects.filter(organization=org, item=item).aggregate(s=models.Sum('qty'))['s'] or Decimal('0')


@register.filter
def ms_dispo(stock, reserved):
    try:
        s = Decimal(stock or 0)
        r = Decimal(reserved or 0)
        d = s - r
        return d if d > 0 else Decimal('0')
    except Exception:
        return Decimal('0')
