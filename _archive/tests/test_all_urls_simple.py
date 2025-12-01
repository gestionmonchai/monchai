#!/usr/bin/env python
"""
TEST SIMPLE DE TOUTES LES URLs IMPORTANTES
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

def test_url(client, url, description=""):
    """Teste une URL et retourne le résultat"""
    try:
        response = client.get(url, follow=False)
        status = response.status_code
        
        if status == 200:
            return "OK"
        elif status == 302:
            location = response.get('Location', '')
            if '/auth/login' in location:
                return "Redir Login"
            else:
                return f"Redir {location[:30]}"
        elif status == 403:
            return "403 FORBIDDEN"
        elif status == 404:
            return "404 Not Found"
        elif status == 405:
            return "405 Method Not Allowed"
        elif status == 500:
            return "500 Server Error"
        else:
            return f"Status {status}"
            
    except Exception as e:
        return f"Exception: {str(e)[:30]}"

def main():
    print("=" * 80)
    print("TEST DE TOUTES LES URLs IMPORTANTES")
    print("=" * 80)
    
    # URLs importantes à tester
    test_urls = [
        # URL spécifique mentionnée
        ("/admin/viticulture/cuvee/add/", "Admin - Ajouter Cuvée"),
        
        # URLs principales
        ("/", "Accueil"),
        ("/admin/", "Admin Principal"),
        ("/auth/login/", "Login"),
        ("/auth/logout/", "Logout"),
        
        # Catalogue
        ("/catalogue/", "Catalogue Grid"),
        ("/catalogue/produits/", "Produits Dashboard"),
        ("/catalogue/produits/cuvees/", "Produits Cuvées"),
        ("/catalogue/produits/lots/", "Produits Lots"),
        ("/catalogue/produits/skus/", "Produits SKUs"),
        ("/catalogue/produits/referentiels/", "Produits Référentiels"),
        ("/catalogue/lots/", "Liste Lots"),
        ("/catalogue/lots/nouveau/", "Nouveau Lot"),
        
        # Admin Viticulture
        ("/admin/viticulture/", "Admin Viticulture"),
        ("/admin/viticulture/cuvee/", "Admin Cuvées"),
        ("/admin/viticulture/appellation/", "Admin Appellations"),
        ("/admin/viticulture/cepage/", "Admin Cépages"),
        ("/admin/viticulture/parcelle/", "Admin Parcelles"),
        ("/admin/viticulture/unitofmeasure/", "Admin Unités"),
        
        # Admin Catalogue
        ("/admin/catalogue/", "Admin Catalogue"),
        ("/admin/catalogue/lot/", "Admin Lots"),
        
        # Admin Stock
        ("/admin/stock/", "Admin Stock"),
        ("/admin/stock/warehouse/", "Admin Entrepôts"),
        ("/admin/stock/stockitem/", "Admin Stock Items"),
        
        # Admin Sales
        ("/admin/sales/", "Admin Ventes"),
        ("/admin/sales/customer/", "Admin Clients"),
        ("/admin/sales/pricelist/", "Admin Grilles Prix"),
        
        # Admin Accounts
        ("/admin/accounts/", "Admin Comptes"),
        ("/admin/accounts/organization/", "Admin Organisations"),
        ("/admin/accounts/membership/", "Admin Memberships"),
        
        # APIs
        ("/catalogue/api/catalogue/", "API Catalogue"),
        ("/catalogue/api/catalogue/facets/", "API Facettes"),
        
        # Référentiels
        ("/referentiels/", "Référentiels"),
        ("/referentiels/cepages/", "Référentiels Cépages"),
        ("/referentiels/appellations/", "Référentiels Appellations"),
        ("/referentiels/unites/", "Référentiels Unités"),
    ]
    
    # Test sans authentification
    print("\n" + "=" * 50)
    print("TEST SANS AUTHENTIFICATION")
    print("=" * 50)
    
    client_no_auth = Client()
    for url, description in test_urls:
        result = test_url(client_no_auth, url, description)
        print(f"{url:<40} | {result:<20} | {description}")
    
    # Test avec authentification
    print("\n" + "=" * 50)
    print("TEST AVEC AUTHENTIFICATION")
    print("=" * 50)
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("ERREUR: Aucun utilisateur trouvé dans la base")
        return
    
    membership = Membership.objects.filter(user=user).first()
    if not membership:
        print(f"ERREUR: Aucune organisation trouvée pour {user.email}")
        return
    
    print(f"Utilisateur: {user.email}")
    print(f"Organisation: {membership.organization.name}")
    print(f"Rôle: {membership.role}")
    print("-" * 50)
    
    client_auth = Client()
    client_auth.force_login(user)
    
    critical_errors = []
    
    for url, description in test_urls:
        result = test_url(client_auth, url, description)
        print(f"{url:<40} | {result:<20} | {description}")
        
        # Détecter les erreurs critiques
        if "403 FORBIDDEN" in result or "500 Server Error" in result:
            critical_errors.append((url, result, description))
    
    # Résumé des erreurs critiques
    print("\n" + "=" * 80)
    print("RESUME DES ERREURS CRITIQUES")
    print("=" * 80)
    
    if critical_errors:
        print(f"ERREURS DETECTEES: {len(critical_errors)}")
        for url, error, description in critical_errors:
            print(f"  {url} -> {error} ({description})")
    else:
        print("AUCUNE ERREUR CRITIQUE DETECTEE!")
    
    # Test spécial pour l'URL mentionnée
    print("\n" + "=" * 50)
    print("FOCUS SUR L'URL SPECIFIQUE")
    print("=" * 50)
    
    specific_url = "/admin/viticulture/cuvee/add/"
    print(f"URL: {specific_url}")
    
    # Test sans auth
    result_no_auth = test_url(Client(), specific_url)
    print(f"Sans auth: {result_no_auth}")
    
    # Test avec auth
    result_auth = test_url(client_auth, specific_url)
    print(f"Avec auth: {result_auth}")
    
    if "403 FORBIDDEN" in result_auth:
        print("PROBLEME: Erreur 403 même avec utilisateur authentifié!")
        print("Vérifiez les permissions Django Admin pour cet utilisateur.")
    elif "OK" in result_auth:
        print("SUCCESS: L'URL fonctionne correctement!")
    
    print(f"\nSTATISTIQUES:")
    print(f"- URLs testées: {len(test_urls)}")
    print(f"- Erreurs critiques: {len(critical_errors)}")
    print(f"- Utilisateur test: {user.email}")

if __name__ == '__main__':
    main()
