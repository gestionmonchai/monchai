#!/usr/bin/env python
"""
TEST DIRECT D'ACCES AUX URLs AVEC DJANGO CLIENT
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

def test_direct_access():
    """Test direct avec Django Client"""
    
    print("=" * 80)
    print("TEST DIRECT D'ACCES AUX URLs")
    print("=" * 80)
    
    User = get_user_model()
    
    # Récupérer l'utilisateur
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"Utilisateur: {user.email}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        
        # Vérifier les permissions spécifiques
        can_add_cuvee = user.has_perm('viticulture.add_cuvee')
        print(f"Peut ajouter cuvée: {can_add_cuvee}")
        
    except User.DoesNotExist:
        print("ERREUR: Utilisateur non trouvé")
        return False
    
    # Créer le client et se connecter
    client = Client()
    client.force_login(user)
    
    print(f"\n=== TEST URL SPECIFIQUE ===")
    
    # Test de l'URL spécifique
    url = "/admin/viticulture/cuvee/add/"
    print(f"Test: {url}")
    
    try:
        response = client.get(url, follow=True)
        print(f"Status final: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: URL accessible!")
            
            # Vérifier le contenu
            content = response.content.decode('utf-8')
            if 'Ajouter' in content and 'cuvée' in content.lower():
                print("OK: Page d'ajout de cuvée détectée")
            elif 'login' in content.lower():
                print("PROBLEME: Page de login au lieu du formulaire")
            else:
                print("ATTENTION: Contenu inattendu")
                print(f"Titre de la page: {content[content.find('<title>')+7:content.find('</title>')]}")
                
        elif response.status_code == 403:
            print("ERREUR: 403 Forbidden - Problème de permissions")
            
        elif response.status_code == 302:
            print("ERREUR: Redirection inattendue")
            
        else:
            print(f"ERREUR: Status inattendu {response.status_code}")
            
        # Afficher la chaîne de redirections
        if hasattr(response, 'redirect_chain') and response.redirect_chain:
            print("Redirections:")
            for redirect_url, status_code in response.redirect_chain:
                print(f"  -> {redirect_url} (status {status_code})")
                
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False
    
    # Test d'autres URLs admin importantes
    print(f"\n=== TEST AUTRES URLs ADMIN ===")
    
    admin_urls = [
        "/admin/",
        "/admin/viticulture/",
        "/admin/viticulture/cuvee/",
        "/admin/viticulture/appellation/",
        "/admin/accounts/",
    ]
    
    for url in admin_urls:
        try:
            response = client.get(url, follow=False)
            status = response.status_code
            
            if status == 200:
                result = "OK"
            elif status == 302:
                location = response.get('Location', '')
                result = f"Redir {location[:30]}"
            elif status == 403:
                result = "403 FORBIDDEN"
            else:
                result = f"Status {status}"
                
            print(f"{url:<35} | {result}")
            
        except Exception as e:
            print(f"{url:<35} | ERREUR: {e}")
    
    # Test URLs catalogue
    print(f"\n=== TEST URLs CATALOGUE ===")
    
    catalogue_urls = [
        "/catalogue/",
        "/catalogue/produits/",
        "/catalogue/produits/cuvees/",
        "/catalogue/lots/",
    ]
    
    for url in catalogue_urls:
        try:
            response = client.get(url, follow=False)
            status = response.status_code
            
            if status == 200:
                result = "OK"
            elif status == 302:
                location = response.get('Location', '')
                if '/auth/login' in location:
                    result = "Redir Login"
                elif '/auth/first-run' in location:
                    result = "Redir First-Run"
                else:
                    result = f"Redir {location[:30]}"
            elif status == 403:
                result = "403 FORBIDDEN"
            else:
                result = f"Status {status}"
                
            print(f"{url:<35} | {result}")
            
        except Exception as e:
            print(f"{url:<35} | ERREUR: {e}")
    
    return response.status_code == 200

def main():
    success = test_direct_access()
    
    print(f"\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if success:
        print("SUCCESS: L'URL /admin/viticulture/cuvee/add/ fonctionne!")
    else:
        print("ECHEC: L'URL /admin/viticulture/cuvee/add/ ne fonctionne pas")
        
        print("\nDIAGNOSTIC SUPPLEMENTAIRE NECESSAIRE:")
        print("1. Vérifier la configuration Django Admin")
        print("2. Vérifier les permissions utilisateur")
        print("3. Vérifier les middlewares")
        print("4. Tester manuellement dans le navigateur")

if __name__ == '__main__':
    main()
