from __future__ import annotations
from decimal import Decimal
from .models import CostSnapshot, LotTechnique


def get_cmp_lot(lot_id) -> Decimal:
    snap = (CostSnapshot.objects
            .filter(entity_type='lottech', entity_id=lot_id)
            .order_by('-updated_at')
            .first())
    return getattr(snap, 'cmp_vrac_eur_l', Decimal('0')) if snap else Decimal('0')


def set_snapshot_cmp_lot(lot_id, cmp_eur_l: Decimal) -> None:
    # Ensure a snapshot exists for this lot with its organization
    try:
        lt = LotTechnique.objects.select_related('cuvee').get(id=lot_id)
        org = getattr(lt.cuvee, 'organization', None)
    except LotTechnique.DoesNotExist:
        org = None
        lt = None
    if not org:
        # Fallback: update existing snapshot if any
        snap = (CostSnapshot.objects
                .filter(entity_type='lottech', entity_id=lot_id)
                .order_by('-updated_at')
                .first())
        if snap:
            snap.cmp_vrac_eur_l = cmp_eur_l
            snap.save(update_fields=['cmp_vrac_eur_l', 'updated_at'])
        return
    CostSnapshot.objects.update_or_create(
        organization=org,
        entity_type='lottech',
        entity_id=lot_id,
        defaults={'cmp_vrac_eur_l': cmp_eur_l}
    )
