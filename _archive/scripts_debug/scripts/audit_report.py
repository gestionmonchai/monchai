#!/usr/bin/env python
"""
Rapport d'audit complet des fonctions d'affichage BDD
"""

import os
import sys
import django
import time

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection
from apps.accounts.models import Organization, Membership
from apps.referentiels.models import Cepage, Parcelle, Unite
from apps.catalogue.models import Lot

User = get_user_model()

def audit_database_queries():
    """Audit des performances des requêtes"""
    print("Audit des performances des requetes...")
    
    # Test des requêtes communes
    queries = [
        ("Cépages - Count", "SELECT COUNT(*) FROM referentiels_cepage"),
        ("Cépages - Liste", "SELECT * FROM referentiels_cepage ORDER BY nom LIMIT 20"),
        ("Cépages - Recherche", "SELECT * FROM referentiels_cepage WHERE nom ILIKE '%sauvignon%'"),
        ("Parcelles - Count", "SELECT COUNT(*) FROM referentiels_parcelle"),
        ("Unités - Count", "SELECT COUNT(*) FROM referentiels_unite"),
    ]
    
    results = []
    
    for name, query in queries:
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            elapsed = (time.time() - start_time) * 1000
            
            result = {
                'query': name,
                'elapsed_ms': round(elapsed, 2),
                'row_count': len(rows),
                'status': 'OK' if elapsed < 100 else 'SLOW'
            }
            
        except Exception as e:
            result = {
                'query': name,
                'elapsed_ms': 0,
                'row_count': 0,
                'status': 'ERROR',
                'error': str(e)
            }
        
        results.append(result)
    
    return results

def audit_permissions():
    """Audit des permissions"""
    print("Audit des permissions...")
    
    client = Client()
    
    # Test sans authentification
    response = client.get('/ref/cepages/')
    no_auth_result = {
        'test': 'Accès sans authentification',
        'status': response.status_code,
        'expected': 302,  # Redirection vers login
        'success': response.status_code == 302
    }
    
    # Créer utilisateur sans membership
    user_no_org, created = User.objects.get_or_create(
        email='noorg@test.com',
        defaults={'first_name': 'No', 'last_name': 'Org'}
    )
    
    client.force_login(user_no_org)
    response = client.get('/ref/cepages/')
    no_org_result = {
        'test': 'Accès sans organisation',
        'status': response.status_code,
        'expected': 302,  # Redirection vers first-run
        'success': response.status_code == 302
    }
    
    return [no_auth_result, no_org_result]

def audit_data_integrity():
    """Audit de l'intégrité des données"""
    print("Audit de l'integrite des donnees...")
    
    results = []
    
    # Vérifier les contraintes
    try:
        # Cépages sans organisation (ne devrait pas exister)
        orphan_cepages = Cepage.objects.filter(organization__isnull=True).count()
        results.append({
            'check': 'Cépages orphelins',
            'count': orphan_cepages,
            'status': 'OK' if orphan_cepages == 0 else 'WARNING'
        })
        
        # Parcelles sans organisation
        orphan_parcelles = Parcelle.objects.filter(organization__isnull=True).count()
        results.append({
            'check': 'Parcelles orphelines',
            'count': orphan_parcelles,
            'status': 'OK' if orphan_parcelles == 0 else 'WARNING'
        })
        
        # Unités sans organisation
        orphan_unites = Unite.objects.filter(organization__isnull=True).count()
        results.append({
            'check': 'Unités orphelines',
            'count': orphan_unites,
            'status': 'OK' if orphan_unites == 0 else 'WARNING'
        })
        
    except Exception as e:
        results.append({
            'check': 'Erreur intégrité',
            'count': 0,
            'status': 'ERROR',
            'error': str(e)
        })
    
    return results

