from __future__ import annotations
from decimal import Decimal
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid

from .models import Mise, MiseLigne, LotCommercial
from apps.production.models import LotTechnique, MouvementLot, VendangeReception, Assemblage, AssemblageLigne
from apps.drm.models import DRMLine
from apps.drm.services import select_inao_codes
from apps.viticulture.models import Lot as VitiLot, Warehouse, UnitOfMeasure, Cuvee as VitiCuvee
from apps.stock.models import StockManager, SKU, StockVracBalance, StockVracMove
from apps.production.models import CostEntry, CostSnapshot
from apps.production.service_vinif import _recalc_lottech_snapshot


def _next_mise_code(date) -> str:
    yy = str(date.year)[-2:]
    mm = f"{date.month:02d}"
    prefix = f"M{yy}{mm}-"
    latest = Mise.objects.filter(code_of__startswith=prefix).order_by('-code_of').first()
    seq = 1
    if latest:
        try:
            seq = int(latest.code_of.split('-')[-1]) + 1
        except Exception:
            seq = 1
    return f"{prefix}{seq:03d}"


def _has_basic_analyses(cuvee) -> bool:
    """Vérifie la présence d'analyses minimales sur la cuvée (pH, TA, SO2)."""
    if not cuvee:
        return False
    detail = getattr(cuvee, 'detail', None)
    if not detail:
        return False
    return any([
        getattr(detail, 'ph', None) is not None,
        getattr(detail, 'acidite_totale', None) is not None,
        getattr(detail, 'so2_total', None) is not None,
        getattr(detail, 'so2_libre', None) is not None,
    ])


def _ensure_warehouse(org) -> Warehouse:
    """Return a default warehouse for organization, create if needed."""
    wh = Warehouse.objects.filter(organization=org).order_by('name').first()
    if not wh:
        wh = Warehouse.objects.create(organization=org, name='Principal')
    return wh


def _ensure_viti_lot_for_lottech(lottech: LotTechnique, user=None) -> VitiLot:
    """Ensure a viticulture Lot exists and is linked via external_lot_id."""
    # Try fetch existing link
    if lottech.external_lot_id:
        try:
            return VitiLot.objects.get(id=lottech.external_lot_id)
        except VitiLot.DoesNotExist:
            pass
    org = getattr(lottech.cuvee, 'organization', None)
    wh = _ensure_warehouse(org)
    vlot = VitiLot.objects.create(
        organization=org,
        code=lottech.code,
        cuvee=lottech.cuvee,
        warehouse=wh,
        volume_l=lottech.volume_l,
        status='elevage',
    )
    lottech.external_lot_id = vlot.id
    lottech.save(update_fields=['external_lot_id'])
    # Initialize stock vrac balance with an 'entree' if no existing moves/balance
    try:
        has_moves = StockVracMove.objects.filter(organization=org, lot=vlot).exists()
        bal = StockVracBalance.objects.filter(organization=org, lot=vlot, warehouse=wh).first()
        if not has_moves and (bal is None or bal.qty_l == 0) and (vlot.volume_l or Decimal('0')) > 0 and user is not None:
            StockManager.move_vrac(
                lot=vlot,
                src_warehouse=None,
                dst_warehouse=wh,
                qty_l=vlot.volume_l,
                move_type='entree',
                user=user,
                ref_type='init_lottech',
                ref_id=lottech.id,
                notes='Initialisation stock depuis lot technique'
            )
    except Exception:
        pass
    return vlot


def _resolve_unit(org, format_ml: int) -> UnitOfMeasure:
    """Find or create a UnitOfMeasure for given ml (ex: BT750)."""
    code = f"BT{int(format_ml)}"
    name = f"Bouteille {int(format_ml)} ml"
    base_ratio = (Decimal(int(format_ml)) / Decimal(1000)).quantize(Decimal('0.0001'))
    uom, created = UnitOfMeasure.objects.get_or_create(
        organization=org,
        code=code,
        defaults={'name': name, 'base_ratio_to_l': base_ratio, 'is_default': False}
    )
    # If exists but ratio not set, keep existing; do not override silently.
    return uom


