"""Services métier pour la gestion des Lots Techniques.

Invariants:
- Toute action modifiant l'état crée une Operation.
- Les opérations versionnantes créent un nouveau lot enfant et une LotLineage.
- Les volumes sont référencés en hL @ 20°C (volume_hl20) côté service; conversion 1 hL = 100 L.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple
from django.db import transaction
from django.utils import timezone

from apps.production.models import (
    VendangeReception,
    LotTechnique,
    Operation,
    LotLineage,
)
from apps.production.models import generate_lot_tech_code
from apps.production.service_vinif import init_from_vendange


HL_TO_L = Decimal("100")


def _to_liters(volume_hl20: Optional[Decimal]) -> Optional[Decimal]:
    if volume_hl20 is None:
        return None
    return (Decimal(str(volume_hl20)) * HL_TO_L).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _to_hl20(volume_l: Optional[Decimal]) -> Optional[Decimal]:
    if volume_l is None:
        return None
    return (Decimal(str(volume_l)) / HL_TO_L).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


@transaction.atomic
def create_from_encuvage(
    *,
    harvest: VendangeReception,
    container: str,
    volume_hl20: Optional[Decimal] = None,
    poids_debite_kg: Optional[Decimal] = None,
    mode_encuvage: Optional[str] = None,
    lot_type: Optional[str] = None,
    temperature_c: Optional[Decimal] = None,
    notes: Optional[str] = None,
    user=None,
) -> Tuple[LotTechnique, Optional[Operation]]:
    """Crée un LotTechnique depuis une vendange (Encuvage/Pressurage).

    - Si volume_hl20 est fourni, il est converti en litres pour l'encuvage.
    - Retourne (lot, operation) où operation est l'Operation d'encuvage liée via LotLineage.
    """
    vol_l = _to_liters(volume_hl20)
    new_lot_id = init_from_vendange(
        vendange_id=harvest.id,
        rendement_base_l_par_kg=Decimal('0.75'),  # ignoré si vol_l fourni
        effic_pct=Decimal('100'),                  # ignoré si vol_l fourni
        contenant=container,
        volume_mesure_l=str(vol_l) if vol_l is not None else None,
        user=user,
        poids_debite_kg=poids_debite_kg,
        mode_encuvage=mode_encuvage,
        lot_type=lot_type,
        temperature_c=temperature_c,
        notes=notes,
        expected_org_id=(getattr(harvest, 'organization_id', None) or getattr(getattr(harvest, 'cuvee', None), 'organization_id', None)),
    )
    lot = LotTechnique.objects.get(id=new_lot_id)
    # Renseigner volume_hl20 à partir de volume_l si absent
    if lot.volume_hl20 is None:
        try:
            lot.volume_hl20 = _to_hl20(lot.volume_l)
            lot.save(update_fields=['volume_hl20'])
        except Exception:
            pass
    # Retrouver l'opération d'encuvage via la filiation
    op = Operation.objects.filter(kind='encuvage', lineages__child_lot=lot).order_by('-date', '-id').first()
    return lot, op


@transaction.atomic
def send_offsite(*, lot: LotTechnique, third_party: Optional[str] = None, meta: Optional[dict] = None, user=None):
    """Marque le lot comme hors site et journalise l'opération.
    Opération neutre (pas de nouveau lot)."""
    if getattr(lot, 'location_kind', 'ONSITE') == 'OFFSITE':
        raise ValueError("Lot déjà hors site")
    org = getattr(getattr(lot, 'cuvee', None), 'organization', None)
    op = Operation.objects.create(
        organization=org,
        kind='offsite_send',
        date=timezone.now(),
        meta={**(meta or {}), 'third_party': (third_party or '')},
    )
    lot.location_kind = 'OFFSITE'
    lot.save(update_fields=['location_kind'])
    return lot, op


@transaction.atomic
def return_offsite_neutral(*, lot: LotTechnique, meta: Optional[dict] = None, user=None):
    """Retour hors site neutre (pas de nouveau lot)."""
    if getattr(lot, 'location_kind', 'ONSITE') != 'OFFSITE':
        raise ValueError("Lot non hors site")
    org = getattr(getattr(lot, 'cuvee', None), 'organization', None)
    op = Operation.objects.create(
        organization=org,
        kind='offsite_return_neutral',
        date=timezone.now(),
        meta=(meta or {}),
    )
    lot.location_kind = 'ONSITE'
    lot.save(update_fields=['location_kind'])
    return lot, op


@transaction.atomic
def return_offsite_non_neutral(*, lot: LotTechnique, target_status: Optional[str] = None, meta: Optional[dict] = None, user=None):
    """Retour hors site non neutre (crée un lot enfant + filiation)."""
    if getattr(lot, 'location_kind', 'ONSITE') != 'OFFSITE':
        raise ValueError("Lot non hors site")
    org = getattr(getattr(lot, 'cuvee', None), 'organization', None)
    op = Operation.objects.create(
        organization=org,
        kind='offsite_return_non_neutral',
        date=timezone.now(),
        meta=(meta or {}),
    )
    code = generate_lot_tech_code(lot.campagne)
    child = LotTechnique.objects.create(
        code=code,
        campagne=lot.campagne,
        contenant=lot.contenant,
        volume_l=lot.volume_l,
        volume_hl20=lot.volume_hl20,
        statut=(target_status or lot.statut),
        cuvee=lot.cuvee,
        source=lot.source,
        composition_json=lot.composition_json,
        analytics_json=lot.analytics_json,
        external_lot_id=lot.external_lot_id,
        location_kind='ONSITE',
    )
    LotLineage.objects.create(operation=op, parent_lot=lot, child_lot=child, ratio=None)
    return child, op


@transaction.atomic
def transition(
    *,
    lot: LotTechnique,
    operation_kind: str,
    target_status: Optional[str] = None,
    versioning: bool = False,
    meta: Optional[dict] = None,
    user=None,
) -> Tuple[LotTechnique, Operation]:
    """Effectue une transition d'état sur un lot technique.

    - Crée une Operation de type `operation_kind`.
    - Si `versioning` est vrai, crée un lot enfant (copie métadonnées, volume inchangé) + LotLineage.
    - Si `target_status` est fourni, le statut est validé via can_transition(), sinon inchangé.
    """
    org = getattr(getattr(lot, 'cuvee', None), 'organization', None)
    op = Operation.objects.create(
        organization=org,
        kind=operation_kind,
        date=timezone.now(),
        meta=(meta or {}),
    )
    if versioning:
        # Nouveau lot enfant (code et timestamps gérés par services appelants si besoin)
        child = LotTechnique.objects.create(
            code=lot.code + "-V" + timezone.now().strftime("%H%M%S"),
            campagne=lot.campagne,
            contenant=lot.contenant,
            volume_l=lot.volume_l,
            volume_hl20=lot.volume_hl20,
            statut=target_status or lot.statut,
            cuvee=lot.cuvee,
            source=lot.source,
            composition_json=lot.composition_json,
            analytics_json=lot.analytics_json,
            external_lot_id=lot.external_lot_id,
            location_kind=lot.location_kind,
        )
        LotLineage.objects.create(operation=op, parent_lot=lot, child_lot=child, ratio=None)
        return child, op
    # Transition in-place
    if target_status:
        if not lot.can_transition(target_status):
            raise ValueError(f"Transition de statut invalide: {lot.statut} → {target_status}")
        lot.statut = target_status
        lot.save(update_fields=['statut'])
    return lot, op
