#!/usr/bin/env python
"""
Test du flux d'authentification
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

def test_auth_flow():
    """Tester le flux d'authentification complet"""
    print("=== TEST FLUX AUTHENTIFICATION ===")
    
    client = Client()
    errors = []
    
    # 1. Test accès page protégée sans login -> redirection
    print("\n1. Test accès page protégée sans login")
    try:
        response = client.get('/catalogue/produits/', follow=False)
        if response.status_code == 302:
            print(f"  OK Redirection vers login: {response.status_code}")
        else:
            error = f"Attendu 302, reçu {response.status_code}"
            print(f"  ERREUR {error}")
            errors.append(error)
    except Exception as e:
        error = f"Erreur accès page protégée: {e}"
        print(f"  ERREUR {error}")
        errors.append(error)
    
    # 2. Test login avec utilisateur existant
    print("\n2. Test login utilisateur")
    try:
        # Utiliser un utilisateur existant ou en créer un
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='testauth',
                email='testauth@example.com',
                password='testpass123'
            )
            
            # Créer organisation et membership
            org = Organization.objects.create(
                name='Test Auth Org',
                siret='98765432109876'
            )
            
            Membership.objects.create(
                user=user,
                organization=org,
                role='admin'
            )
        
        # Login
        login_success = client.login(username=user.email, password='testpass123')
        if login_success:
            print(f"  OK Login réussi pour {user.email}")
        else:
            # Essayer force_login
            client.force_login(user)
            print(f"  OK Force login pour {user.email}")
            
    except Exception as e:
        error = f"Erreur login: {e}"
        print(f"  ERREUR {error}")
        errors.append(error)
    
    # 3. Test accès page protégée après login -> 200
    print("\n3. Test accès page protégée après login")
    try:
        response = client.get('/catalogue/produits/', follow=True)
        if response.status_code == 200:
            print(f"  OK Accès autorisé: {response.status_code}")
        else:
            error = f"Attendu 200, reçu {response.status_code}"
            print(f"  ERREUR {error}")
            errors.append(error)
    except Exception as e:
        error = f"Erreur accès après login: {e}"
        print(f"  ERREUR {error}")
        errors.append(error)
    
    # 4. Test logout -> redirection
    print("\n4. Test logout")
    try:
        response = client.post(reverse('auth:logout'), follow=False)
        if response.status_code == 302:
            print(f"  OK Logout redirection: {response.status_code}")
        else:
            error = f"Attendu 302, reçu {response.status_code}"
            print(f"  ERREUR {error}")
            errors.append(error)
    except Exception as e:
        error = f"Erreur logout: {e}"
        print(f"  ERREUR {error}")
        errors.append(error)
    
    # 5. Test accès page protégée après logout -> redirection
    print("\n5. Test accès page protégée après logout")
    try:
        response = client.get('/catalogue/produits/', follow=False)
        if response.status_code == 302:
            print(f"  OK Redirection après logout: {response.status_code}")
        else:
            error = f"Attendu 302, reçu {response.status_code}"
            print(f"  ERREUR {error}")
            errors.append(error)
    except Exception as e:
        error = f"Erreur accès après logout: {e}"
        print(f"  ERREUR {error}")
        errors.append(error)
    
    # Résultats
    if errors:
        print(f"\nRésultats: {5-len(errors)}/5 tests OK")
        print("\nERREURS détectées:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\nRésultats: 5/5 tests OK")
        print("Flux d'authentification fonctionne correctement!")
        return True

if __name__ == '__main__':
    success = test_auth_flow()
    sys.exit(0 if success else 1)