def _resolve_sku(org, cuvee: VitiCuvee, format_ml: int) -> SKU:
    """Find or create SKU for cuvée + format ml using per-format UOM."""
    uom = _resolve_unit(org, format_ml)
    volume_l = (Decimal(int(format_ml)) / Decimal(1000)).quantize(Decimal('0.0001'))
    label = f"{cuvee.name} {int(format_ml/10)}cl" if cuvee and cuvee.name else f"SKU {int(format_ml)}ml"
    sku, created = SKU.objects.get_or_create(
        organization=org,
        cuvee=cuvee,
        uom=uom,
        defaults={
            'volume_by_uom_to_l': volume_l,
            'label': label,
            'code_barres': '',
            'is_active': True,
        }
    )
    # If SKU exists but volume differs, keep existing; do not mutate silently.
    return sku


def prepare_mise_plan(cuvee, sources: List[Dict[str, Any]], formats: List[Dict[str, Any]]):
    """Calcule les volumes requis et renvoie un plan indicatif pour l'OF."""
    # Lock sources LotTechnique in stable order to avoid deadlocks
    try:
        from apps.production.models import LotTechnique as _LT
        lt_ids = sorted([s['lot'].id for s in sources])
        locked_lots = {lt.id: lt for lt in _LT.objects.select_for_update().filter(id__in=lt_ids).order_by('id')}
        # Replace sources with locked instances
        sources = [
            {'lot': locked_lots[s['lot'].id], 'volume_l': s['volume_l']}
            for s in sources
        ]
    except Exception:
        pass

    total_available_l = sum(Decimal(str(s['volume_l'])) for s in sources)
    total_nominal_l = sum(Decimal(f['quantite_unites']) * Decimal(f['format_ml']) / Decimal(1000) for f in formats)
    return {
        'total_available_l': total_available_l,
        'total_nominal_l': total_nominal_l,
        'ok': total_nominal_l <= total_available_l,
    }


