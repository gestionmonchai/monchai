"""
Tests pour les modèles de ventes - DB Roadmap 03
Tests de robustesse selon la roadmap
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.utils import timezone

from apps.accounts.models import Organization
from apps.viticulture.models import (
    GrapeVariety, Appellation, Vintage, UnitOfMeasure, 
    Cuvee, Warehouse, Lot
)
from apps.stock.models import SKU, StockSKUBalance, StockManager
from .models import (
    TaxCode, Customer, PriceList, PriceItem, CustomerPriceList,
    Quote, QuoteLine, Order, OrderLine, StockReservation
)
from .managers import PricingManager, SalesManager

User = get_user_model()


class SalesModelsTestCase(TestCase):
    """Tests des modèles de ventes selon DB Roadmap 03"""
    
    def setUp(self):
        """Configuration des données de test"""
        # Organisation et utilisateur
        self.org = Organization.objects.create(
            name="Test Winery",
            siret="12345678901234"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Données viticulture de base
        self.grape_variety = GrapeVariety.objects.create(
            organization=self.org,
            name="Cabernet Sauvignon",
            color="rouge"
        )
        
        self.appellation = Appellation.objects.create(
            organization=self.org,
            name="Bordeaux AOC",
            region="Bordeaux"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.org,
            year=2023
        )
        
        self.uom_bottle = UnitOfMeasure.objects.create(
            organization=self.org,
            name="Bouteille",
            code="BT",
            base_ratio_to_l=Decimal('0.75')
        )
        
        self.uom_liter = UnitOfMeasure.objects.create(
            organization=self.org,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        self.cuvee = Cuvee.objects.create(
            organization=self.org,
            name="Réserve Rouge",
            vintage=self.vintage,
            appellation=self.appellation,
            default_uom=self.uom_liter
        )
        
        self.warehouse = Warehouse.objects.create(
            organization=self.org,
            name="Chai Principal"
        )
        
        self.sku = SKU.objects.create(
            organization=self.org,
            cuvee=self.cuvee,
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Réserve Rouge 2023 - Bouteille"
        )
        
        # Codes taxes
        self.tax_code_20 = TaxCode.objects.create(
            organization=self.org,
            code="TVA20",
            name="TVA 20%",
            rate_pct=Decimal('20.00'),
            country="FR"
        )
        
        self.tax_code_0 = TaxCode.objects.create(
            organization=self.org,
            code="TVA0",
            name="TVA 0%",
            rate_pct=Decimal('0.00'),
            country="FR"
        )
    
    def test_customer_creation_and_validation(self):
        """Test création et validation clients"""
        # Client particulier
        customer_part = Customer.objects.create(
            organization=self.org,
            type='part',
            legal_name="Jean Dupont",
            billing_address="123 Rue de la Paix",
            billing_postal_code="75001",
            billing_city="Paris",
            billing_country="FR"
        )
        
        self.assertEqual(customer_part.type, 'part')
        self.assertTrue(customer_part.is_active)
        
        # Client professionnel avec TVA
        customer_pro = Customer.objects.create(
            organization=self.org,
            type='pro',
            legal_name="Vins & Co SARL",
            vat_number="FR12345678901",
            billing_address="456 Avenue du Commerce",
            billing_postal_code="33000",
            billing_city="Bordeaux",
            billing_country="FR"
        )
        
        self.assertEqual(customer_pro.vat_number, "FR12345678901")
        self.assertTrue(customer_pro.has_shipping_address is False)
    
    def test_price_list_and_items(self):
        """Test grilles tarifaires et éléments de prix"""
        # Grille tarifaire
        price_list = PriceList.objects.create(
            organization=self.org,
            name="Tarif Standard",
            currency="EUR",
            valid_from=timezone.now().date()
        )
        
        # Élément de prix simple
        price_item = PriceItem.objects.create(
            organization=self.org,
            price_list=price_list,
            sku=self.sku,
            unit_price=Decimal('15.00')
        )
        
        self.assertEqual(price_item.effective_price, Decimal('15.00'))
        
        # Élément avec remise
        price_item_discount = PriceItem.objects.create(
            organization=self.org,
            price_list=price_list,
            sku=self.sku,
            unit_price=Decimal('20.00'),
            min_qty=12,
            discount_pct=Decimal('10.00')
        )
        
        self.assertEqual(price_item_discount.effective_price, Decimal('18.00'))
    
    def test_pricing_manager_resolution(self):
        """Test résolution de prix par PricingManager"""
        # Client et grille
        customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="Test Address",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        price_list = PriceList.objects.create(
            organization=self.org,
            name="Tarif Test",
            currency="EUR",
            valid_from=timezone.now().date()
        )
        
        # Prix avec seuils
        PriceItem.objects.create(
            organization=self.org,
            price_list=price_list,
            sku=self.sku,
            unit_price=Decimal('20.00'),
            min_qty=1
        )
        
        PriceItem.objects.create(
            organization=self.org,
            price_list=price_list,
            sku=self.sku,
            unit_price=Decimal('18.00'),
            min_qty=6,
            discount_pct=Decimal('5.00')
        )
        
        # Associer client à la grille
        CustomerPriceList.objects.create(
            customer=customer,
            price_list=price_list,
            priority=1
        )
        
        # Test résolution prix quantité 1
        price_info = PricingManager.resolve_price(customer, self.sku, qty=1)
        self.assertEqual(price_info['unit_price'], Decimal('20.00'))
        self.assertEqual(price_info['source'], 'customer_list')
        
        # Test résolution prix quantité 6
        price_info = PricingManager.resolve_price(customer, self.sku, qty=6)
        self.assertEqual(price_info['unit_price'], Decimal('18.00'))
        self.assertEqual(price_info['effective_price'], Decimal('17.10'))  # 18 - 5%
    
    def test_quote_creation_and_totals(self):
        """Test création devis et calcul totaux"""
        customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="Test Address",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        quote = Quote.objects.create(
            organization=self.org,
            customer=customer,
            valid_until=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # Ligne de devis
        quote_line = QuoteLine.objects.create(
            organization=self.org,
            quote=quote,
            sku=self.sku,
            description=self.sku.label,
            qty=6,
            unit_price=Decimal('15.00'),
            tax_code=self.tax_code_20
        )
        
        # Vérifier calculs automatiques
        self.assertEqual(quote_line.total_ht, Decimal('90.00'))  # 6 * 15
        self.assertEqual(quote_line.total_tax, Decimal('18.00'))  # 90 * 20%
        self.assertEqual(quote_line.total_ttc, Decimal('108.00'))  # 90 + 18
        
        # Recalculer totaux devis
        quote.calculate_totals()
        quote.save()
        
        self.assertEqual(quote.total_ht, Decimal('90.00'))
        self.assertEqual(quote.total_ttc, Decimal('108.00'))
    
    def test_sales_manager_quote_creation(self):
        """Test création devis via SalesManager"""
        # Setup prix
        customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="Test Address",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        price_list = PriceList.objects.create(
            organization=self.org,
            name="Défaut",
            currency="EUR",
            valid_from=timezone.now().date()
        )
        
        PriceItem.objects.create(
            organization=self.org,
            price_list=price_list,
            sku=self.sku,
            unit_price=Decimal('15.00')
        )
        
        # Panier
        cart_items = [
            {'sku': self.sku, 'qty': 3}
        ]
        
        # Créer devis
        quote = SalesManager.create_quote_from_cart(customer, cart_items)
        
        self.assertEqual(quote.customer, customer)
        self.assertEqual(quote.lines.count(), 1)
        self.assertEqual(quote.total_ttc, Decimal('54.00'))  # 3 * 15 * 1.20
    
    def test_order_confirmation_and_stock_reservation(self):
        """Test confirmation commande et réservation stock"""
        # Setup stock
        StockSKUBalance.objects.create(
            organization=self.org,
            sku=self.sku,
            warehouse=self.warehouse,
            qty_units=100
        )
        
        # Client et commande
        customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="Test Address",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        order = Order.objects.create(
            organization=self.org,
            customer=customer
        )
        
        OrderLine.objects.create(
            organization=self.org,
            order=order,
            sku=self.sku,
            description=self.sku.label,
            qty=10,
            unit_price=Decimal('15.00'),
            tax_code=self.tax_code_20
        )
        
        # Confirmer commande
        reservations = SalesManager.confirm_order(order, self.warehouse)
        
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations[0].qty_units, 10)
    
    def test_insufficient_stock_error(self):
        """Test erreur stock insuffisant"""
        # Stock limité
        StockSKUBalance.objects.create(
            organization=self.org,
            sku=self.sku,
            warehouse=self.warehouse,
            qty_units=5  # Seulement 5 unités
        )
        
        customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="Test Address",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        order = Order.objects.create(
            organization=self.org,
            customer=customer
        )
        
        OrderLine.objects.create(
            organization=self.org,
            order=order,
            sku=self.sku,
            description=self.sku.label,
            qty=10,  # Plus que disponible
            unit_price=Decimal('15.00'),
            tax_code=self.tax_code_20
        )
        
        # Doit échouer
        with self.assertRaises(ValidationError) as cm:
            SalesManager.confirm_order(order, self.warehouse)
        
        self.assertIn("Stock insuffisant", str(cm.exception))
    
    def test_cross_organization_validation(self):
        """Test validation cross-organisation"""
        # Autre organisation
        other_org = Organization.objects.create(
            name="Other Winery",
            siret="98765432109876"
        )
        
        other_customer = Customer.objects.create(
            organization=other_org,
            legal_name="Other Customer",
            billing_address="Other Address",
            billing_postal_code="54321",
            billing_city="Other City"
        )
        
        # Tenter de créer un devis avec client d'autre organisation
        quote = Quote(
            organization=self.org,
            customer=other_customer,  # Autre organisation
            valid_until=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        with self.assertRaises(ValidationError):
            quote.full_clean()
    
    def test_tax_code_resolution(self):
        """Test résolution codes taxes selon client"""
        # Client français
        customer_fr = Customer.objects.create(
            organization=self.org,
            legal_name="Client FR",
            billing_address="Test",
            billing_postal_code="12345",
            billing_city="Paris",
            billing_country="FR"
        )
        
        tax_code = PricingManager.get_tax_code(customer_fr, self.sku)
        self.assertEqual(tax_code.code, "TVA20")
        
        # Client pro UE avec TVA
        customer_eu_pro = Customer.objects.create(
            organization=self.org,
            type='pro',
            legal_name="EU Company",
            vat_number="DE123456789",
            billing_address="Test",
            billing_postal_code="12345",
            billing_city="Berlin",
            billing_country="DE"
        )
        
        tax_code = PricingManager.get_tax_code(customer_eu_pro, self.sku)
        self.assertEqual(tax_code.code, "TVA0")  # Autoliquidation
