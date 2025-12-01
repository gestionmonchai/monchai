from __future__ import annotations
from decimal import Decimal
from django.db import transaction, models
from .models_ms import MSItem, MSEmplacement, MSMove, MSMoveNature


def _current_stock(org, item: MSItem) -> Decimal:
    qs = MSMove.objects.filter(organization=org, item=item)
    plus = qs.filter(nature__in=[MSMoveNature.MS_IN, MSMoveNature.TRANSFER_IN, MSMoveNature.ADJUST_POS]).aggregate(s=models.Sum("qty"))['s'] or Decimal('0')
    minus = qs.filter(nature__in=[MSMoveNature.TRANSFER_OUT, MSMoveNature.MS_OUT, MSMoveNature.ADJUST_NEG, MSMoveNature.SCRAP_OUT]).aggregate(s=models.Sum("qty"))['s'] or Decimal('0')
    return (plus - minus) or Decimal('0')


@transaction.atomic
def ms_receive(org, item: MSItem, location: MSEmplacement, qty: Decimal, unit_price_eur: Decimal, ref: str = ""):
    if qty is None or Decimal(qty) <= 0:
        raise ValueError("Quantité d'entrée invalide")
    if unit_price_eur is None or Decimal(unit_price_eur) < 0:
        raise ValueError("Prix unitaire invalide")
    # Update CMP (moyenne pondérée)
    old_stock = _current_stock(org, item)
    old_value = old_stock * (item.cmp_eur_u or Decimal('0'))
    new_value = old_value + (Decimal(qty) * Decimal(unit_price_eur))
    new_stock = old_stock + Decimal(qty)
    item.cmp_eur_u = (new_value / new_stock) if new_stock > 0 else Decimal('0')
    item.save(update_fields=["cmp_eur_u"])

    MSMove.objects.create(
        organization=org,
        item=item,
        from_location=None,
        to_location=location,
        qty=Decimal(qty),
        unit_price_eur=Decimal(unit_price_eur),
        nature=MSMoveNature.MS_IN,
        ref=ref,
    )


@transaction.atomic
def ms_transfer(org, item: MSItem, from_loc: MSEmplacement, to_loc: MSEmplacement, qty: Decimal, ref: str = ""):
    if qty is None or Decimal(qty) <= 0:
        raise ValueError("Quantité de transfert invalide")
    # Record OUT then IN
    MSMove.objects.create(
        organization=org,
        item=item,
        from_location=from_loc,
        to_location=to_loc,
        qty=Decimal(qty),
        unit_price_eur=Decimal('0'),
        nature=MSMoveNature.TRANSFER_OUT,
        ref=ref,
    )
    MSMove.objects.create(
        organization=org,
        item=item,
        from_location=from_loc,
        to_location=to_loc,
        qty=Decimal(qty),
        unit_price_eur=Decimal('0'),
        nature=MSMoveNature.TRANSFER_IN,
        ref=ref,
    )


@transaction.atomic
def ms_adjust(org, item: MSItem, location: MSEmplacement, delta_qty: Decimal, reason: str):
    if delta_qty is None or Decimal(delta_qty) == 0:
        raise ValueError("Delta quantité requis")
    if Decimal(delta_qty) < 0 and not (reason or '').strip():
        raise ValueError("Motif requis pour ajustement négatif")
    nature = MSMoveNature.ADJUST_POS if Decimal(delta_qty) > 0 else MSMoveNature.ADJUST_NEG
    MSMove.objects.create(
        organization=org,
        item=item,
        from_location=None if Decimal(delta_qty) > 0 else location,
        to_location=location if Decimal(delta_qty) > 0 else None,
        qty=abs(Decimal(delta_qty)),
        unit_price_eur=Decimal('0'),
        nature=nature,
        ref=reason or "",
    )
