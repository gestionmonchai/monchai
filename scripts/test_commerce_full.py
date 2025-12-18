
import os
import sys
import django
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from decimal import Decimal

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monchai.settings")
django.setup()

from apps.accounts.models import Organization, Membership
from apps.commerce.models import CommercialDocument, CommercialLine, Payment
from apps.produits.models_catalog import Product, SKU
from apps.clients.models import Customer
from apps.referentiels.models import Unite

def run_test():
    print("=== STARTING FULL COMMERCE TEST & SIMULATION ===")
    
    # 1. Setup User and Organization
    User = get_user_model()
    email = "test_commerce_full@example.com"
    password = "password123"
    
    user, created = User.objects.get_or_create(email=email)
    if created:
        user.set_password(password)
        user.first_name = "Test"
        user.last_name = "User"
        user.save()
        print(f"[SETUP] Created user {email}")
    else:
        print(f"[SETUP] Using existing user {email}")

    org, created = Organization.objects.get_or_create(name="Commerce Test Org")
    if created:
        print(f"[SETUP] Created organization {org.name}")
    else:
        print(f"[SETUP] Using existing organization {org.name}")
        
    # Ensure user is in org
    if not Membership.objects.filter(user=user, organization=org).exists():
        Membership.objects.create(user=user, organization=org, role='owner')
        print(f"[SETUP] Created membership for user in org")
        
    # Switch to this org context for requests
    c = Client()
    c.force_login(user)
    session = c.session
    session['organization_id'] = str(org.id)
    session.save()
    
    # 2. Setup Master Data (Product, Client, Supplier)
    unite, _ = Unite.objects.get_or_create(symbole="btl", organization=org, defaults={'nom': 'Bouteille'})
    
    product, _ = Product.objects.get_or_create(
        name="Vin Test Commerce",
        organization=org,
        defaults={'product_type': 'vin', 'type_code': 'wine', 'unit': unite, 'price_eur_u': 10.0}
    )
    
    sku, _ = SKU.objects.get_or_create(
        product=product,
        internal_ref="SKU-TEST-COMMERCE",
        defaults={'name': 'Vin Test Bouteille', 'organization': org, 'unite': unite}
    )
    print(f"[SETUP] Product/SKU ready: {sku.internal_ref}")
    
    supplier, _ = Customer.objects.get_or_create(
        name="Fournisseur Test",
        organization=org,
        defaults={'segment': 'supplier'}
    )
    
    client, _ = Customer.objects.get_or_create(
        name="Client Test",
        organization=org,
        defaults={'segment': 'business'}
    )
    print(f"[SETUP] Clients ready: {supplier.name}, {client.name}")

    # 3. URL Verification (Crawling)
    print("\n--- 3. URL Verification ---")
    
    urls_to_test = [
        # Dashboard
        ('commerce:dashboard', {'side': 'purchase'}, "Dashboard Purchase"),
        ('commerce:dashboard', {'side': 'sale'}, "Dashboard Sale"),
        
        # Lists
        ('commerce:document_list', {'side': 'purchase'}, "List Purchase"),
        ('commerce:document_list', {'side': 'sale'}, "List Sale"),
        ('commerce:payment_list', {'side': 'purchase'}, "Payments Purchase"),
        ('commerce:payment_list', {'side': 'sale'}, "Payments Sale"),
        ('commerce:payment_schedule', {'side': 'purchase'}, "Schedule Purchase"),
        ('commerce:payment_schedule', {'side': 'sale'}, "Schedule Sale"),
        
        # Clients (New path)
        ('clients:customers_list', {}, "Clients List"),
        ('clients:customer_create', {}, "Clients Create"),
        
        # Legacy paths (Redirects)
        ('/ventes/clients/', None, "Legacy Clients Redirect"),
    ]
    
    for url_name, kwargs, label in urls_to_test:
        try:
            if url_name.startswith('/'):
                url = url_name
            else:
                url = reverse(url_name, kwargs=kwargs)
            
            resp = c.get(url, follow=True)
            if resp.status_code == 200:
                print(f"[OK] {label}: {url}")
            else:
                print(f"[FAIL] {label}: {url} returned {resp.status_code}")
        except Exception as e:
            print(f"[ERROR] {label}: {e}")

    # 4. Simulation: Purchase Flow
    print("\n--- 4. Simulation: Purchase Flow ---")
    
    # Create Purchase Order
    po_data = {
        'type': 'order',
        'client': supplier.id,
        'date_issue': '2025-01-01',
        'date_due': '2025-01-31',
        'sale_mode': 'standard',
        'notes': 'Test Auto Purchase'
    }
    url_create = reverse('commerce:document_create', kwargs={'side': 'purchase', 'type': 'order'})
    resp = c.post(url_create, po_data, follow=True)
    if resp.status_code == 200:
        po = CommercialDocument.objects.filter(organization=org, side='purchase', type='order').order_by('-created_at').first()
        if po:
            print(f"[SUCCESS] Created Purchase Order: {po.number}")
        else:
            print(f"[FAIL] PO not found in DB. Response context errors:")
            if resp.context is not None and 'form' in resp.context:
                print(resp.context['form'].errors)
            else:
                # Decode content to show meaningful error if possible
                content = resp.content.decode('utf-8')
                print(f"No form in context. Content start: {content[:500]}")
            return
    else:
        print(f"[FAIL] Creating PO: {resp.status_code}")
        return

    # Add Line
    line_data = {
        'sku': sku.id,
        'description': 'Achat Vin Test',
        'quantity': 100,
        'unit_price': 5.00,
        'tax_rate': 20.00,
        'discount_pct': 0
    }
    c.post(reverse('commerce:line_add', args=[po.id]), line_data, follow=True)
    po.refresh_from_db()
    print(f"[INFO] Added line. Total TTC: {po.total_ttc}")
    
    # Validate
    c.post(reverse('commerce:document_validate', args=[po.id]), follow=True)
    po.refresh_from_db()
    print(f"[INFO] Validated PO. Status: {po.status}")
    
    # Receive (Transform to Delivery/Reception)
    c.post(reverse('commerce:document_transform', args=[po.id, 'delivery']), follow=True)
    reception = CommercialDocument.objects.filter(organization=org, side='purchase', type='delivery').order_by('-created_at').first()
    print(f"[SUCCESS] Created Reception: {reception.number}")
    
    # Execute Reception (Stock Move)
    c.post(reverse('commerce:document_execute', args=[reception.id]), follow=True)
    reception.refresh_from_db()
    print(f"[INFO] Executed Reception. Status: {reception.status}")
    
    # Bill (Transform to Invoice)
    c.post(reverse('commerce:document_transform', args=[reception.id, 'invoice']), follow=True)
    bill = CommercialDocument.objects.filter(organization=org, side='purchase', type='invoice').order_by('-created_at').first()
    print(f"[SUCCESS] Created Bill: {bill.number}")
    
    # Pay Bill
    pay_data = {
        'amount': bill.total_ttc,
        'method': 'virement',
        'date': '2025-01-02',
        'reference': 'VIR123'
    }
    c.post(reverse('commerce:payment_add', args=[bill.id]), pay_data, follow=True)
    bill.refresh_from_db()
    print(f"[INFO] Paid Bill. Status: {bill.status}, Paid: {bill.amount_paid}")

    # 5. Simulation: Sale Flow
    print("\n--- 5. Simulation: Sale Flow ---")
    
    # Create Quote
    quote_data = {
        'type': 'quote',
        'client': client.id,
        'date_issue': '2025-02-01',
        'date_due': '2025-02-28',
        'sale_mode': 'standard',
        'notes': 'Test Auto Sale'
    }
    url_create_quote = reverse('commerce:document_create', kwargs={'side': 'sale', 'type': 'quote'})
    resp = c.post(url_create_quote, quote_data, follow=True)
    if resp.status_code == 200:
        quote = CommercialDocument.objects.filter(organization=org, side='sale', type='quote').order_by('-created_at').first()
        if quote:
            print(f"[SUCCESS] Created Quote: {quote.number}")
        else:
            print(f"[FAIL] Quote not found in DB. Response context errors:")
            if resp.context and 'form' in resp.context:
                print(resp.context['form'].errors)
            else:
                print(f"No form in context. Content: {resp.content[:200]}")
            return
    else:
        print(f"[FAIL] Creating Quote: {resp.status_code}")
        return
    
    # Add Line
    line_data_sale = {
        'sku': sku.id,
        'description': 'Vente Vin Test',
        'quantity': 12,
        'unit_price': 10.00,
        'tax_rate': 20.00,
        'discount_pct': 0
    }
    c.post(reverse('commerce:line_add', args=[quote.id]), line_data_sale, follow=True)
    quote.refresh_from_db()
    print(f"[INFO] Added line to Quote. Total TTC: {quote.total_ttc}")
    
    # Transform to Order
    c.post(reverse('commerce:document_transform', args=[quote.id, 'order']), follow=True)
    so = CommercialDocument.objects.filter(organization=org, side='sale', type='order').order_by('-created_at').first()
    print(f"[SUCCESS] Converted to Order: {so.number}")
    
    # Validate Order
    c.post(reverse('commerce:document_validate', args=[so.id]), follow=True)
    
    # Deliver
    c.post(reverse('commerce:document_transform', args=[so.id, 'delivery']), follow=True)
    delivery = CommercialDocument.objects.filter(organization=org, side='sale', type='delivery').order_by('-created_at').first()
    print(f"[SUCCESS] Created Delivery: {delivery.number}")
    
    # Execute Delivery
    c.post(reverse('commerce:document_execute', args=[delivery.id]), follow=True)
    delivery.refresh_from_db()
    print(f"[INFO] Executed Delivery. Status: {delivery.status}")
    
    # Invoice
    c.post(reverse('commerce:document_transform', args=[delivery.id, 'invoice']), follow=True)
    invoice = CommercialDocument.objects.filter(organization=org, side='sale', type='invoice').order_by('-created_at').first()
    print(f"[SUCCESS] Created Invoice: {invoice.number}")
    
    # Pay Invoice
    c.post(reverse('commerce:payment_add', args=[invoice.id]), pay_data, follow=True)
    invoice.refresh_from_db()
    print(f"[INFO] Paid Invoice. Status: {invoice.status}")

    print("\n=== TEST COMPLETE ===")

if __name__ == '__main__':
    run_test()
