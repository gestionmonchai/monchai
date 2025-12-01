#!/usr/bin/env python
"""
Audit simple des fonctions d'affichage BDD
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership
from apps.referentiels.models import Cepage

User = get_user_model()

def test_search_endpoints():
    """Test des endpoints de recherche"""
    print("Test des endpoints de recherche...")
    
    client = Client()
    
    # Créer utilisateur de test
    user, created = User.objects.get_or_create(
        email='test@audit.com',
        defaults={'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Créer organisation
    org, created = Organization.objects.get_or_create(
        name='Test Org'
    )
    
    # Membership
    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={'role': 'admin'}
    )
    
    # Créer quelques cépages
    Cepage.objects.get_or_create(
        nom='Sauvignon Blanc',
        organization=org,
        defaults={'couleur': 'blanc'}
    )
    
    # Login
    client.force_login(user)
    
    # Tests
    results = []
    
    # Test 1: Page liste cépages
    print("Test 1: Page liste cepages")
    response = client.get('/ref/cepages/')
    results.append({
        'test': 'Page liste cépages',
        'url': '/ref/cepages/',
        'status': response.status_code,
        'success': response.status_code == 200
    })
    
    # Test 2: Recherche AJAX
    print("Test 2: Recherche AJAX")
    response = client.get('/ref/cepages/search-ajax/', 
                         {'search': 'sauvignon'}, 
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    results.append({
        'test': 'Recherche AJAX',
        'url': '/ref/cepages/search-ajax/',
        'status': response.status_code,
        'success': response.status_code == 200
    })
    
    # Test 3: Recherche vide
    print("Test 3: Recherche vide")
    response = client.get('/ref/cepages/search-ajax/', 
                         {'search': ''}, 
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    results.append({
        'test': 'Recherche vide',
        'url': '/ref/cepages/search-ajax/',
        'status': response.status_code,
        'success': response.status_code == 200
    })
    
    # Test 4: API V2 (si disponible)
    print("Test 4: API V2")
    response = client.get('/ref/api/v2/search/', 
                         {'q': 'sauvignon', 'entity': 'cepage'}, 
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    results.append({
        'test': 'API V2',
        'url': '/ref/api/v2/search/',
        'status': response.status_code,
        'success': response.status_code in [200, 503]  # 503 = V2 désactivé
    })
    
    return results

def check_templates():
    """Vérification des templates"""
    print("Verification des templates...")
    
    templates_to_check = [
        'templates/referentiels/cepage_list.html',
        'templates/referentiels/partials/cepage_table_rows.html',
        'templates/referentiels/partials/pagination.html'
    ]
    
    results = []
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for template in templates_to_check:
        full_path = os.path.join(base_path, template)
        exists = os.path.exists(full_path)
        
        results.append({
            'template': template,
            'exists': exists,
            'path': full_path
        })
    
    return results

def main():
    print("AUDIT SIMPLE - FONCTIONS AFFICHAGE BDD")
    print("=" * 45)
    
    # Test des endpoints
    endpoint_results = test_search_endpoints()
    
    print("\nRESULTATS ENDPOINTS:")
    for result in endpoint_results:
        status = "OK" if result['success'] else "ERREUR"
        print(f"  {result['test']}: {status} (HTTP {result['status']})")
    
    # Test des templates
    template_results = check_templates()
    
    print("\nRESULTATS TEMPLATES:")
    for result in template_results:
        status = "OK" if result['exists'] else "MANQUANT"
        print(f"  {result['template']}: {status}")
    
    # Résumé
    endpoint_success = sum(1 for r in endpoint_results if r['success'])
    template_success = sum(1 for r in template_results if r['exists'])
    
    total_tests = len(endpoint_results) + len(template_results)
    total_success = endpoint_success + template_success
    
    print(f"\nRESUME:")
    print(f"  Endpoints: {endpoint_success}/{len(endpoint_results)}")
    print(f"  Templates: {template_success}/{len(template_results)}")
    print(f"  Total: {total_success}/{total_tests}")
    
    score = (total_success / total_tests) * 100 if total_tests > 0 else 0
    print(f"  Score: {score:.1f}%")
    
    if score >= 90:
        print("  Statut: EXCELLENT")
    elif score >= 75:
        print("  Statut: BON")
    elif score >= 60:
        print("  Statut: MOYEN")
    else:
        print("  Statut: CRITIQUE")

if __name__ == '__main__':
    main()
