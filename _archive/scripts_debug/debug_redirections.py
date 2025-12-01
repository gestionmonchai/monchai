#!/usr/bin/env python
"""
DEBUG DETAILLE DES REDIRECTIONS
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, Membership

def debug_user_state(user):
    """Debug complet de l'état utilisateur"""
    print(f"=== DEBUG UTILISATEUR: {user.email} ===")
    print(f"Is authenticated: {user.is_authenticated}")
    print(f"Is active: {user.is_active}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    
    # Memberships
    memberships = Membership.objects.filter(user=user)
    print(f"\nMemberships total: {memberships.count()}")
    
    for membership in memberships:
        print(f"  - Org: {membership.organization.name}")
        print(f"    Role: {membership.role}")
        print(f"    Active: {membership.is_active}")
        print(f"    Org initialized: {membership.organization.is_initialized}")
    
    # Test get_active_membership
    active_membership = user.get_active_membership()
    print(f"\nget_active_membership(): {active_membership}")
    if active_membership:
        print(f"  - Org: {active_membership.organization.name}")
        print(f"  - Role: {active_membership.role}")

def test_specific_urls():
    """Test spécifique des URLs problématiques"""
    print("\n" + "=" * 80)
    print("DEBUG REDIRECTIONS SPECIFIQUES")
    print("=" * 80)
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("ERREUR: Aucun utilisateur")
        return
    
    debug_user_state(user)
    
    # Test avec client authentifié
    client = Client()
    client.force_login(user)
    
    # URLs à tester en détail
    test_urls = [
        "/catalogue/produits/",
        "/catalogue/",
        "/admin/viticulture/cuvee/add/",
    ]
    
    for url in test_urls:
        print(f"\n--- TEST URL: {url} ---")
        
        # Test avec follow=True pour voir toute la chaîne de redirections
        response = client.get(url, follow=True)
        
        print(f"Status final: {response.status_code}")
        print(f"URL finale: {response.request['PATH_INFO']}")
        
        # Afficher la chaîne de redirections
        if hasattr(response, 'redirect_chain') and response.redirect_chain:
            print("Chaîne de redirections:")
            for redirect_url, status_code in response.redirect_chain:
                print(f"  -> {redirect_url} (status {status_code})")
        else:
            print("Aucune redirection")
        
        # Vérifier le contenu de la réponse
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'login' in content.lower():
                print("ATTENTION: Page contient 'login' - possible page de connexion")
            elif 'dashboard' in content.lower():
                print("OK: Page semble être un dashboard")
            elif 'catalogue' in content.lower():
                print("OK: Page semble être le catalogue")
            else:
                print(f"Contenu: {content[:200]}...")

def test_middleware_behavior():
    """Test du comportement des middlewares"""
    print("\n" + "=" * 80)
    print("DEBUG MIDDLEWARES")
    print("=" * 80)
    
    from django.conf import settings
    
    print("Middlewares configurés:")
    for middleware in settings.MIDDLEWARE:
        print(f"  - {middleware}")
    
    # Test d'une requête simple
    User = get_user_model()
    user = User.objects.first()
    
    client = Client()
    client.force_login(user)
    
    # Test avec une URL simple
    print(f"\nTest requête vers /catalogue/produits/")
    response = client.get('/catalogue/produits/', follow=False)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 302:
        location = response.get('Location', '')
        print(f"Redirection vers: {location}")
        
        # Analyser la redirection
        if '/auth/login' in location:
            print("PROBLEME: Redirection vers login malgré authentification")
        elif '/auth/first-run' in location:
            print("PROBLEME: Redirection vers first-run - membership ou org non initialisée")
        else:
            print(f"Redirection inattendue: {location}")

def main():
    test_specific_urls()
    test_middleware_behavior()

if __name__ == '__main__':
    main()
