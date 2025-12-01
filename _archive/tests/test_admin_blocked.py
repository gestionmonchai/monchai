#!/usr/bin/env python
"""
Test que l'admin sales.Customer est bloqué pour utilisateurs normaux
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()

def test_admin_blocked_for_normal_users():
    """Test que /admin/sales/customer/ est bloqué pour utilisateurs normaux"""
    
    client = Client()
    
    # Test 1: Utilisateur normal (non-superuser)
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"Utilisateur trouvé: {user.email} (superuser: {user.is_superuser})")
    except User.DoesNotExist:
        print("Utilisateur demo@monchai.fr non trouvé")
        return False
    
    # Se connecter
    client.force_login(user)
    print("Connexion réussie")
    
    # Tester l'accès à /admin/sales/customer/
    response = client.get('/admin/sales/customer/')
    print(f"GET /admin/sales/customer/ → Status: {response.status_code}")
    
    if response.status_code == 301:
        location = response.get('Location', '')
        print(f"Redirection 301 vers: {location}")
        
        # Suivre la redirection
        response = client.get(location)
        print(f"GET {location} → Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Redirection vers /clients/ fonctionne")
            return True
        else:
            print(f"❌ Erreur après redirection: {response.status_code}")
            return False
    
    elif response.status_code == 403:
        print("✅ Accès bloqué (403 Forbidden) - Parfait !")
        return True
    
    elif response.status_code == 200:
        print("❌ PROBLÈME: L'admin est encore accessible !")
        return False
    
    else:
        print(f"❌ Status inattendu: {response.status_code}")
        return False

def test_clients_page_works():
    """Test que /clients/ fonctionne bien"""
    
    client = Client()
    user = User.objects.get(email='demo@monchai.fr')
    client.force_login(user)
    
    response = client.get('/clients/')
    print(f"GET /clients/ → Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page /clients/ fonctionne")
        return True
    else:
        print(f"❌ Page /clients/ ne fonctionne pas: {response.status_code}")
        return False

if __name__ == '__main__':
    print("TEST: Admin sales.Customer bloqué pour utilisateurs normaux")
    print("=" * 60)
    
    print("\n1. Test blocage admin")
    admin_blocked = test_admin_blocked_for_normal_users()
    
    print("\n2. Test page clients fonctionne")
    clients_works = test_clients_page_works()
    
    print("\n" + "=" * 60)
    if admin_blocked and clients_works:
        print("🎉 SUCCÈS: Sortie réelle de l'admin réussie !")
        print("   ✅ /admin/sales/customer/ bloqué ou redirigé")
        print("   ✅ /clients/ fonctionne")
    else:
        print("❌ ÉCHEC: Problèmes détectés")
        if not admin_blocked:
            print("   ❌ Admin encore accessible")
        if not clients_works:
            print("   ❌ Page clients ne fonctionne pas")
            
    sys.exit(0 if (admin_blocked and clients_works) else 1)