def audit_search_functionality():
    """Audit de la fonctionnalité de recherche"""
    print("Audit de la fonctionnalite de recherche...")
    
    client = Client()
    
    # Créer données de test
    user, created = User.objects.get_or_create(
        email='search@test.com',
        defaults={'first_name': 'Search', 'last_name': 'Test'}
    )
    
    org, created = Organization.objects.get_or_create(name='Search Org')
    
    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={'role': 'admin'}
    )
    
    # Créer cépages de test
    test_cepages = [
        'Cabernet Sauvignon',
        'Sauvignon Blanc', 
        'Chardonnay',
        'Merlot'
    ]
    
    for nom in test_cepages:
        Cepage.objects.get_or_create(
            nom=nom,
            organization=org,
            defaults={'couleur': 'rouge' if 'Sauvignon' in nom else 'blanc'}
        )
    
    client.force_login(user)
    
    # Tests de recherche
    search_tests = [
        ('sauvignon', 'Recherche partielle'),
        ('Cabernet', 'Recherche exacte'),
        ('inexistant', 'Recherche sans résultat'),
        ('', 'Recherche vide'),
    ]
    
    results = []
    
    for term, description in search_tests:
        response = client.get('/ref/cepages/search-ajax/', 
                             {'search': term}, 
                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        success = response.status_code == 200
        
        if success:
            try:
                data = response.json()
                has_count = 'count' in data
                has_html = 'html' in data
                has_pagination = 'pagination' in data
                
                result = {
                    'test': f'{description} ({term})',
                    'status': 'OK',
                    'response_valid': has_count and has_html and has_pagination,
                    'count': data.get('count', 0)
                }
            except:
                result = {
                    'test': f'{description} ({term})',
                    'status': 'ERROR',
                    'response_valid': False,
                    'error': 'Invalid JSON response'
                }
        else:
            result = {
                'test': f'{description} ({term})',
                'status': 'ERROR',
                'response_valid': False,
                'http_status': response.status_code
            }
        
        results.append(result)
    
    return results

def generate_full_report():
    """Génère le rapport complet"""
    print("AUDIT COMPLET - FONCTIONS AFFICHAGE BDD")
    print("=" * 50)
    
    # Tests de performance
    perf_results = audit_database_queries()
    
    print("\nPERFORMANCE DES REQUETES:")
    for result in perf_results:
        status_icon = "OK" if result['status'] == 'OK' else "SLOW" if result['status'] == 'SLOW' else "ERR"
        print(f"  [{status_icon}] {result['query']}: {result['elapsed_ms']}ms ({result['row_count']} rows)")
    
    # Tests de permissions
    perm_results = audit_permissions()
    
    print("\nPERMISSIONS:")
    for result in perm_results:
        status_icon = "OK" if result['success'] else "ERR"
        print(f"  [{status_icon}] {result['test']}: HTTP {result['status']} (attendu: {result['expected']})")
    
    # Tests d'intégrité
    integrity_results = audit_data_integrity()
    
    print("\nINTEGRITE DES DONNEES:")
    for result in integrity_results:
        status_icon = "OK" if result['status'] == 'OK' else "WARN" if result['status'] == 'WARNING' else "ERR"
        print(f"  [{status_icon}] {result['check']}: {result['count']}")
    
    # Tests de recherche
    search_results = audit_search_functionality()
    
    print("\nFONCTIONNALITE DE RECHERCHE:")
    for result in search_results:
        status_icon = "OK" if result['status'] == 'OK' else "ERR"
        valid_icon = "✓" if result.get('response_valid', False) else "✗"
        count_info = f" ({result.get('count', 0)} résultats)" if 'count' in result else ""
        print(f"  [{status_icon}] {result['test']}: {valid_icon}{count_info}")
    
    # Score global
    total_tests = len(perf_results) + len(perm_results) + len(integrity_results) + len(search_results)
    
    successful_tests = (
        len([r for r in perf_results if r['status'] == 'OK']) +
        len([r for r in perm_results if r['success']]) +
        len([r for r in integrity_results if r['status'] == 'OK']) +
        len([r for r in search_results if r['status'] == 'OK'])
    )
    
    score = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\nSCORE GLOBAL: {score:.1f}% ({successful_tests}/{total_tests})")
    
    if score >= 90:
        print("STATUT: EXCELLENT - Système en parfait état")
    elif score >= 75:
        print("STATUT: BON - Quelques optimisations possibles")
    elif score >= 60:
        print("STATUT: MOYEN - Corrections nécessaires")
    else:
        print("STATUT: CRITIQUE - Intervention urgente requise")
    
    # Recommandations
    print("\nRECOMMANDATIONS:")
    
    slow_queries = [r for r in perf_results if r['status'] == 'SLOW']
    if slow_queries:
        print("  • Optimiser les requêtes lentes:")
        for query in slow_queries:
            print(f"    - {query['query']} ({query['elapsed_ms']}ms)")
    
    integrity_issues = [r for r in integrity_results if r['status'] != 'OK']
    if integrity_issues:
        print("  • Corriger les problèmes d'intégrité:")
        for issue in integrity_issues:
            print(f"    - {issue['check']}: {issue['count']} éléments")
    
    search_issues = [r for r in search_results if r['status'] != 'OK']
    if search_issues:
        print("  • Corriger les problèmes de recherche:")
        for issue in search_issues:
            print(f"    - {issue['test']}")
    
    if score >= 90:
        print("  • Système en excellent état, pas d'action requise")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    generate_full_report()
