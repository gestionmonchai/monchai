from __future__ import annotations
from decimal import Decimal
from typing import Optional

try:
    from apps.viticulture.models import Lot as VitiLot, Warehouse
    from apps.stock.models import StockManager
except Exception:  # pragma: no cover - optional imports
    VitiLot = None
    Warehouse = None
    StockManager = None


def move_vrac(lottech, delta_l: Decimal, reason: str, user=None):
    """Bridge vers StockManager.move_vrac si environnement dispo. No-op sinon.
    lottech: apps.production.models.LotTechnique
    delta_l: positif = entrée, négatif = sortie
    reason: libellé ('ASSEMBLAGE_IN'/'OUT', etc.)
    """
    if not (VitiLot and Warehouse and StockManager):
        return
    org = getattr(lottech.cuvee, 'organization', None)
    if org is None:
        return
    # Ensurer un Lot viticulture proxy
    vlot = None
    try:
        from apps.production.views import _ensure_viti_lot_for_lottech  # lazy import
        vlot = _ensure_viti_lot_for_lottech(lottech)
    except Exception:
        return
    if delta_l == 0:
        return
    # Déterminer sens
    if delta_l > 0:
        # entrée: None -> warehouse
        StockManager.move_vrac(
            lot=vlot,
            src_warehouse=None,
            dst_warehouse=vlot.warehouse,
            qty_l=delta_l,
            move_type='entree',
            user=user,
            ref_type=reason,
            ref_id=lottech.id,
            notes='Assemblage wizard',
        )
    else:
        # sortie: warehouse -> None
        StockManager.move_vrac(
            lot=vlot,
            src_warehouse=vlot.warehouse,
            dst_warehouse=None,
            qty_l=abs(delta_l),
            move_type='sortie',
            user=user,
            ref_type=reason,
            ref_id=lottech.id,
            notes='Assemblage wizard',
        )
