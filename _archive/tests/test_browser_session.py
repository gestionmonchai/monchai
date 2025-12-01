#!/usr/bin/env python
"""
TEST SESSION NAVIGATEUR POUR CREATION CUVEE
"""
import requests
from urllib.parse import urljoin

def test_browser_session():
    """Test avec session navigateur réelle"""
    
    print("=" * 80)
    print("TEST SESSION NAVIGATEUR - CREATION CUVEE")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    # Étape 1: Aller à la page de login
    print("Étape 1: Récupération page de login")
    login_url = urljoin(base_url, "/auth/login/")
    
    try:
        login_page = session.get(login_url)
        print(f"Login page status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            print("ERREUR: Impossible d'accéder à la page de login")
            return
        
        # Extraire le token CSRF
        csrf_token = None
        for line in login_page.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                start = line.find('value="') + 7
                end = line.find('"', start)
                csrf_token = line[start:end]
                break
        
        if not csrf_token:
            print("ERREUR: Token CSRF non trouvé")
            return
            
        print(f"Token CSRF: {csrf_token[:20]}...")
        
    except Exception as e:
        print(f"Erreur récupération login: {e}")
        return
    
    # Étape 2: Se connecter
    print("\nÉtape 2: Connexion utilisateur")
    
    login_data = {
        'email': 'demo@monchai.fr',
        'password': 'test123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    try:
        login_response = session.post(login_url, data=login_data, allow_redirects=False)
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code == 302:
            redirect_location = login_response.headers.get('Location', '')
            print(f"Redirection vers: {redirect_location}")
            
            # Suivre la redirection
            if redirect_location:
                follow_response = session.get(urljoin(base_url, redirect_location))
                print(f"Après redirection: {follow_response.status_code}")
        else:
            print("ERREUR: Connexion échouée")
            print("Contenu réponse:")
            print(login_response.text[:500])
            return
            
    except Exception as e:
        print(f"Erreur connexion: {e}")
        return
    
    # Étape 3: Tester l'URL de création de cuvée
    print("\nÉtape 3: Test URL création cuvée")
    
    cuvee_add_url = urljoin(base_url, "/admin/viticulture/cuvee/add/")
    
    try:
        cuvee_response = session.get(cuvee_add_url, allow_redirects=False)
        print(f"Cuvée add URL status: {cuvee_response.status_code}")
        
        if cuvee_response.status_code == 200:
            print("SUCCESS: URL accessible dans le navigateur!")
            
            # Vérifier le contenu
            content = cuvee_response.text
            if 'Ajouter' in content and ('cuvée' in content.lower() or 'cuvee' in content.lower()):
                print("OK: Formulaire d'ajout présent")
            else:
                print("ATTENTION: Formulaire non détecté")
                
        elif cuvee_response.status_code == 403:
            print("ERREUR: 403 Forbidden")
            print("Contenu erreur:")
            print(cuvee_response.text[:1000])
            
        elif cuvee_response.status_code == 302:
            redirect_location = cuvee_response.headers.get('Location', '')
            print(f"REDIRECTION vers: {redirect_location}")
            
            if '/auth/login' in redirect_location:
                print("Problème: Redirection vers login - session non valide")
            elif '/auth/first-run' in redirect_location:
                print("Problème: Redirection vers first-run - organisation non initialisée")
            else:
                print("Redirection inattendue")
                
        else:
            print(f"Status inattendu: {cuvee_response.status_code}")
            
    except Exception as e:
        print(f"Erreur test cuvée: {e}")
    
    # Étape 4: Tester d'autres URLs admin pour comparaison
    print("\nÉtape 4: Test autres URLs admin")
    
    test_urls = [
        "/admin/",
        "/admin/viticulture/",
        "/admin/viticulture/cuvee/",
        "/admin/accounts/",
    ]
    
    for test_url in test_urls:
        try:
            full_url = urljoin(base_url, test_url)
            response = session.get(full_url, allow_redirects=False)
            
            if response.status_code == 200:
                result = "OK"
            elif response.status_code == 302:
                location = response.headers.get('Location', '')
                result = f"Redir {location[:50]}"
            elif response.status_code == 403:
                result = "403 FORBIDDEN"
            else:
                result = f"Status {response.status_code}"
                
            print(f"{test_url:<30} | {result}")
            
        except Exception as e:
            print(f"{test_url:<30} | ERREUR: {e}")
    
    print(f"\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print("Si l'URL /admin/viticulture/cuvee/add/ fonctionne ici mais pas")
    print("dans votre navigateur, le problème vient de:")
    print("1. Cache navigateur")
    print("2. Cookies/session corrompus")
    print("3. Extensions navigateur")
    print("4. Mode incognito nécessaire")

def main():
    test_browser_session()

if __name__ == '__main__':
    main()
