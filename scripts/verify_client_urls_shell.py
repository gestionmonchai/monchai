
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership
from apps.clients.models import Customer

print("=== Verifying Client Pages (Shell) ===")

User = get_user_model()

# 1. Setup User and Organization
user = User.objects.filter(email='test@example.com').first()
if not user:
    user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='password123'
    )
    print(f"Created user: {user}")
else:
    print(f"Using user: {user}")

org = Organization.objects.filter(name='Test Org').first()
if not org:
    org = Organization.objects.create(name='Test Org')
    print(f"Created org: {org}")
else:
    print(f"Using org: {org}")

# Ensure membership
if not Membership.objects.filter(user=user, organization=org).exists():
    Membership.objects.create(user=user, organization=org, role='admin')
    print("Created membership")

c = Client()
c.force_login(user)

# Middleware simulation hack: force current_org in session if needed, 
# but usually middleware sets it on request based on user.
# Let's hope the middleware handles it for authenticated users with one org.

# 2. Verify List Page
try:
    url = reverse('clients:customers_list')
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: List page loaded")
    else:
        print(f"FAILURE: List page status {response.status_code}")
        if response.status_code in [301, 302]:
            print(f"Redirects to: {response.get('Location', 'Unknown')}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load list page: {e}")

# 3. Create a Customer for Detail/Edit tests
customer = Customer.objects.filter(name='Test Client Flow', organization=org).first()
if not customer:
    customer = Customer.objects.create(
        name='Test Client Flow',
        organization=org,
        segment='business',
        email='flow@test.com'
    )
    print(f"Created customer: {customer.id}")
else:
    print(f"Using customer: {customer.id}")

# 4. Verify Detail Page
try:
    url = reverse('clients:customer_detail', args=[customer.id])
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Detail page loaded")
    else:
        print(f"FAILURE: Detail page status {response.status_code}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load detail page: {e}")

# 5. Verify Edit Page
try:
    url = reverse('clients:customer_edit', args=[customer.id])
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Edit page loaded")
    else:
        print(f"FAILURE: Edit page status {response.status_code}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load edit page: {e}")

# 6. Verify Create Page
try:
    url = reverse('clients:customer_create')
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Create page loaded")
    else:
        print(f"FAILURE: Create page status {response.status_code}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load create page: {e}")

# 7. Verify Sales Pricelist (Tarifs)
try:
    url = reverse('sales:pricelist_list')
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Pricelist page loaded")
    else:
        print(f"FAILURE: Pricelist page status {response.status_code}")
        if response.status_code in [301, 302]:
            print(f"Redirects to: {response.get('Location', 'Unknown')}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load pricelist page: {e}")

# 8. Verify Ventes Dashboard
try:
    url = reverse('ventes:dashboard')
    print(f"Testing URL: {url}")
    response = c.get(url)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Ventes Dashboard loaded")
    else:
        print(f"FAILURE: Ventes Dashboard status {response.status_code}")
        if response.status_code in [301, 302]:
            print(f"Redirects to: {response.get('Location', 'Unknown')}")
except Exception as e:
    print(f"FAILURE: Could not reverse or load Ventes Dashboard: {e}")