@transaction.atomic
def create_mise_and_lots(mise_data: Dict[str, Any], sources: List[Dict[str, Any]], formats: List[Dict[str, Any]], user=None, execution_token=None):
    """
    Create a Mise with its lines and LotCommerciaux; decrement LotTechnique volumes and emit one DRMLine.
    - sources: list of {lot: LotTechnique, volume_l: Decimal}
    - formats: list of {format_ml: int, quantite_unites: int, pertes_pct: Decimal}
    """
    date = mise_data.get('date') or timezone.now().date()
    campagne = mise_data.get('campagne') or f"{date.year}-{date.year+1}"
    notes = mise_data.get('notes', '')
    cuvee = mise_data.get('cuvee')  # optional ViticultureCuvee

    mise = Mise.objects.create(
        code_of=_next_mise_code(date),
        date=date,
        campagne=campagne,
        notes=notes,
        execution_token=execution_token or uuid.uuid4(),
    )

    if not sources:
        raise ValidationError("Aucune source de lot technique fournie")
    if not formats:
        raise ValidationError("Aucun format de mise fourni")

    total_available_l = sum(Decimal(str(s['volume_l'])) for s in sources)

    # Compute total liters nominal required by packages (without losses)
    total_nominal_l = sum(Decimal(f['quantite_unites']) * Decimal(f['format_ml']) / Decimal(1000) for f in formats)

    # Guard: do not exceed available (before considering pertes)
    if total_nominal_l > total_available_l:
        raise ValueError("Le volume total requis dépasse le volume alloué des lots techniques")

    # Compute bottled total liters after losses (for DRM/reporting)
    bottled_total_l = Decimal('0')
    # weighted_amt (€/L * L) sera calculé après allocations pour journaliser les coûts

    # Optional MO cost provided via mise_data (total €); default 0
    mo_total_eur = Decimal(str(mise_data.get('mo_eur', 0))) if mise_data.get('mo_eur') is not None else Decimal('0')

    for f in formats:
        format_ml = int(f['format_ml'])
        qty = int(f['quantite_unites'])
        pertes_pct = Decimal(str(f.get('pertes_pct', 0)))
        nominal_l = Decimal(qty) * Decimal(format_ml) / Decimal(1000)
        bottled_l = (nominal_l * (Decimal('1') - pertes_pct / Decimal('100'))).quantize(Decimal('0.01'))
        bottled_total_l += bottled_l

    # Allocate NOMINAL liters to consume from sources (proportional to available)
    allocations = []  # [{'lottech': LotTechnique, 'vlot': VitiLot, 'allocated_nominal_l': Decimal}]
    if total_available_l > 0:
        running_sum = Decimal('0.00')
        for idx, s in enumerate(sources):
            lottech: LotTechnique = s['lot']
            vlot = _ensure_viti_lot_for_lottech(lottech, user=user)
            if idx < len(sources) - 1:
                frac = Decimal(str(s['volume_l'])) / total_available_l
                alloc = (total_nominal_l * frac).quantize(Decimal('0.01'))
                running_sum += alloc
            else:
                # last one gets the remainder to match exactly total_nominal_l
                alloc = (total_nominal_l - running_sum).quantize(Decimal('0.01'))
            allocations.append({'lottech': lottech, 'vlot': vlot, 'allocated_nominal_l': alloc})

    # Record MiseLigne per source with allocated bottled liters; also prepare costing
    # Compute weighted average CMP (€/L) across sources using snapshots
    weighted_amt = Decimal('0')
    for_cost_recalc_ids = []
    for item in allocations:
        lot = item['lottech']
        allocated_l = item['allocated_nominal_l']
        MiseLigne.objects.create(
            mise=mise,
            lot_tech_source=lot,
            format_ml=formats[0]['format_ml'] if formats else 750,
            quantite_unites=0,
            pertes_pct=Decimal('0'),
            volume_l=allocated_l,
        )
        # Decrement LotTechnique volume and update statut
        before = Decimal(str(lot.volume_l))
        new_vol = (before - allocated_l).quantize(Decimal('0.01'))
        lot.volume_l = new_vol if new_vol > 0 else Decimal('0.00')
        if lot.volume_l <= 0:
            lot.statut = 'epuise'
        else:
            lot.statut = 'conditionne_partiel'
        lot.save(update_fields=['volume_l', 'statut'])
        # Journal MouvementLot: MISE_OUT
        try:
            MouvementLot.objects.create(
                lot=lot,
                type='MISE_OUT',
                volume_l=allocated_l,
                meta={'mise_id': str(mise.id)},
            )
        except Exception:
            pass
        # Costing: create vrac_out cost entry valued at CMP of lottech snapshot
        try:
            org = getattr(lot.cuvee, 'organization', None)
            snap = CostSnapshot.objects.filter(organization=org, entity_type='lottech', entity_id=lot.id).first()
            cmp_vrac = getattr(snap, 'cmp_vrac_eur_l', Decimal('0')) or Decimal('0')
            amt = (cmp_vrac * allocated_l).quantize(Decimal('0.0001'))
            if org:
                CostEntry.objects.create(
                    organization=org,
                    entity_type='lottech',
                    entity_id=lot.id,
                    nature='vrac_out',
                    qty=allocated_l,
                    amount_eur=amt,
                    meta={'mise_id': str(mise.id)},
                    author=user,
                )
                for_cost_recalc_ids.append((org.id, lot.id))
            weighted_amt += (cmp_vrac * allocated_l)
        except Exception:
            pass

    # Destination warehouse (use first source lot's warehouse)
    first_vlot = allocations[0]['vlot'] if allocations else _ensure_viti_lot_for_lottech(sources[0]['lot'], user=user)
    dest_wh = first_vlot.warehouse or _ensure_warehouse(first_vlot.organization)

    # Create LotCommerciaux and Stock SKU moves (fabrication); accumulate bottled_total_l already computed
    for f in formats:
        format_ml = int(f['format_ml'])
        qty = int(f['quantite_unites'])
        pertes_pct = Decimal(str(f.get('pertes_pct', 0)))
        nominal_l = Decimal(qty) * Decimal(format_ml) / Decimal(1000)
        bottled_l = (nominal_l * (Decimal('1') - pertes_pct / Decimal('100'))).quantize(Decimal('0.01'))

        # Build lot code
        slug = slugify(getattr(cuvee, 'name', '') or 'mix')
        d = date
        code_lot = f"{slug}-{d.strftime('%y%m%d')}-{format_ml}"

        lot_com = LotCommercial.objects.create(
            mise=mise,
            code_lot=code_lot,
            cuvee=cuvee if cuvee else None,
            format_ml=format_ml,
            date_mise=date,
            quantite_unites=qty,
            stock_disponible=qty,
        )
        # effective cuvée pour sélection INAO
        effective_cuvee = cuvee or first_vlot.cuvee
        # Auto-select INAO/NC code using packaging (L), ABV (%) and appellation
        try:
            # Packaging in litres
            packaging_l = (Decimal(int(format_ml)) / Decimal(1000)).quantize(Decimal('0.001'))
            # ABV from cuvée detail if available, else from first viticulture lot
            abv_pct = None
            try:
                det = getattr((cuvee or effective_cuvee), 'detail', None)
                if det and getattr(det, 'degre_alcool_final', None) is not None:
                    abv_pct = det.degre_alcool_final
            except Exception:
                abv_pct = None
            if abv_pct is None:
                try:
                    abv_pct = getattr(first_vlot, 'alcohol_pct', None)
                except Exception:
                    abv_pct = None
            # Appellation (label)
            appellation_label = None
            try:
                appellation_label = getattr((cuvee or effective_cuvee), 'appellation', None)
                appellation_label = getattr(appellation_label, 'name', None)
            except Exception:
                appellation_label = None
            # Color from cuvée detail
            color = None
            try:
                tv = getattr((cuvee or effective_cuvee).detail, 'type_vin', None)
                color = tv if tv else None
            except Exception:
                color = None
            candidates = select_inao_codes(
                appellation=appellation_label,
                color=color,
                volume_l=packaging_l,
                abv_pct=abv_pct,
                q=None,
                limit=1,
            )
            code = candidates.first()
            if code:
                lot_com.inao_code = code.code_inao
                lot_com.nc_code = code.code_nc
                lot_com.save(update_fields=['inao_code', 'nc_code'])
        except Exception:
            # Do not fail mise on code auto-selection
            pass

        # Resolve SKU (by org inferred from cuvée or first_vlot)
        org = getattr(cuvee, 'organization', None) or first_vlot.organization
        sku = _resolve_sku(org, effective_cuvee, format_ml)
        # Create SKU move (fabrication)
        if user is None:
            # For audit trail, user is required; raise explicit error rather than creating anonymous moves
            raise ValidationError("Utilisateur requis pour enregistrer les mouvements de stock")
        StockManager.move_sku(
            sku=sku,
            src_warehouse=None,
            dst_warehouse=dest_wh,
            qty_units=qty,
            move_type='fabrication',
            user=user,
            ref_type='mise',
            ref_id=mise.id,
            notes=f"Mise {mise.code_of} – {qty} x {format_ml}ml"
        )

    # Emit DRM line for bottled liters (with organization)
    try:
        org_for_drm = None
        try:
            org_for_drm = getattr(cuvee, 'organization', None) or first_vlot.organization
        except Exception:
            org_for_drm = getattr(first_vlot, 'organization', None)
        DRMLine.objects.create(
            organization=org_for_drm,
            date=date,
            type='mise',
            volume_l=bottled_total_l,
            ref_kind='mise',
            ref_id=mise.id,
            campagne=campagne,
        )
    except Exception:
        pass

    # Journal de coûts au niveau de la Mise (aggrégés)
    try:
        org = getattr(cuvee, 'organization', None) or first_vlot.organization
        if org:
            # Vrac consommé (mise-level)
            if total_nominal_l and weighted_amt:
                CostEntry.objects.create(
                    organization=org,
                    entity_type='mise',
                    entity_id=mise.id,
                    nature='vrac_out',
                    qty=total_nominal_l,
                    amount_eur=weighted_amt.quantize(Decimal('0.0001')),
                    meta={'note': 'consommation vrac pour mise'},
                    author=user,
                )
            # Main d'œuvre (mise-level)
            if mo_total_eur and mo_total_eur > 0:
                CostEntry.objects.create(
                    organization=org,
                    entity_type='mise',
                    entity_id=mise.id,
                    nature='mo',
                    qty=Decimal('1.0000'),
                    amount_eur=mo_total_eur.quantize(Decimal('0.0001')),
                    meta={'note': 'main d\'œuvre mise'},
                    author=user,
                )
    except Exception:
        pass

    # Create vrac stock moves (sortie) proportionally from each source lot (consume NOMINAL liters)
    for item in allocations:
        vlot: VitiLot = item['vlot']
        allocated_l: Decimal = item['allocated_nominal_l']
        if allocated_l <= 0:
            continue
        if user is None:
            raise ValidationError("Utilisateur requis pour enregistrer les mouvements de stock")
        StockManager.move_vrac(
            lot=vlot,
            src_warehouse=vlot.warehouse,
            dst_warehouse=None,
            qty_l=allocated_l,
            move_type='sortie',
            user=user,
            ref_type='mise',
            ref_id=mise.id,
            notes=f"Mise {mise.code_of} – consommation vrac"
        )
        # Also update viticulture lot current volume for display coherence
        try:
            cur = (vlot.volume_l or Decimal('0'))
            vlot.volume_l = (cur - allocated_l).quantize(Decimal('0.01'))
            if vlot.volume_l < 0:
                vlot.volume_l = Decimal('0.00')
            vlot.save(update_fields=['volume_l'])
        except Exception:
            pass

    # Recalculate CMP snapshots for impacted lot techniques
    try:
        for org_id, lt_id in for_cost_recalc_ids:
            _recalc_lottech_snapshot(org_id=org_id, lottech_id=lt_id)
    except Exception:
        pass

    # Marquer la mise comme terminée (idempotence)
    try:
        mise.state = 'terminee'
        mise.save(update_fields=['state'])
    except Exception:
        pass
    return mise


