#!/usr/bin/env python
"""
Test script pour vérifier que la page /clients/ fonctionne
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

def test_clients_page():
    """Test que la page /clients/ fonctionne avec un utilisateur authentifié"""
    
    # Créer un client de test Django
    client = Client()
    
    # Récupérer un utilisateur existant
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"✅ Utilisateur trouvé: {user.email}")
    except User.DoesNotExist:
        print("❌ Utilisateur demo@monchai.fr non trouvé")
        return False
    
    # Vérifier qu'il a un membership
    membership = Membership.objects.filter(user=user).first()
    if not membership:
        print("❌ Aucun membership trouvé pour cet utilisateur")
        return False
    
    print(f"✅ Membership trouvé: {membership.organization.name} ({membership.role})")
    
    # Se connecter
    login_success = client.force_login(user)
    print(f"✅ Connexion réussie")
    
    # Tester la page /clients/
    response = client.get('/clients/')
    print(f"📄 GET /clients/ → Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page /clients/ fonctionne !")
        
        # Vérifier le contenu
        content = response.content.decode('utf-8')
        if 'Clients' in content:
            print("✅ Contenu 'Clients' trouvé dans la page")
        else:
            print("⚠️  Contenu 'Clients' non trouvé")
            
        return True
    else:
        print(f"❌ Erreur: Status {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Contenu: {response.content.decode('utf-8')[:200]}...")
        return False

def test_admin_redirect():
    """Test que /admin/sales/customer/ redirige vers /clients/"""
    
    client = Client()
    
    # Test de la redirection sans authentification
    response = client.get('/admin/sales/customer/', follow=False)
    print(f"📄 GET /admin/sales/customer/ → Status: {response.status_code}")
    
    if response.status_code == 301:
        location = response.get('Location', '')
        print(f"✅ Redirection 301 vers: {location}")
        
        if location == '/clients/':
            print("✅ Redirection correcte vers /clients/")
            return True
        else:
            print(f"❌ Redirection incorrecte, attendu /clients/, reçu {location}")
            return False
    else:
        print(f"❌ Pas de redirection 301, status: {response.status_code}")
        return False

if __name__ == '__main__':
    print("🧪 Test du refactoring routage - Page Clients")
    print("=" * 50)
    
    print("\n1. Test de la redirection /admin/sales/customer/ → /clients/")
    redirect_ok = test_admin_redirect()
    
    print("\n2. Test de la page /clients/ avec authentification")
    page_ok = test_clients_page()
    
    print("\n" + "=" * 50)
    if redirect_ok and page_ok:
        print("🎉 SUCCÈS: Le refactoring fonctionne !")
        print("   ✅ /admin/sales/customer/ → 301 → /clients/")
        print("   ✅ /clients/ accessible et fonctionnelle")
    else:
        print("❌ ÉCHEC: Le refactoring a des problèmes")
        if not redirect_ok:
            print("   ❌ Redirection 301 non fonctionnelle")
        if not page_ok:
            print("   ❌ Page /clients/ non fonctionnelle")
            
    sys.exit(0 if (redirect_ok and page_ok) else 1)
