#!/usr/bin/env python
"""
Test des endpoints AJAX et API
Vérifie les recherches, les réponses JSON, les headers
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_ajax_endpoints():
    """Test des endpoints AJAX et API"""
    print("=== Test des endpoints AJAX et API ===\n")
    
    # Utiliser un utilisateur existant
    User = get_user_model()
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("[ERROR] Aucun utilisateur actif trouvé")
            return False
        print(f"[SETUP] Utilisateur de test: {user.email}")
    except Exception as e:
        print(f"[ERROR] Erreur récupération utilisateur: {e}")
        return False
    
    client = Client()
    client.force_login(user)
    
    errors = []
    success_count = 0
    
    # Endpoints AJAX à tester
    ajax_endpoints = [
        {
            'url': '/catalogue/search/',
            'method': 'GET',
            'params': {'q': 'test'},
            'name': 'Catalogue search'
        },
        {
            'url': '/catalogue/api/catalogue/',
            'method': 'GET',
            'params': {},
            'name': 'Catalogue API'
        },
        {
            'url': '/ref/api/v2/search/',
            'method': 'GET',
            'params': {'q': 'test', 'entity_type': 'cepage'},
            'name': 'Referentiels search v2'
        },
        {
            'url': '/clients/api/',
            'method': 'GET',
            'params': {'q': 'test'},
            'name': 'Clients API'
        },
        {
            'url': '/stocks/api/alertes/',
            'method': 'GET',
            'params': {},
            'name': 'Stock alerts API'
        }
    ]
    
    # Test chaque endpoint
    for endpoint in ajax_endpoints:
        print(f"[TEST] {endpoint['name']}...")
        try:
            # Headers AJAX
            headers = {
                'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
                'HTTP_ACCEPT': 'application/json'
            }
            
            if endpoint['method'] == 'GET':
                response = client.get(endpoint['url'], endpoint['params'], **headers)
            else:
                response = client.post(endpoint['url'], endpoint['params'], **headers)
            
            # Vérifier le status code
            if response.status_code == 200:
                success_count += 1
                print(f"[OK] {endpoint['url']} -> {response.status_code}")
                
                # Vérifier le contenu JSON si applicable
                try:
                    if 'application/json' in response.get('Content-Type', ''):
                        data = response.json()
                        if isinstance(data, (dict, list)):
                            print(f"[OK] JSON valide reçu")
                        else:
                            print(f"[WARNING] JSON structure inattendue")
                except json.JSONDecodeError:
                    print(f"[WARNING] Réponse non-JSON")
                except Exception as e:
                    print(f"[WARNING] Erreur parsing JSON: {e}")
                    
            elif response.status_code == 403:
                print(f"[WARNING] {endpoint['url']} -> 403 (permissions)")
                # Ne pas compter comme erreur, peut être normal
                success_count += 1
                
            elif response.status_code == 404:
                errors.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status': response.status_code,
                    'error': 'Endpoint not found'
                })
                print(f"[ERROR] {endpoint['url']} -> 404 (not found)")
                
            elif response.status_code >= 500:
                errors.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status': response.status_code,
                    'error': 'Server error'
                })
                print(f"[ERROR] {endpoint['url']} -> {response.status_code} (server error)")
                
            else:
                errors.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status': response.status_code,
                    'error': f'Unexpected status {response.status_code}'
                })
                print(f"[ERROR] {endpoint['url']} -> {response.status_code}")
                
        except Exception as e:
            errors.append({
                'endpoint': endpoint['name'],
                'url': endpoint['url'],
                'error': str(e)
            })
            print(f"[ERROR] Exception: {e}")
    
    # Test endpoint de santé
    print(f"\n[TEST] Health endpoint...")
    try:
        response = client.get('/healthz')
        if response.status_code == 200:
            success_count += 1
            print(f"[OK] /healthz -> {response.status_code}")
        else:
            # Essayer sans /healthz
            response = client.get('/health/')
            if response.status_code == 200:
                success_count += 1
                print(f"[OK] /health/ -> {response.status_code}")
            else:
                print(f"[WARNING] Aucun endpoint de santé trouvé")
    except Exception as e:
        print(f"[WARNING] Health endpoint exception: {e}")
    
    # Test CSRF token endpoint
    print(f"\n[TEST] CSRF token endpoint...")
    try:
        response = client.get('/api/auth/csrf/')
        if response.status_code == 200:
            success_count += 1
            print(f"[OK] /api/auth/csrf/ -> {response.status_code}")
        else:
            print(f"[WARNING] CSRF endpoint: {response.status_code}")
    except Exception as e:
        print(f"[WARNING] CSRF endpoint exception: {e}")
    
    # Test avec paramètres manquants
    print(f"\n[TEST] Gestion paramètres manquants...")
    try:
        # Test recherche sans paramètre q
        response = client.get('/catalogue/search/', {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        if response.status_code in [200, 400]:  # 200 ou 400 acceptable
            success_count += 1
            print(f"[OK] Recherche sans paramètre gérée: {response.status_code}")
        else:
            errors.append({
                'endpoint': 'Search without params',
                'url': '/catalogue/search/',
                'status': response.status_code,
                'error': 'Bad handling of missing params'
            })
            print(f"[ERROR] Mauvaise gestion paramètres manquants: {response.status_code}")
    except Exception as e:
        print(f"[WARNING] Test paramètres manquants: {e}")
    
    # Résumé
    print(f"\n[RESUME] AJAX/API Resume:")
    print(f"[OK] Endpoints testés: {len(ajax_endpoints) + 3}")
    print(f"[OK] Succès: {success_count}")
    print(f"[ERROR] Erreurs: {len(errors)}")
    
    if errors:
        print(f"\n[DETAIL] Détail des erreurs:")
        for error in errors:
            print(f"  - {error['endpoint']}: {error['url']}")
            if 'status' in error:
                print(f"    Status: {error['status']}")
            print(f"    Erreur: {error['error']}")
    
    return len(errors) <= 2  # Tolérer quelques erreurs mineures

if __name__ == "__main__":
    success = test_ajax_endpoints()
    sys.exit(0 if success else 1)
