"""
Tests pour les modèles de facturation - DB Roadmap 04
Tests de robustesse selon la roadmap
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.utils import timezone
import uuid

from apps.accounts.models import Organization
from apps.viticulture.models import GrapeVariety, Appellation, Vintage, UnitOfMeasure, Cuvee, Warehouse
from apps.stock.models import SKU, StockSKUBalance
from apps.sales.models import Customer, TaxCode, Order, OrderLine
from .models import (
    Invoice, InvoiceLine, CreditNote, Payment, Reconciliation,
    AccountMap, GLEntry
)
from .managers import BillingManager, AccountingManager

User = get_user_model()


class BillingModelsTestCase(TestCase):
    """Tests des modèles de facturation selon DB Roadmap 04"""
    
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
        
        # Données de base pour facturation
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
        
        self.cuvee = Cuvee.objects.create(
            organization=self.org,
            name="Réserve Rouge",
            vintage=self.vintage,
            appellation=self.appellation,
            default_uom=self.uom_bottle
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
        
        # Client et codes taxes
        self.customer = Customer.objects.create(
            organization=self.org,
            legal_name="Test Customer",
            billing_address="123 Test Street",
            billing_postal_code="12345",
            billing_city="Test City"
        )
        
        self.tax_code_20 = TaxCode.objects.create(
            organization=self.org,
            code="TVA20",
            name="TVA 20%",
            rate_pct=Decimal('20.00'),
            country="FR"
        )
        
        # Commande pour facturation
        self.order = Order.objects.create(
            organization=self.org,
            customer=self.customer,
            status='fulfilled'  # Prête à facturer
        )
        
        self.order_line = OrderLine.objects.create(
            organization=self.org,
            order=self.order,
            sku=self.sku,
            description=self.sku.label,
            qty=6,
            unit_price=Decimal('15.00'),
            tax_code=self.tax_code_20
        )
    
    def test_invoice_number_generation(self):
        """Test génération numéros de facture séquentiels"""
        # Premier numéro de l'année
        number1 = BillingManager.generate_invoice_number(self.org)
        year = timezone.now().year
        expected = f"{year}-0001"
        self.assertEqual(number1, expected)
        
        # Créer une facture avec ce numéro
        invoice1 = Invoice.objects.create(
            organization=self.org,
            customer=self.customer,
            number=number1,
            date_issue=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # Deuxième numéro doit être incrémenté
        number2 = BillingManager.generate_invoice_number(self.org)
        expected2 = f"{year}-0002"
        self.assertEqual(number2, expected2)
    
    def test_create_invoice_from_order(self):
        """Test création facture depuis commande"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        
        self.assertEqual(invoice.customer, self.customer)
        self.assertEqual(invoice.order, self.order)
        self.assertEqual(invoice.status, 'draft')
        self.assertEqual(invoice.lines.count(), 1)
        
        # Vérifier totaux
        line = invoice.lines.first()
        self.assertEqual(line.qty, 6)
        self.assertEqual(line.unit_price, Decimal('15.00'))
        self.assertEqual(line.total_ht, Decimal('90.00'))  # 6 * 15
        self.assertEqual(line.total_tva, Decimal('18.00'))  # 90 * 20%
        self.assertEqual(line.total_ttc, Decimal('108.00'))  # 90 + 18
        
        self.assertEqual(invoice.total_ttc, Decimal('108.00'))
    
    def test_invoice_cannot_be_created_twice_from_order(self):
        """Test qu'une commande ne peut être facturée qu'une fois"""
        # Première facture
        BillingManager.create_invoice_from_order(self.order)
        
        # Tentative de seconde facture
        with self.assertRaises(ValidationError) as cm:
            BillingManager.create_invoice_from_order(self.order)
        
        self.assertIn("déjà été facturée", str(cm.exception))
    
    def test_issue_invoice_and_accounting_entries(self):
        """Test émission facture et génération écritures comptables"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        
        # Émettre la facture
        gl_entries = BillingManager.issue_invoice(invoice, self.user)
        
        self.assertEqual(invoice.status, 'issued')
        self.assertTrue(len(gl_entries) >= 2)  # Au moins client + ventes
        
        # Vérifier écritures
        customer_entry = next((e for e in gl_entries if e.debit > 0), None)
        self.assertIsNotNone(customer_entry)
        self.assertEqual(customer_entry.debit, invoice.total_ttc)
        self.assertEqual(customer_entry.account_code, '411')  # Client
        
        sales_entry = next((e for e in gl_entries if e.credit > 0 and e.account_code == '707'), None)
        self.assertIsNotNone(sales_entry)
        self.assertEqual(sales_entry.credit, invoice.total_ht)
    
    def test_credit_note_creation(self):
        """Test création d'avoir"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Créer avoir partiel
        credit_note = BillingManager.create_credit_note(
            invoice, 
            "Produit défectueux", 
            amount_ht=Decimal('30.00')  # 1/3 de la facture
        )
        
        self.assertEqual(credit_note.invoice, invoice)
        self.assertEqual(credit_note.total_ht, Decimal('-30.00'))  # Négatif
        self.assertEqual(credit_note.total_tva, Decimal('-6.00'))   # -30 * 20%
        self.assertEqual(credit_note.total_ttc, Decimal('-36.00'))  # -30 - 6
        
        # Vérifier numérotation
        self.assertTrue(credit_note.number.startswith('AV-'))
    
    def test_payment_and_reconciliation(self):
        """Test paiement et lettrage"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Créer paiement
        payment = Payment.objects.create(
            organization=self.org,
            customer=self.customer,
            method='sepa',
            amount=Decimal('108.00'),  # Montant exact
            date_received=timezone.now().date()
        )
        
        # Lettrer le paiement
        reconciliation = BillingManager.allocate_payment(payment, invoice)
        
        self.assertEqual(reconciliation.amount_allocated, Decimal('108.00'))
        self.assertEqual(payment.amount_unallocated, Decimal('0'))
        
        # Vérifier que la facture est marquée comme payée
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.amount_due, Decimal('0'))
    
    def test_partial_payment_allocation(self):
        """Test allocation partielle de paiement"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Paiement partiel
        payment = Payment.objects.create(
            organization=self.org,
            customer=self.customer,
            method='sepa',
            amount=Decimal('50.00'),  # Moins que le total
            date_received=timezone.now().date()
        )
        
        # Lettrer partiellement
        reconciliation = BillingManager.allocate_payment(payment, invoice)
        
        self.assertEqual(reconciliation.amount_allocated, Decimal('50.00'))
        self.assertEqual(payment.amount_unallocated, Decimal('0'))
        
        # Facture toujours en attente
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'issued')
        self.assertEqual(invoice.amount_due, Decimal('58.00'))  # 108 - 50
    
    def test_overpayment_allocation(self):
        """Test allocation avec trop-perçu"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Paiement supérieur
        payment = Payment.objects.create(
            organization=self.org,
            customer=self.customer,
            method='sepa',
            amount=Decimal('150.00'),  # Plus que le total
            date_received=timezone.now().date()
        )
        
        # Lettrer automatiquement le maximum
        reconciliation = BillingManager.allocate_payment(payment, invoice)
        
        self.assertEqual(reconciliation.amount_allocated, Decimal('108.00'))  # Maximum possible
        self.assertEqual(payment.amount_unallocated, Decimal('42.00'))  # Reste
        
        # Facture payée
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
    
    def test_multiple_payments_on_invoice(self):
        """Test plusieurs paiements sur une facture"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Premier paiement
        payment1 = Payment.objects.create(
            organization=self.org,
            customer=self.customer,
            method='sepa',
            amount=Decimal('50.00'),
            date_received=timezone.now().date()
        )
        BillingManager.allocate_payment(payment1, invoice)
        
        # Deuxième paiement
        payment2 = Payment.objects.create(
            organization=self.org,
            customer=self.customer,
            method='card',
            amount=Decimal('58.00'),
            date_received=timezone.now().date()
        )
        BillingManager.allocate_payment(payment2, invoice)
        
        # Vérifier totaux
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal('108.00'))
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.reconciliations.count(), 2)
    
    def test_account_mapping(self):
        """Test mapping comptes comptables"""
        # Créer mapping personnalisé
        AccountMap.objects.create(
            organization=self.org,
            mapping_type='product',
            key='default',
            account_code='701',
            account_name='Ventes de produits finis'
        )
        
        # Tester résolution
        account_code = AccountingManager.get_account_code(
            self.org, 'product', 'default'
        )
        self.assertEqual(account_code, '701')
        
        # Tester fallback pour mapping inexistant
        account_code_fallback = AccountingManager.get_account_code(
            self.org, 'product', 'inexistant'
        )
        self.assertEqual(account_code_fallback, '707')  # Défaut
    
    def test_journal_export_csv(self):
        """Test export journal en CSV"""
        invoice = BillingManager.create_invoice_from_order(self.order)
        BillingManager.issue_invoice(invoice, self.user)
        
        # Export journal des ventes
        date_from = timezone.now().date()
        date_to = timezone.now().date()
        
        csv_data = AccountingManager.export_journal(
            self.org, 'VEN', date_from, date_to, 'csv'
        )
        
        self.assertIn('Date;Journal;Pièce;Compte;Libellé;Débit;Crédit', csv_data)
        self.assertIn('VEN', csv_data)
        self.assertIn(invoice.number, csv_data)
        self.assertIn('411', csv_data)  # Compte client
        self.assertIn('707', csv_data)  # Compte ventes
    
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
        
        # Tenter de créer une facture avec client d'autre organisation
        invoice = Invoice(
            organization=self.org,
            customer=other_customer,  # Autre organisation
            number="TEST-001",
            date_issue=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        with self.assertRaises(ValidationError):
            invoice.full_clean()
    
    def test_invoice_due_date_validation(self):
        """Test validation date d'échéance"""
        # Date d'échéance antérieure à la date d'émission
        invoice = Invoice(
            organization=self.org,
            customer=self.customer,
            number="TEST-001",
            date_issue=timezone.now().date(),
            due_date=timezone.now().date() - timezone.timedelta(days=1)  # Hier
        )
        
        with self.assertRaises(ValidationError) as cm:
            invoice.full_clean()
        
        self.assertIn("postérieure", str(cm.exception))
    
    def test_gl_entry_debit_credit_validation(self):
        """Test validation débit/crédit exclusifs"""
        # Écriture avec débit ET crédit
        gl_entry = GLEntry(
            organization=self.org,
            journal='VEN',
            date=timezone.now().date(),
            doc_type='invoice',
            doc_id=uuid.uuid4(),
            doc_number='TEST-001',
            account_code='411',
            debit=Decimal('100.00'),
            credit=Decimal('50.00'),  # Interdit
            label='Test'
        )
        
        with self.assertRaises(ValidationError):
            gl_entry.full_clean()
        
        # Écriture sans débit ni crédit
        gl_entry_empty = GLEntry(
            organization=self.org,
            journal='VEN',
            date=timezone.now().date(),
            doc_type='invoice',
            doc_id=uuid.uuid4(),
            doc_number='TEST-001',
            account_code='411',
            debit=Decimal('0'),
            credit=Decimal('0'),  # Interdit
            label='Test'
        )
        
        with self.assertRaises(ValidationError):
            gl_entry_empty.full_clean()
    
    def test_rounding_consistency(self):
        """Test cohérence arrondis ligne→totaux"""
        invoice = Invoice.objects.create(
            organization=self.org,
            customer=self.customer,
            number="TEST-001",
            date_issue=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # Ligne avec prix unitaire créant des arrondis
        line = InvoiceLine.objects.create(
            organization=self.org,
            invoice=invoice,
            sku=self.sku,
            description="Test arrondi",
            qty=Decimal('3'),
            unit_price=Decimal('10.33'),  # 3 * 10.33 = 30.99
            tax_code=self.tax_code_20
        )
        
        # Vérifier calculs
        self.assertEqual(line.total_ht, Decimal('30.99'))
        self.assertEqual(line.total_tva, Decimal('6.20'))  # 30.99 * 20% arrondi
        self.assertEqual(line.total_ttc, Decimal('37.19'))  # 30.99 + 6.20
        
        # Recalculer totaux facture
        invoice.calculate_totals()
        invoice.save()
        
        self.assertEqual(invoice.total_ht, Decimal('30.99'))
        self.assertEqual(invoice.total_ttc, Decimal('37.19'))
