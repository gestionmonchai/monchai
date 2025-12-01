from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Organization, Membership
from apps.viticulture.models import UnitOfMeasure, Cuvee
from apps.referentiels.models import Unite
from apps.produits.models_catalog import Product, SKU, InventoryItem
from apps.produits.models import Mise, LotCommercial


class ProductCatalogTests(TestCase):
    def setUp(self):
        # Org and user with active membership
        self.org = Organization.objects.create(
            name="OrgTest", siret="12345678901234",
        )
        self.user = User.objects.create_user(email="user@example.com", username="user", password="pwd")
        Membership.objects.create(user=self.user, organization=self.org, role=Membership.Role.OWNER, is_active=True)
        self.client.login(username="user@example.com", password="pwd")

        # Viticulture UoM and Cuvee
        self.uom_l = UnitOfMeasure.objects.create(
            organization=self.org,
            code="L",
            name="Litre",
            base_ratio_to_l=Decimal("1.0"),
            is_default=True,
        )
        self.cuvee = Cuvee.objects.create(
            organization=self.org,
            name="Cuvée Test",
            default_uom=self.uom_l,
        )

        # Référentiel Unités (catalogue SKUs): 0.75 L bottle
        self.unite_b75 = Unite.objects.create(
            organization=self.org,
            nom="Bouteille 75cl",
            symbole="75cl",
            type_unite="volume",
            facteur_conversion=Decimal("0.75"),
        )
        # Non-volume unit for non-wine products
        self.unite_unit = Unite.objects.create(
            organization=self.org,
            nom="Unité",
            symbole="u",
            type_unite="quantite",
            facteur_conversion=Decimal("1"),
        )

    def test_list_and_detail_show_sku_for_wine_product(self):
        # Create wine product + SKU
        p = Product.objects.create(
            organization=self.org,
            type_code="wine",
            name="Vin Demo",
            brand="Maison",
            slug="vin-demo",
            cuvee=self.cuvee,
            is_active=True,
        )
        SKU.objects.create(
            organization=self.org,
            product=p,
            name="Bouteille 75cl",
            unite=self.unite_b75,
            default_price_ht=Decimal("8.50"),
            is_active=True,
        )

        # List
        resp_list = self.client.get(reverse('produits:catalog_list'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "Vin Demo")

        # Detail
        resp_detail = self.client.get(reverse('produits:product_detail', kwargs={'slug': p.slug}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, "Bouteille 75cl")

    def test_wine_stock_aggregates_from_lots(self):
        # Create wine product + SKU
        p = Product.objects.create(
            organization=self.org,
            type_code="wine",
            name="Vin Lots",
            brand="Maison",
            slug="vin-lots",
            cuvee=self.cuvee,
            is_active=True,
        )
        sku = SKU.objects.create(
            organization=self.org,
            product=p,
            name="Bouteille 75cl",
            unite=self.unite_b75,
            is_active=True,
        )
        # Create Mise and LotCommercial for the cuvee with 750 ml format and available stock
        mise = Mise.objects.create(code_of="M2509-001", date=timezone.now().date(), campagne="2025-2026")
        LotCommercial.objects.create(
            mise=mise,
            code_lot="test-250928-750",
            cuvee=self.cuvee,
            format_ml=750,
            date_mise=timezone.now().date(),
            quantite_unites=50,
            stock_disponible=42,
        )

        resp = self.client.get(reverse('produits:product_detail', kwargs={'slug': p.slug}))
        self.assertEqual(resp.status_code, 200)
        # Expect to see the aggregated stock "42" in the table
        self.assertContains(resp, ">42<")

    def test_non_wine_stock_from_inventory(self):
        # Create non-wine product + SKU
        p = Product.objects.create(
            organization=self.org,
            type_code="food",
            name="Miel",
            brand="Maison",
            slug="miel",
            is_active=True,
        )
        sku = SKU.objects.create(
            organization=self.org,
            product=p,
            name="Pot 1u",
            unite=self.unite_unit,
            is_active=True,
        )
        InventoryItem.objects.create(
            organization=self.org,
            sku=sku,
            qty=13,
        )

        resp = self.client.get(reverse('produits:product_detail', kwargs={'slug': p.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, ">13<")
