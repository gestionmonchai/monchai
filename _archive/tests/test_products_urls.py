#!/usr/bin/env python
"""
Test des URLs produits pour détecter les erreurs 403
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

def test_products_urls():
    """Test les URLs produits avec un utilisateur authentifié"""
    
    # Créer un client de test
    client = Client()
    
    # URLs produits à tester
    products_urls = [
        '/catalogue/produits/',
        '/catalogue/produits/cuvees/',
        '/catalogue/produits/lots/',
        '/catalogue/produits/skus/',
        '/catalogue/produits/referentiels/',
        '/catalogue/produits/search/',
    ]
    
    print("=== TEST URLs PRODUITS SANS AUTHENTIFICATION ===")
    for url in products_urls:
        try:
            response = client.get(url)
            print(f"{url} -> Status: {response.status_code}")
            if response.status_code == 403:
                print(f"  ❌ ERREUR 403 - Accès refusé")
            elif response.status_code == 302:
                print(f"  🔄 Redirection vers: {response.get('Location', 'N/A')}")
            elif response.status_code == 200:
                print(f"  ✅ OK")
            else:
                print(f"  ⚠️  Status inattendu: {response.status_code}")
        except Exception as e:
            print(f"{url} -> ERREUR: {e}")
    
    # Test avec utilisateur authentifié
    User = get_user_model()
    
    # Chercher un utilisateur existant ou en créer un
    try:
        user = User.objects.first()
        if not user:
            print("\n❌ Aucun utilisateur trouvé dans la base")
            return
            
        # Chercher son organisation
        membership = Membership.objects.filter(user=user).first()
        if not membership:
            print(f"\n❌ Aucune organisation trouvée pour l'utilisateur {user.email}")
            return
            
        print(f"\n=== TEST URLs PRODUITS AVEC UTILISATEUR {user.email} ===")
        print(f"Organisation: {membership.organization.name}")
        print(f"Rôle: {membership.role}")
        
        # Se connecter
        client.force_login(user)
        
        for url in products_urls:
            try:
                response = client.get(url)
                print(f"{url} -> Status: {response.status_code}")
                if response.status_code == 403:
                    print(f"  ❌ ERREUR 403 - Accès refusé même authentifié!")
                elif response.status_code == 302:
                    print(f"  🔄 Redirection vers: {response.get('Location', 'N/A')}")
                elif response.status_code == 200:
                    print(f"  ✅ OK")
                elif response.status_code == 500:
                    print(f"  💥 ERREUR SERVEUR 500")
                else:
                    print(f"  ⚠️  Status inattendu: {response.status_code}")
            except Exception as e:
                print(f"{url} -> ERREUR: {e}")
                
    except Exception as e:
        print(f"\nErreur lors du test avec utilisateur: {e}")

if __name__ == '__main__':
    test_products_urls()
