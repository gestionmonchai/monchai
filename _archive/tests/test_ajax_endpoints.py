#!/usr/bin/env python
"""
Test des endpoints AJAX
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
import json

User = get_user_model()

def test_ajax_endpoints():
    """Tester les endpoints AJAX"""
    print("=== TEST ENDPOINTS AJAX ===")
    
    client = Client()
    errors = []
    
    # Login avec utilisateur existant
    user = User.objects.first()
    if user:
        client.force_login(user)
        print(f"Login avec {user.email}")
    else:
        print("Aucun utilisateur disponible")
        return False
    
    # Endpoints AJAX à tester
    ajax_endpoints = [
        {
            'url': '/catalogue/produits/search/',
            'method': 'GET',
            'params': {'q': 'test'},
            'expected_status': 200,
            'description': 'Recherche produits'
        }
    ]
    
    success_count = 0
    
    for endpoint in ajax_endpoints:
        print(f"\nTest: {endpoint['description']}")
        try:
            # Headers AJAX
            headers = {
                'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
                'HTTP_ACCEPT': 'application/json'
            }
            
            if endpoint['method'] == 'GET':
                response = client.get(
                    endpoint['url'], 
                    endpoint.get('params', {}),
                    **headers
                )
            else:
                response = client.post(
                    endpoint['url'],
                    endpoint.get('params', {}),
                    **headers
                )
            
            status = response.status_code
            expected = endpoint['expected_status']
            
            if status == expected:
                print(f"  OK {endpoint['url']} -> {status}")
                
                # Vérifier contenu si JSON attendu
                if 'application/json' in response.get('Content-Type', ''):
                    try:
                        data = json.loads(response.content)
                        print(f"    JSON valide: {len(str(data))} caractères")
                    except json.JSONDecodeError:
                        print(f"    Attention: Réponse non-JSON")
                
                success_count += 1
            else:
                error = f"{endpoint['url']} retourne {status}, attendu {expected}"
                print(f"  ERREUR {error}")
                errors.append(error)
                
        except Exception as e:
            error = f"Exception sur {endpoint['url']}: {e}"
            print(f"  ERREUR {error}")
            errors.append(error)
    
    # Résultats
    total_tests = len(ajax_endpoints)
    if errors:
        print(f"\nRésultats: {success_count}/{total_tests} endpoints AJAX OK")
        print("\nERREURS détectées:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"\nRésultats: {success_count}/{total_tests} endpoints AJAX OK")
        print("Tous les endpoints AJAX fonctionnent!")
        return True

if __name__ == '__main__':
    success = test_ajax_endpoints()
    sys.exit(0 if success else 1)
