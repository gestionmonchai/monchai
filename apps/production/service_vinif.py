from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone

from .models import VendangeReception, LotTechnique, generate_lot_tech_code, MouvementLot, Operation, LotLineage
from .models import CostEntry, CostSnapshot
from apps.viticulture.models import Lot as VitiLot, Warehouse
from apps.stock.models import StockManager
from apps.viticulture.services_journal import log_parcelle_op
from apps.drm.models import DRMLine


def compute_mout_volume_l(
    poids_kg: Decimal | float | int,
    rendement_base_l_par_kg: Decimal | float | int = Decimal('0.75'),
    effic_pct: Decimal | float | int = Decimal('100'),
) -> Decimal:
    """Calcule le volume de moût (L) avec rendement de base (L/kg) et efficacité (%).
    Formule: L ≈ kg * rendement_base_l_par_kg * (effic_pct / 100)
    Arrondis à 2 décimales (banquier) pour stockage.
    """
    kg = Decimal(str(poids_kg))
    base = Decimal(str(rendement_base_l_par_kg))
    pct = Decimal(str(effic_pct))
    vol = kg * base * (pct / Decimal('100'))
    return vol.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def init_from_vendange(
    vendange_id,
    rendement_base_l_par_kg: Decimal | float | int = Decimal('0.75'),
    effic_pct: Decimal | float | int = Decimal('100'),
    contenant: str = "",
    volume_mesure_l: Decimal | float | int | None = None,
    user=None,
    poids_debite_kg: Decimal | float | int | None = None,
    mode_encuvage: str | None = None,
    lot_type: str | None = None,
    temperature_c: Decimal | float | int | None = None,
    notes: str | None = None,
    expected_org_id=None,
) -> str:
    """Crée un LotTechnique à partir d'une vendange.
    - Prend la cuvée affectée à la vendange (obligatoire)
    - Calcule volume moût =
        • si volume_mesure_l est fourni → utilise la valeur mesurée
        • sinon kg * rendement_base_l_par_kg * effic_pct/100
    - Détermine la campagne à partir de vendange.campagne sinon vendange.date
    Retourne l'ID du lot technique créé (UUID en string).
    """
    with transaction.atomic():
        v = VendangeReception.objects.select_related('cuvee').select_for_update().get(pk=vendange_id)
        # Guard: enforce organization if provided
        try:
            v_org_id = getattr(v, 'organization_id', None) or (getattr(getattr(v, 'cuvee', None), 'organization_id', None))
            if expected_org_id is not None and v_org_id is not None and str(v_org_id) != str(expected_org_id):
                raise ValueError("Accès interdit: vendange hors organisation courante")
        except Exception:
            pass
        if not v.cuvee_id:
            raise ValueError("La vendange n'est pas affectée à une cuvée.")

        # Utiliser le poids débité si fourni, sinon le poids restant (fractionnement), fallback poids total
        try:
            if (poids_debite_kg is not None and str(poids_debite_kg).strip() != ""):
                kg_used = Decimal(str(poids_debite_kg))
            else:
                try:
                    # propriété calculée si disponible
                    kg_used = Decimal(str(getattr(v, 'kg_restant')))
                except Exception:
                    # fallback sur total - cumul
                    cum = Decimal(str(getattr(v, 'kg_debites_cumules', 0) or 0))
                    tot = Decimal(str(getattr(v, 'poids_kg', 0) or 0))
                    rem = tot - cum
                    kg_used = rem if rem > 0 else tot
        except Exception:
            kg_used = Decimal(str(getattr(v, 'poids_kg', 0) or 0))

        if volume_mesure_l is not None:
            volume_l = Decimal(str(volume_mesure_l)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            volume_l = compute_mout_volume_l(kg_used, rendement_base_l_par_kg, effic_pct)

        # Campagne AA AA+1 (utiliser le champ s'il existe déjà)
        campagne = v.campagne
        if not campagne:
            y = v.date.year if v.date else timezone.now().year
            campagne = f"{y}-{y+1}"

        # Générer code unique
        code = generate_lot_tech_code(campagne)

        # Déterminer un statut initial simple
        try:
            m = (mode_encuvage or '')
            lt = (lot_type or '')
            m_low = str(m).lower()
            lt_low = str(lt).lower()
            init_status = 'MOUT_PRESSE' if ('press' in m_low or 'presse' in m_low or lt_low in ('mout_presse', 'presse')) else 'MOUT_ENCUVE'
        except Exception:
            init_status = 'MOUT_ENCUVE'

        lot = LotTechnique.objects.create(
            code=code,
            campagne=campagne,
            contenant=contenant or "",
            volume_l=volume_l,
            statut=init_status,
            cuvee_id=v.cuvee_id,
            source=v,
        )
        # Normaliser le volume hL@20°C
        try:
            lot.volume_hl20 = (volume_l / Decimal('100')).quantize(Decimal('0.001'))
            # Back-compat: remplir aussi l'ancien champ si présent
            if hasattr(lot, 'volume_v20_hl'):
                lot.volume_v20_hl = lot.volume_hl20
            lot.save(update_fields=['volume_hl20', 'volume_v20_hl'] if hasattr(lot, 'volume_v20_hl') else ['volume_hl20'])
        except Exception:
            pass
        try:
            org = getattr(v.cuvee, 'organization', None)
        except Exception:
            org = None
        try:
            op = Operation.objects.create(
                organization=org,
                kind='encuvage',
                date=timezone.now(),
                meta={
                    'vendange_id': str(v.id),
                    'volume_l': str(volume_l),
                    'poids_debite_kg': str(kg_used),
                    'mode_encuvage': mode_encuvage or '',
                    'lot_type': lot_type or '',
                },
            )
            LotLineage.objects.create(operation=op, parent_lot=None, child_lot=lot, ratio=None)
        except Exception:
            pass
        # Mouvement interne (journal lottech): entrée initiale
        try:
            MouvementLot.objects.create(
                lot=lot,
                type='ENTREE_INITIALE',
                volume_l=volume_l,
                meta={
                    'vendange_id': str(v.id),
                    'rendement_pct': str(effic_pct),
                    'contenant': contenant or '',
                    'poids_debite_kg': str(kg_used),
                    'mode_encuvage': mode_encuvage or '',
                    'lot_type': lot_type or '',
                    'temperature_c': str(temperature_c) if temperature_c is not None else '',
                    'notes': (notes or '')[:200],
                },
                author=user,
            )
        except Exception:
            pass
        # Mettre à jour la vendange (statut, contenant, métriques, cumul kg débités)
        try:
            updates = []
            if hasattr(v, 'statut'):
                v.statut = 'encuvee'
                updates.append('statut')
            if hasattr(v, 'contenant') and (contenant or '') != getattr(v, 'contenant', ''):
                v.contenant = contenant or ''
                updates.append('contenant')
            if hasattr(v, 'rendement_pct') and effic_pct is not None:
                v.rendement_pct = Decimal(str(effic_pct))
                updates.append('rendement_pct')
            if hasattr(v, 'volume_mesure_l') and volume_mesure_l is not None:
                v.volume_mesure_l = Decimal(str(volume_mesure_l)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                updates.append('volume_mesure_l')
            # Incrémenter les kg débités cumulés (protégé par select_for_update)
            try:
                if hasattr(v, 'kg_debites_cumules'):
                    tot = Decimal(str(getattr(v, 'poids_kg', 0) or 0))
                    cur = Decimal(str(getattr(v, 'kg_debites_cumules', 0) or 0))
                    new_val = cur + (kg_used or Decimal('0'))
                    if tot and new_val > tot:
                        new_val = tot
                    v.kg_debites_cumules = new_val
                    updates.append('kg_debites_cumules')
            except Exception:
                pass
            if updates:
                v.save(update_fields=list(set(updates)))
        except Exception:
            pass
        # Créer le lot viticulture et mouvement d'entrée initial (ENTREE_INITIALE)
        try:
            org = getattr(v.cuvee, 'organization', None)
            if org and user is not None:
                wh = Warehouse.objects.filter(organization=org).order_by('name').first()
                if not wh:
                    wh = Warehouse.objects.create(organization=org, name='Principal')
                vlot = VitiLot.objects.create(
                    organization=org,
                    code=code,
                    cuvee=v.cuvee,
                    warehouse=wh,
                    volume_l=volume_l,
                    status='elevage',
                )
                lot.external_lot_id = vlot.id
                lot.save(update_fields=['external_lot_id'])
                # Mouvement stock: entrée initiale
                StockManager.move_vrac(
                    lot=vlot,
                    src_warehouse=None,
                    dst_warehouse=wh,
                    qty_l=volume_l,
                    move_type='entree',
                    user=user,
                    ref_type='encuvage',
                    ref_id=lot.id,
                    notes=(f"Encuvage vendange {str(v.id)}" + (f" – {notes}" if notes else ""))[:200],
                )
        except Exception:
            # Ne jamais faire échouer l'encuvage sur la partie stock; journaliser ultérieurement si besoin
            pass
        # Journal coût: entrée vrac initiale (montant = prix raisin * kg si fourni, sinon 0)
        try:
            org = getattr(v.cuvee, 'organization', None)
            if org:
                amount = Decimal('0.0000')
                try:
                    if v.prix_raisin_eur_kg and kg_used and Decimal(v.prix_raisin_eur_kg) > 0:
                        amount = (Decimal(v.prix_raisin_eur_kg) * Decimal(kg_used)).quantize(Decimal('0.0001'))
                except Exception:
                    amount = Decimal('0.0000')
                CostEntry.objects.create(
                    organization=org,
                    entity_type='lottech',
                    entity_id=lot.id,
                    nature='vrac_in',
                    qty=volume_l,
                    amount_eur=amount,
                    meta={
                        'source': 'vendange',
                        'vendange_id': str(v.id),
                        'prix_raisin_eur_kg': str(getattr(v, 'prix_raisin_eur_kg', '')),
                        'kg_net': str(getattr(v, 'poids_kg', '')),
                        'kg_debite_kg': str(kg_used),
                        'rendement_base_l_kg': str(rendement_base_l_par_kg),
                        'effic_pct': str(effic_pct),
                        'contenant': contenant or '',
                        'volume_source': 'mesure' if volume_mesure_l is not None else 'calcule',
                        'mode_encuvage': mode_encuvage or '',
                        'lot_type': lot_type or '',
                        'temperature_c': str(temperature_c) if temperature_c is not None else '',
                        'notes': (notes or '')[:200],
                    },
                    author=None,
                )
                _recalc_lottech_snapshot(org_id=org.id, lottech_id=lot.id)
                # Journal parcelle (vendange) et DRM entrée
                try:
                    # Journal parcelle (vendange)
                    p = getattr(v, 'parcelle', None)
                    if p is not None:
                        log_parcelle_op(
                            org=org,
                            parcelle=p,
                            op_code='vendange',
                            date=getattr(v, 'date', timezone.now().date()),
                            resume=f"Encuvage {volume_l} L (kg débités {kg_used})",
                            surface_ha=getattr(p, 'surface_ha', None),
                            attachments=[],
                            cout_matiere_eur=str(amount),
                            source_obj=v,
                        )
                except Exception:
                    pass
                try:
                    # DRM entrée (encuvage)
                    DRMLine.objects.create(
                        organization=org,
                        date=getattr(v, 'date', timezone.now().date()),
                        type='entree',
                        volume_l=volume_l,
                        ref_kind='encuvage',
                        ref_id=lot.id,
                        campagne=campagne,
                    )
                except Exception:
                    pass
        except Exception:
            # Ne jamais faire échouer l'encuvage sur la compta; journaliser ultérieurement si besoin
            pass
        return str(lot.id)


def _recalc_lottech_snapshot(*, org_id, lottech_id) -> None:
    """Recalcule le CMP vrac (€/L) pour un LotTechnique depuis le journal CostEntry.
    CMP = (Σ amount_in - Σ amount_out - Σ amount_loss) / (Σ qty_in - Σ qty_out - Σ qty_loss)
    """
    from django.db.models import Sum
    entries = CostEntry.objects.filter(organization_id=org_id, entity_type='lottech', entity_id=lottech_id)
    latest = entries.order_by('-date', '-id').first()
    # Existing snapshot (if any)
    snap = CostSnapshot.objects.filter(organization_id=org_id, entity_type='lottech', entity_id=lottech_id).first()
    # If latest movement is a loss, keep CMP unchanged; only touch updated_at
    if latest and latest.nature == 'vrac_loss' and snap:
        snap.save(update_fields=['updated_at'])
        return

    # Else compute CMP from all journal lines
    sums = entries.values('nature').annotate(qty_sum=Sum('qty'), amt_sum=Sum('amount_eur'))
    qty_in = Decimal('0'); amt_in = Decimal('0')
    qty_out = Decimal('0'); amt_out = Decimal('0')
    qty_loss = Decimal('0'); amt_loss = Decimal('0')
    for row in sums:
        n = row['nature']; q = row['qty_sum'] or Decimal('0'); a = row['amt_sum'] or Decimal('0')
        if n == 'vrac_in':
            qty_in += q; amt_in += a
        elif n == 'vrac_out':
            qty_out += q; amt_out += a
        elif n == 'vrac_loss':
            qty_loss += q; amt_loss += a
    num = (amt_in - amt_out - amt_loss)
    den = (qty_in - qty_out - qty_loss)
    cmp = Decimal('0')
    if den and den > 0:
        try:
            cmp = (num / den).quantize(Decimal('0.0001'))
        except Exception:
            cmp = Decimal('0')
    if not snap:
        snap = CostSnapshot.objects.create(
            organization_id=org_id,
            entity_type='lottech',
            entity_id=lottech_id,
            cmp_vrac_eur_l=cmp,
        )
    else:
        snap.cmp_vrac_eur_l = cmp
        snap.save(update_fields=['cmp_vrac_eur_l', 'updated_at'])