@transaction.atomic
def valider_mise(mise_data: Dict[str, Any], sources: List[Dict[str, Any]], formats: List[Dict[str, Any]], enforce_analyses: bool = True, user=None, token=None):
    """Valide une mise avec garde-fous:
    - Tous les lots sources doivent être en statut 'pret_mise'
    - Si enforce_analyses: la cuvée doit avoir des analyses basiques (pH/TA/SO2)
    """
    cuvee = mise_data.get('cuvee')
    if enforce_analyses and not _has_basic_analyses(cuvee):
        raise ValueError("Analyses insuffisantes (pH/TA/SO₂) pour valider la mise")

    for s in sources:
        lot: LotTechnique = s['lot']
        if lot.statut != 'pret_mise':
            raise ValueError(f"Lot technique {lot.code} non prêt pour mise (statut={lot.statut})")

    # Plan de volume
    plan = prepare_mise_plan(cuvee, sources, formats)
    if not plan['ok']:
        raise ValueError("Volume requis supérieur au volume disponible")

    # Idempotence via token/execution_token
    if token is not None:
        existing = Mise.objects.select_for_update().filter(execution_token=token).first()
        if existing and existing.state == 'terminee':
            return existing
    mise = create_mise_and_lots(mise_data, sources, formats, user=user, execution_token=token)
    return mise


