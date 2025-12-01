#!/usr/bin/env python
"""
Test de la recherche avancée par champs
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

def test_advanced_search():
    """Test de la recherche avancée par champs"""
    print("Test de la recherche avancée par champs")
    print("=" * 50)
    
    client = Client()
    
    # Créer utilisateur de test
    user, created = User.objects.get_or_create(
        email='search@test.com',
        defaults={'first_name': 'Search', 'last_name': 'Test'}
    )
    
    # Créer organisation
    org, created = Organization.objects.get_or_create(
        name='Test Search Org'
    )
    
    # Membership
    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={'role': 'admin'}
    )
    
    # Créer quelques cépages de test
    test_cepages = [
        {'nom': 'Cabernet Sauvignon', 'code': 'CS', 'couleur': 'rouge', 'notes': 'Cépage noble de Bordeaux'},
        {'nom': 'Sauvignon Blanc', 'code': 'SB', 'couleur': 'blanc', 'notes': 'Cépage aromatique de Loire'},
        {'nom': 'Chardonnay', 'code': 'CH', 'couleur': 'blanc', 'notes': 'Cépage bourguignon'},
        {'nom': 'Merlot', 'code': 'ME', 'couleur': 'rouge', 'notes': 'Cépage souple'},
        {'nom': 'Pinot Noir', 'code': 'PN', 'couleur': 'rouge', 'notes': 'Cépage délicat'},
    ]
    
    for cepage_data in test_cepages:
        Cepage.objects.get_or_create(
            nom=cepage_data['nom'],
            organization=org,
            defaults=cepage_data
        )
    
    client.force_login(user)
    
    # Tests des différents filtres
    test_cases = [
        # Test 1: Filtre par nom
        {
            'params': {'nom': 'Sauvignon'},
            'description': 'Filtre par nom "Sauvignon"',
            'expected_count': 2  # Cabernet Sauvignon + Sauvignon Blanc
        },
        
        # Test 2: Filtre par code
        {
            'params': {'code': 'C'},
            'description': 'Filtre par code contenant "C"',
            'expected_count': 2  # CS + CH
        },
        
        # Test 3: Filtre par couleur
        {
            'params': {'couleur': 'blanc'},
            'description': 'Filtre par couleur "blanc"',
            'expected_count': 2  # Sauvignon Blanc + Chardonnay
        },
        
        # Test 4: Filtre par notes
        {
            'params': {'notes': 'Bordeaux'},
            'description': 'Filtre par notes contenant "Bordeaux"',
            'expected_count': 1  # Cabernet Sauvignon
        },
        
        # Test 5: Filtres combinés
        {
            'params': {'couleur': 'rouge', 'notes': 'souple'},
            'description': 'Filtres combinés: couleur rouge + notes "souple"',
            'expected_count': 1  # Merlot
        },
        
        # Test 6: Recherche globale
        {
            'params': {'search': 'noir'},
            'description': 'Recherche globale "noir"',
            'expected_count': 1  # Pinot Noir
        },
        
        # Test 7: Tri
        {
            'params': {'sort': 'code', 'order': 'asc'},
            'description': 'Tri par code croissant',
            'expected_count': 5  # Tous les cépages
        },
        
        # Test 8: Aucun filtre
        {
            'params': {},
            'description': 'Aucun filtre (tous les cépages)',
            'expected_count': 5
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Paramètres: {test_case['params']}")
        
        # Test de la page principale
        response = client.get('/ref/cepages/', test_case['params'])
        page_success = response.status_code == 200
        
        # Test de l'endpoint AJAX
        ajax_response = client.get('/ref/cepages/search-ajax/', 
                                  test_case['params'], 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ajax_success = ajax_response.status_code == 200
        
        result = {
            'test': test_case['description'],
            'params': test_case['params'],
            'page_status': response.status_code,
            'ajax_status': ajax_response.status_code,
            'page_success': page_success,
            'ajax_success': ajax_success,
            'expected_count': test_case['expected_count']
        }
        
        if ajax_success:
            try:
                ajax_data = ajax_response.json()
                result['actual_count'] = ajax_data.get('count', 0)
                result['has_results'] = ajax_data.get('has_results', False)
                result['count_match'] = result['actual_count'] == test_case['expected_count']
            except:
                result['ajax_data_error'] = True
                result['count_match'] = False
        else:
            result['count_match'] = False
        
        results.append(result)
        
        # Affichage du résultat
        status_page = "✅" if page_success else "❌"
        status_ajax = "✅" if ajax_success else "❌"
        status_count = "✅" if result.get('count_match', False) else "❌"
        
        print(f"  Page: {status_page} (HTTP {response.status_code})")
        print(f"  AJAX: {status_ajax} (HTTP {ajax_response.status_code})")
        if 'actual_count' in result:
            print(f"  Résultats: {status_count} ({result['actual_count']}/{test_case['expected_count']})")
    
    # Résumé
    print("\n" + "=" * 50)
    print("RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    total_tests = len(results)
    page_success_count = sum(1 for r in results if r['page_success'])
    ajax_success_count = sum(1 for r in results if r['ajax_success'])
    count_success_count = sum(1 for r in results if r.get('count_match', False))
    
    print(f"Pages principales: {page_success_count}/{total_tests}")
    print(f"Endpoints AJAX: {ajax_success_count}/{total_tests}")
    print(f"Comptages corrects: {count_success_count}/{total_tests}")
    
    overall_score = (page_success_count + ajax_success_count + count_success_count) / (total_tests * 3) * 100
    print(f"\nScore global: {overall_score:.1f}%")
    
    if overall_score >= 90:
        print("🎉 EXCELLENT - Recherche avancée parfaitement fonctionnelle")
    elif overall_score >= 75:
        print("✅ BON - Quelques ajustements possibles")
    elif overall_score >= 60:
        print("⚠️ MOYEN - Corrections nécessaires")
    else:
        print("🚨 CRITIQUE - Problèmes majeurs détectés")
    
    # Test des URLs générées
    print(f"\nTest des URLs générées:")
    print(f"  Nom=Sauvignon: /ref/cepages/?nom=Sauvignon")
    print(f"  Code=CH: /ref/cepages/?code=CH")
    print(f"  Couleur=rouge: /ref/cepages/?couleur=rouge")
    print(f"  Combiné: /ref/cepages/?nom=Sauvignon&couleur=blanc")
    print(f"  Tri: /ref/cepages/?sort=code&order=desc")
    
    return results

if __name__ == '__main__':
    test_advanced_search()
