from __future__ import annotations
from typing import Optional, Sequence, Mapping
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

from .models_parcelle_journal import ParcelleJournalEntry, ParcelleOperationType


def _to_decimal(v) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def log_parcelle_op(*, org, parcelle, op_code: str, date, date_end=None,
                    resume: str = "", notes: str = "", surface_ha=None, rangs: str = "",
                    attachments: Optional[Sequence[Mapping]] = None,
                    cout_mo_eur=None, cout_matiere_eur=None,
                    source_obj=None) -> ParcelleJournalEntry:
    """
    Crée une entrée journal en lecture seule. Idempotence simple via (org, parcelle, op_code, date, source).
    Vendanges: ne pas appeler ce helper (aucune entrée dans la timeline).
    """
    attachments = list(attachments or [])
    op_type, _ = ParcelleOperationType.objects.get_or_create(
        code=op_code,
        defaults={"label": op_code.replace("_", " ").title()}
    )
    source_ct = ContentType.objects.get_for_model(source_obj) if source_obj else None
    source_id = str(getattr(source_obj, 'pk', '')) if source_obj else ""

    cout_mo = _to_decimal(cout_mo_eur)
    cout_ms = _to_decimal(cout_matiere_eur)
    cout_total = None
    if cout_mo is not None or cout_ms is not None:
        try:
            cout_total = (cout_mo or Decimal('0')) + (cout_ms or Decimal('0'))
        except Exception:
            cout_total = None

    entry = ParcelleJournalEntry.objects.create(
        organization=org,
        parcelle=parcelle,
        op_type=op_type,
        date=date,
        date_end=date_end,
        surface_ha=_to_decimal(surface_ha),
        rangs=rangs or "",
        resume=resume or "",
        notes=notes or "",
        attachments=attachments,
        cout_mo_eur=cout_mo,
        cout_matiere_eur=cout_ms,
        cout_total_eur=cout_total,
        source_ct=source_ct,
        source_id=source_id,
    )
    return entry