# ================== Traçabilité (Mise → Vendange) ==================

def _collect_vendanges_from_lottech(lottech_id) -> set[str]:
    """Retourne un set d'UUID vendanges liés à un LotTechnique (directement ou via assemblage)."""
    visited_lots: set[str] = set()
    vendanges: set[str] = set()

    def _walk(lt_id):
        sid = str(lt_id)
        if sid in visited_lots:
            return
        visited_lots.add(sid)
        lt = LotTechnique.objects.filter(id=lt_id).only('id', 'source_id').first()
        if not lt:
            return
        # Lien direct vendange → lot technique
        if getattr(lt, 'source_id', None):
            vendanges.add(str(lt.source_id))
            return
        # Sinon, tenter via assemblage (lot résultat)
        asm = Assemblage.objects.filter(result_lot_id=lt_id).only('id').first()
        if not asm:
            return
        src_ids = list(AssemblageLigne.objects.filter(assemblage=asm).values_list('lot_source_id', flat=True))
        for src in src_ids:
            _walk(src)

    _walk(lottech_id)
    return vendanges


def build_trace_for_mise(mise_id) -> list[dict]:
    """Construit la traçabilité d'une mise: liste de vendanges liées (sans pondération de volumes).
    Retour: [{id, code, date, parcelle}]
    """
    lines = list(MiseLigne.objects.filter(mise_id=mise_id).values_list('lot_tech_source_id', flat=True))
    vend_ids: set[str] = set()
    for lt_id in lines:
        vend_ids |= _collect_vendanges_from_lottech(lt_id)
    # Scope by organizations of involved lots (cuvee.organization or source.organization)
    org_ids = set()
    try:
        org_ids |= set(LotTechnique.objects.filter(id__in=lines).values_list('cuvee__organization_id', flat=True))
        org_ids |= set(LotTechnique.objects.filter(id__in=lines).values_list('source__organization_id', flat=True))
        org_ids = {oid for oid in org_ids if oid is not None}
    except Exception:
        org_ids = set()
    qs = VendangeReception.objects.filter(id__in=vend_ids)
    if org_ids:
        qs = qs.filter(organization_id__in=list(org_ids))
    vendanges = list(qs.select_related('parcelle').only('id', 'code', 'date', 'parcelle__nom'))
    # Serializer léger pour template
    return [
        {
            'id': str(v.id),
            'code': v.code or '',
            'date': v.date,
            'parcelle': getattr(getattr(v, 'parcelle', None), 'nom', '') or '',
        }
        for v in vendanges
    ]
