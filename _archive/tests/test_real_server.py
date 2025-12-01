#!/usr/bin/env python
"""
TEST REEL DE TOUTES LES URLs SUR LE SERVEUR EN COURS
"""
import requests
import time
from urllib.parse import urljoin

def test_real_server():
    """Test toutes les URLs sur le serveur réel"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Créer une session pour maintenir les cookies
    session = requests.Session()
    
    print("=" * 80)
    print("TEST REEL DE TOUTES LES URLs SUR SERVEUR EN COURS")
    print("=" * 80)
    
    # URLs à tester
    test_urls = [
        # URL SPECIFIQUE DEMANDEE
        "/admin/viticulture/cuvee/add/",
        
        # URLs principales
        "/",
        "/admin/",
        "/auth/login/",
        "/auth/logout/",
        
        # Catalogue
        "/catalogue/",
        "/catalogue/produits/",
        "/catalogue/produits/cuvees/",
        "/catalogue/produits/lots/",
        "/catalogue/produits/skus/",
        "/catalogue/produits/referentiels/",
        "/catalogue/lots/",
        "/catalogue/lots/nouveau/",
        
        # Admin sections
        "/admin/viticulture/",
        "/admin/viticulture/cuvee/",
        "/admin/viticulture/appellation/",
        "/admin/viticulture/cepage/",
        "/admin/viticulture/parcelle/",
        "/admin/viticulture/unitofmeasure/",
        "/admin/catalogue/",
        "/admin/catalogue/lot/",
        "/admin/stock/",
        "/admin/stock/warehouse/",
        "/admin/stock/sku/",
        "/admin/sales/",
        "/admin/sales/customer/",
        "/admin/sales/pricelist/",
        "/admin/accounts/",
        "/admin/accounts/organization/",
        "/admin/accounts/membership/",
        
        # APIs
        "/catalogue/api/catalogue/",
        "/catalogue/api/catalogue/facets/",
    ]
    
    print(f"Base URL: {base_url}")
    print(f"URLs à tester: {len(test_urls)}")
    
    # Test 1: Sans authentification
    print(f"\n" + "=" * 50)
    print("PHASE 1: TEST SANS AUTHENTIFICATION")
    print("=" * 50)
    
    results_no_auth = []
    
    for url_path in test_urls:
        full_url = urljoin(base_url, url_path)
        try:
            response = session.get(full_url, allow_redirects=False, timeout=10)
            status = response.status_code
            
            if status == 200:
                result = "OK"
            elif status == 302:
                location = response.headers.get('Location', '')
                if 'login' in location:
                    result = "Redir Login"
                else:
                    result = f"Redir {location[:30]}"
            elif status == 403:
                result = "403 FORBIDDEN"
            elif status == 404:
                result = "404 Not Found"
            elif status == 500:
                result = "500 Server Error"
            else:
                result = f"Status {status}"
                
            results_no_auth.append((url_path, result))
            print(f"{url_path:<40} | {result}")
            
        except requests.exceptions.RequestException as e:
            result = f"ERROR: {str(e)[:30]}"
            results_no_auth.append((url_path, result))
            print(f"{url_path:<40} | {result}")
    
    # Test 2: Avec authentification
    print(f"\n" + "=" * 50)
    print("PHASE 2: AUTHENTIFICATION")
    print("=" * 50)
    
    # Obtenir le token CSRF
    login_url = urljoin(base_url, "/auth/login/")
    try:
        login_page = session.get(login_url)
        if login_page.status_code == 200:
            # Extraire le token CSRF
            csrf_token = None
            for line in login_page.text.split('\n'):
                if 'csrfmiddlewaretoken' in line and 'value=' in line:
                    start = line.find('value="') + 7
                    end = line.find('"', start)
                    csrf_token = line[start:end]
                    break
            
            if csrf_token:
                print(f"Token CSRF obtenu: {csrf_token[:20]}...")
                
                # Tenter la connexion
                login_data = {
                    'email': 'demo@monchai.fr',
                    'password': 'test123',  # Mot de passe correct
                    'csrfmiddlewaretoken': csrf_token
                }
                
                login_response = session.post(login_url, data=login_data, allow_redirects=False)
                print(f"Tentative de connexion: Status {login_response.status_code}")
                
                if login_response.status_code == 302:
                    print("OK Connexion réussie (redirection)")
                else:
                    print("ERREUR Échec de connexion")
                    print("Contenu de la réponse:")
                    print(login_response.text[:500])
            else:
                print("ERREUR Token CSRF non trouvé")
        else:
            print(f"ERREUR Impossible d'accéder à la page de login: {login_page.status_code}")
    
    except Exception as e:
        print(f"ERREUR Erreur lors de l'authentification: {e}")
    
    # Test 3: Avec authentification (si réussie)
    print(f"\n" + "=" * 50)
    print("PHASE 3: TEST AVEC AUTHENTIFICATION")
    print("=" * 50)
    
    results_with_auth = []
    critical_errors = []
    
    for url_path in test_urls:
        full_url = urljoin(base_url, url_path)
        try:
            response = session.get(full_url, allow_redirects=False, timeout=10)
            status = response.status_code
            
            if status == 200:
                result = "OK"
            elif status == 302:
                location = response.headers.get('Location', '')
                if 'login' in location:
                    result = "Redir Login"
                else:
                    result = f"Redir {location[:30]}"
            elif status == 403:
                result = "403 FORBIDDEN"
                critical_errors.append((url_path, result))
            elif status == 404:
                result = "404 Not Found"
            elif status == 500:
                result = "500 Server Error"
                critical_errors.append((url_path, result))
            else:
                result = f"Status {status}"
                
            results_with_auth.append((url_path, result))
            
            # Marquer spécialement l'URL demandée
            marker = " *** URL DEMANDEE ***" if url_path == "/admin/viticulture/cuvee/add/" else ""
            print(f"{url_path:<40} | {result}{marker}")
            
        except requests.exceptions.RequestException as e:
            result = f"ERROR: {str(e)[:30]}"
            results_with_auth.append((url_path, result))
            print(f"{url_path:<40} | {result}")
    
    # Résumé final
    print(f"\n" + "=" * 80)
    print("RESUME FINAL - ERREURS CRITIQUES")
    print("=" * 80)
    
    if critical_errors:
        print(f"ERREURS DETECTEES: {len(critical_errors)}")
        for url, error in critical_errors:
            print(f"  ERREUR {url} -> {error}")
            
        # Focus sur l'URL demandée
        url_demandee_error = None
        for url, error in critical_errors:
            if url == "/admin/viticulture/cuvee/add/":
                url_demandee_error = error
                break
        
        if url_demandee_error:
            print(f"\nURL DEMANDEE PROBLEMATIQUE:")
            print(f"   {base_url}/admin/viticulture/cuvee/add/ -> {url_demandee_error}")
            print(f"   DIAGNOSTIC NECESSAIRE!")
        
    else:
        print("OK AUCUNE ERREUR CRITIQUE DETECTEE!")
    
    print(f"\nSTATISTIQUES:")
    print(f"  - URLs testées: {len(test_urls)}")
    print(f"  - Erreurs critiques: {len(critical_errors)}")
    print(f"  - Serveur: {base_url}")
    
    return len(critical_errors) == 0

if __name__ == '__main__':
    success = test_real_server()
    if not success:
        print("\nDES PROBLEMES ONT ETE DETECTES!")
    else:
        print("\nTOUS LES TESTS SONT PASSES!")
