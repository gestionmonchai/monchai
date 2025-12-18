import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf import settings
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, Membership
from apps.clients.models import Customer

def verify_client_pages():
    print("=== Verifying Client Pages ===")
    
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

    # Set current org for the session (middleware usually handles this, but test client needs help)
    # Assuming middleware picks up the user's primary organization or last active one.
    
    c = Client()
    c.force_login(user)
    
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
            # Check redirect
            if response.status_code == 302:
                print(f"Redirects to: {response.url}")
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

if __name__ == '__main__':
    verify_client_pages()
