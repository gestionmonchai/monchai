from decimal import Decimal
import pytest

from apps.production.service_vinif import compute_mout_volume_l, init_from_vendange, _recalc_lottech_snapshot
from apps.accounts.models import Organization, User
from apps.viticulture.models import UnitOfMeasure, Lot as VitiLot
from apps.referentiels.models import Cuvee
from apps.referentiels.models import Parcelle as RefParcelle
from apps.production.models import VendangeReception, LotTechnique, CostEntry, CostSnapshot
from apps.stock.models import StockVracMove, StockVracBalance


def test_compute_mout_volume_l_basic_defaults():
    # Default base yield 0.75 L/kg and 100% efficiency
    assert compute_mout_volume_l(1000) == Decimal('750.00')


def test_compute_mout_volume_l_custom_base():
    # Base 0.6825 L/kg and 100% efficiency → 850.5*0.6825=580.58625→580.59
    assert compute_mout_volume_l(850.5, Decimal('0.6825'), Decimal('100')) == Decimal('580.59')


def test_compute_mout_volume_l_with_efficiency():
    # 1000 kg, base 0.70, efficiency 95% → 665.00 L
    assert compute_mout_volume_l(1000, Decimal('0.70'), Decimal('95')) == Decimal('665.00')


@pytest.mark.django_db
def test_init_from_vendange_volume_mesure_prioritaire():
    org = Organization.objects.create(name='Org', siret='12345678901234')
    uom = UnitOfMeasure.objects.create(organization=org, code='L', name='Litre', base_ratio_to_l=Decimal('1'))
    cuvee = Cuvee.objects.create(organization=org, name='Cuvée Test', default_uom=uom)
    parcelle = RefParcelle.objects.create(organization=org, nom='Parcelle A', surface=Decimal('1.00'))
    v = VendangeReception.objects.create(parcelle=parcelle, poids_kg=Decimal('8000'), cuvee=cuvee)
    user = User.objects.create_user(email='u@example.com', username='u', password='x')
    lot_id = init_from_vendange(vendange_id=v.id, volume_mesure_l=Decimal('1234.5'), user=user)
    lot = LotTechnique.objects.get(id=lot_id)
    assert lot.volume_l == Decimal('1234.50')
    # Mouvement d'entrée créé
    moves = StockVracMove.objects.filter(ref_type='encuvage', ref_id=lot.id)
    assert moves.count() == 1
    # Balance mise à jour
    vlot = VitiLot.objects.get(code=lot.code, organization=org)
    bal = StockVracBalance.objects.filter(organization=org, lot=vlot, warehouse=vlot.warehouse).first()
    assert bal and bal.qty_l == Decimal('1234.50')
    # Coûts & snapshot
    ce = CostEntry.objects.filter(organization=org, entity_type='lottech', entity_id=lot.id, nature='vrac_in').first()
    assert ce and ce.qty == Decimal('1234.50') and ce.amount_eur == Decimal('0.0000')
    snap = CostSnapshot.objects.filter(organization=org, entity_type='lottech', entity_id=lot.id).first()
    assert snap and snap.cmp_vrac_eur_l == Decimal('0')


@pytest.mark.django_db
def test_init_from_vendange_rendement_calcule():
    org = Organization.objects.create(name='Org2', siret='22345678901234')
    uom = UnitOfMeasure.objects.create(organization=org, code='L', name='Litre', base_ratio_to_l=Decimal('1'))
    cuvee = Cuvee.objects.create(organization=org, name='Cuvée Rdt', default_uom=uom)
    parcelle = RefParcelle.objects.create(organization=org, nom='Parcelle B', surface=Decimal('2.00'))
    v = VendangeReception.objects.create(parcelle=parcelle, poids_kg=Decimal('8000'), cuvee=cuvee)
    user = User.objects.create_user(email='r@example.com', username='r', password='x')
    lot_id = init_from_vendange(vendange_id=v.id, rendement_base_l_par_kg=Decimal('0.75'), effic_pct=Decimal('70'), user=user)
    lot = LotTechnique.objects.get(id=lot_id)
    assert lot.volume_l == Decimal('4200.00')  # 8000 * 0.75 * 0.70


@pytest.mark.django_db
def test_snapshot_cmp_apres_entree_et_perte_ne_change_pas_cmp():
    org = Organization.objects.create(name='Org3', siret='32345678901234')
    uom = UnitOfMeasure.objects.create(organization=org, code='L', name='Litre', base_ratio_to_l=Decimal('1'))
    cuvee = Cuvee.objects.create(organization=org, name='Cuvée CMP', default_uom=uom)
    parcelle = RefParcelle.objects.create(organization=org, nom='Parcelle C', surface=Decimal('3.00'))
    v = VendangeReception.objects.create(parcelle=parcelle, poids_kg=Decimal('8000'), cuvee=cuvee)
    user = User.objects.create_user(email='c@example.com', username='c', password='x')
    lot_id = init_from_vendange(vendange_id=v.id, rendement_base_l_par_kg=Decimal('0.75'), effic_pct=Decimal('70'), user=user)
    lot = LotTechnique.objects.get(id=lot_id)
    # CMP initial 0
    snap = CostSnapshot.objects.get(organization=org, entity_type='lottech', entity_id=lot.id)
    assert snap.cmp_vrac_eur_l == Decimal('0')
    # Ajouter un coût d'achat simulé pour définir CMP = 0.50 €/L
    CostEntry.objects.create(
        organization=org,
        entity_type='lottech',
        entity_id=lot.id,
        nature='vrac_in',
        qty=Decimal('4200.00'),
        amount_eur=Decimal('2100.0000'),
        meta={'source': 'test'},
        author=None,
    )
    _recalc_lottech_snapshot(org_id=org.id, lottech_id=lot.id)
    snap.refresh_from_db()
    assert snap.cmp_vrac_eur_l == Decimal('0.5000')
    # Pertes 100 L au CMP courant → ne change pas CMP
    CostEntry.objects.create(
        organization=org,
        entity_type='lottech',
        entity_id=lot.id,
        nature='vrac_loss',
        qty=Decimal('100.00'),
        amount_eur=Decimal('50.0000'),  # 0.50 * 100
        meta={'source': 'test_loss'},
        author=None,
    )
    _recalc_lottech_snapshot(org_id=org.id, lottech_id=lot.id)
    snap.refresh_from_db()
    assert snap.cmp_vrac_eur_l == Decimal('0.5000')
