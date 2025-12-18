
import os
import sys
import django
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, Membership
from apps.clients.models import Customer
from apps.produits.models_catalog import SKU, Product, InventoryItem
from apps.commerce.models import CommercialDocument, CommercialLine, Payment
from apps.commerce.services import DocumentService
from apps.referentiels.models import Unite

class UserJourneySimulation:
    def __init__(self, user_email='test@example.com', org_name='Test Org'):
        self.User = get_user_model()
        self.user = self.ensure_user(user_email)
        self.org = self.ensure_org(org_name)
        self.ensure_membership()
        self.log_header("Simulation Start")

    def log(self, msg, icon="->"):
        print(f"{icon} {msg}")

    def log_header(self, msg):
        print(f"\n{'='*50}\n{msg.center(50)}\n{'='*50}")

    def ensure_user(self, email):
        user = self.User.objects.filter(email=email).first()
        if not user:
            user = self.User.objects.create_user(username=email.split('@')[0], email=email, password='password123')
            self.log(f"Created system user: {email}", "[USER]")
        return user

    def ensure_org(self, name):
        org = Organization.objects.filter(name=name).first()
        if not org:
            org = Organization.objects.create(name=name)
            self.log(f"Created organization: {name}", "[ORG]")
        return org

    def ensure_membership(self):
        if not Membership.objects.filter(user=self.user, organization=self.org).exists():
            Membership.objects.create(user=self.user, organization=self.org, role='admin')
            self.log("Linked user to organization", "[LINK]")

    def find_or_create_client(self, name, email=None, segment='individual'):
        """
        Simulates the user searching for a client, and creating it if missing.
        """
        self.log(f"User searches for client: '{name}'")
        client = Customer.objects.filter(organization=self.org, name__iexact=name).first()
        
        if client:
            self.log(f"Client found: {client.name} (ID: {client.id})", "[OK]")
            return client
        else:
            self.log(f"Client not found. User clicks 'Create Client'...", "[NEW]")
            client = Customer.objects.create(
                organization=self.org,
                name=name,
                email=email or f"{name.lower().replace(' ', '.')}@example.com",
                segment=segment
            )
            self.log(f"Client created successfully: {client.name}", "[OK]")
            return client

    def ensure_product_and_stock(self, product_name, sku_name="Bouteille", price=15.0, stock_qty=100):
        """
        Ensures a product exists and has stock for the sale.
        """
        self.log(f"User checks catalog for product: '{product_name}'")
        
        # 1. Ensure Unit
        uom, _ = Unite.objects.get_or_create(
            organization=self.org, nom='Unité', 
            defaults={'symbole': 'u', 'type_unite': 'quantite'}
        )
        
        # 2. Ensure Product
        product = Product.objects.filter(organization=self.org, name=product_name).first()
        if not product:
            product = Product.objects.create(
                organization=self.org, name=product_name, product_type='vin',
                unit=uom, price_eur_u=price, vat_rate=20, volume_l=0.75
            )
            self.log(f"Product '{product_name}' created in catalog", "[PROD]")
        
        # 3. Ensure SKU
        sku = SKU.objects.filter(organization=self.org, product=product, name=sku_name).first()
        if not sku:
            sku = SKU.objects.create(
                organization=self.org, product=product, name=sku_name,
                unite=uom, default_price_ht=price
            )
            self.log(f"SKU '{sku_name}' configured for product", "[SKU]")
            
        # 4. Check Stock
        inv, _ = InventoryItem.objects.get_or_create(organization=self.org, sku=sku)
        self.log(f"Checking stock for {product_name}... Current: {inv.qty}")
        if inv.qty < 10:
            inv.qty = stock_qty
            inv.save()
            self.log(f"Refilled stock to {stock_qty} (Simulation adjustment)", "[STOCK]")
            
        return sku

    def create_direct_invoice(self, client_name, items):
        """
        Simulates creating a direct invoice (Fast Invoice)
        """
        self.log_header("Scenario: Direct Invoice Creation")
        
        # Step 1: Client
        client = self.find_or_create_client(client_name)
        
        # Step 2: Initialize Draft Invoice
        self.log("User initializes new Invoice...")
        invoice = CommercialDocument.objects.create(
            organization=self.org,
            type=CommercialDocument.TYPE_INVOICE,
            side=CommercialDocument.SIDE_SALE,
            client=client,
            status=CommercialDocument.STATUS_DRAFT,
            created_by=self.user,
            number="DRAFT" # Will be generated
        )
        self.log(f"Draft Invoice initialized for {client.name}", "[DOC]")
        
        # Step 3: Add Items
        total_amount = 0
        for item in items:
            sku = self.ensure_product_and_stock(item['product'], price=item['price'])
            qty = item['qty']
            
            # Check availability logic could go here
            self.log(f"User adds line: {qty}x {sku.product.name} @ {sku.default_price_ht}€")
            
            # Ensure Decimal for calculations
            unit_price = Decimal(str(sku.default_price_ht))
            quantity = Decimal(str(qty))
            
            line_ht = unit_price * quantity
            line_tax = line_ht * Decimal('0.20')
            
            CommercialLine.objects.create(
                document=invoice,
                sku=sku,
                description=sku.product.name,
                quantity=quantity,
                unit_price=unit_price,
                amount_ht=line_ht,
                amount_tax=line_tax,
                amount_ttc=line_ht + line_tax
            )
            total_amount += (line_ht + line_tax)
            
        # Recalc totals
        invoice.total_ht = sum(l.amount_ht for l in invoice.lines.all())
        invoice.total_tax = sum(l.amount_tax for l in invoice.lines.all())
        invoice.total_ttc = sum(l.amount_ttc for l in invoice.lines.all())
        invoice.save()
        
        # Step 4: Validate/Issue
        self.log("User clicks 'Validate'...", "[CLICK]")
        invoice.number = f"INV-{timezone.now().strftime('%Y%m%d')}-{invoice.id}"
        invoice.status = CommercialDocument.STATUS_ISSUED
        invoice.save()
        self.log(f"Invoice {invoice.number} issued! Total: {invoice.total_ttc}€", "[DONE]")
        
        return invoice

    def run(self):
        # Scenario: Selling wine to a new restaurant
        items_to_sell = [
            {'product': 'Château Mon Chai 2022', 'price': 12.50, 'qty': 24},
            {'product': 'Cuvée Prestige 2018', 'price': 45.00, 'qty': 6}
        ]
        
        # This will trigger lookup then creation
        self.create_direct_invoice("Le Petit Bistrot", items_to_sell)
        
        # This will trigger lookup (found) then use
        self.create_direct_invoice("Le Petit Bistrot", [{'product': 'Château Mon Chai 2022', 'price': 12.50, 'qty': 12}])

if __name__ == '__main__':
    sim = UserJourneySimulation()
    sim.run()
