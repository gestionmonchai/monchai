import uuid
from decimal import Decimal
import pytest
from django.utils import timezone

from apps.accounts.models import Organization
from apps.referentiels.models import Parcelle as RefParcelle
from apps.viticulture.models import UnitOfMeasure, Cuvee
from apps.production.models import VendangeReception, LotTechnique, Operation, LotLineage
from apps.chai.services import lots as lot_services


@pytest.mark.django_db
def test_encuvage_creates_lot_and_operation():
    # Org
    org = Organization.objects.create(name="Domaine Test", siret="12345678901234")

    # Referentials
    uom = UnitOfMeasure.objects.create(
        organization=org,
        code="hL",
        name="Hectolitre",
        base_ratio_to_l=Decimal('100.0'),
        is_default=True,
    )
    cuvee = Cuvee.objects.create(
        organization=org,
        name="Rouge Test",
        default_uom=uom,
    )
    parcelle = RefParcelle.objects.create(
        organization=org,
        nom="Parcelle A",
        surface=Decimal('1.00'),
    )

    # Harvest
    vend = VendangeReception.objects.create(
        nom="Vendange Test",
        date=timezone.now().date(),
        parcelle=parcelle,
        cuvee=cuvee,
        poids_kg=Decimal('1000.00'),
    )

    # When: create lot from encuvage (no measured volume -> compute)
    lot, op = lot_services.create_from_encuvage(
        harvest=vend,
        container="CUVE-1",
        user=None,
    )

    # Then: lot exists
    assert isinstance(lot, LotTechnique)
    assert lot.source_id == vend.id
    assert lot.cuvee_id == cuvee.id
    assert lot.statut in ("MOUT_ENCUVE", "MOUT_PRESSE")

    # Operation and lineage recorded
    op_db = Operation.objects.filter(kind='encuvage', lineages__child_lot=lot).first()
    assert op_db is not None
    ll = LotLineage.objects.filter(operation=op_db, child_lot=lot).first()
    assert ll is not None and ll.parent_lot is None

    # Volume normalized is set (hL@20°C ≈ kg * 0.75 / 100)
    assert lot.volume_hl20 is not None
    expected_hl20 = (Decimal('1000.00') * Decimal('0.75') / Decimal('100')).quantize(Decimal('0.001'))
    assert lot.volume_hl20 == expected_hl20
