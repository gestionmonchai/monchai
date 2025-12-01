from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.contrib.auth import get_user_model

from apps.stock.models import StockManager


class MoveType:
    ENTREE_INITIALE = 'entree'
    SORTIE = 'sortie'
    TRANSFERT = 'transfert'
    AJUSTEMENT = 'ajustement'
    FABRICATION = 'fabrication'  # pour SKU


@transaction.atomic
def move_vrac(lot, src_wh, dst_wh, qty_l: Decimal, move_type: str, user, ref_type: Optional[str] = None, ref_id=None, notes: str = ''):
    """Facade production vers StockManager.move_vrac avec règles communes.
    - Garantit atomicité.
    - Laisse StockManager valider soldes et MAJ balances.
    """
    return StockManager.move_vrac(
        lot=lot,
        src_warehouse=src_wh,
        dst_warehouse=dst_wh,
        qty_l=qty_l,
        move_type=move_type,
        user=user,
        ref_type=ref_type,
        ref_id=ref_id,
        notes=notes,
    )


@transaction.atomic
def fabrication(lot, sku, warehouse, qty_units: int, user, notes: str = ''):
    """Facade production vers StockManager.fabrication_sku (vrac -> SKU).
    Retourne (vrac_move, sku_move).
    """
    return StockManager.fabrication_sku(
        lot=lot,
        sku=sku,
        warehouse=warehouse,
        qty_units=qty_units,
        user=user,
        notes=notes,
    )
