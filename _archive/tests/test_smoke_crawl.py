#!/usr/bin/env python
"""
Smoke crawl GET - Test que les pages sont cliquables
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()

def create_test_user():
    """Créer un utilisateur de test avec organisation"""
    try:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        org = Organization.objects.create(
            name='Test Organization',
            siret='12345678901234'
        )
        
        Membership.objects.create(
            user=user,
            organization=org,
            role='admin'
        )
        
        return user, org
    except Exception as e:
        print(f"Erreur création utilisateur test: {e}")
        # Utiliser utilisateur existant
        user = User.objects.first()
        org = Organization.objects.first()
        return user, org

def test_smoke_crawl():
    """Test smoke crawl des pages importantes"""
    print("=== SMOKE CRAWL GET ===")
    
    client = Client()
    
    # Créer utilisateur de test
    user, org = create_test_user()
    
    # URLs à tester (sans authentification)
    public_urls = [
        '/',
        '/auth/login/',
    ]
    
    # URLs à tester (avec authentification)
    protected_urls = [
        '/catalogue/produits/',
        '/catalogue/produits/cuvees/',
        '/catalogue/produits/lots/',
        '/catalogue/produits/skus/',
        '/catalogue/produits/referentiels/',
        '/admin/',
    ]
    
    errors = []
    success_count = 0
    total_tests = len(public_urls) + len(protected_urls)
    
    print(f"Test de {total_tests} URLs...")
    
    # Test URLs publiques
    print("\n--- URLs PUBLIQUES ---")
    for url in public_urls:
        try:
            response = client.get(url, follow=True)
            status = response.status_code
            
            if status in [200, 302]:
                print(f"  OK {url} -> {status}")
                success_count += 1
            else:
                print(f"  ERREUR {url} -> {status}")
                errors.append(f"URL {url} retourne {status}")
                
        except Exception as e:
            print(f"  ERREUR {url} -> EXCEPTION: {e}")
            errors.append(f"URL {url} erreur: {e}")
    
    # Test URLs protégées (avec login)
    print("\n--- URLs PROTÉGÉES (avec login) ---")
    if user:
        client.force_login(user)
        
        for url in protected_urls:
            try:
                response = client.get(url, follow=True)
                status = response.status_code
                
                if status in [200, 302]:
                    print(f"  OK {url} -> {status}")
                    success_count += 1
                else:
                    print(f"  ERREUR {url} -> {status}")
                    errors.append(f"URL {url} retourne {status}")
                    
            except Exception as e:
                print(f"  ERREUR {url} -> EXCEPTION: {e}")
                errors.append(f"URL {url} erreur: {e}")
    else:
        print("  Pas d'utilisateur disponible pour les tests protégés")
    
    print(f"\nRésultats: {success_count}/{total_tests} URLs OK")
    
    if errors:
        print("\nERREURS détectées:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("Toutes les URLs testées fonctionnent!")
        return True

if __name__ == '__main__':
    success = test_smoke_crawl()
    sys.exit(0 if success else 1)
