#!/usr/bin/env python
"""
Script d'audit complet des fonctions d'affichage BDD
Teste tous les endpoints, templates et performances
"""

import os
import sys
import django
import requests
import time
from urllib.parse import urljoin

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership
from apps.referentiels.models import Cepage, Parcelle, Unite
from apps.catalogue.models import Lot
from django.db import connection

User = get_user_model()

class DatabaseViewsAuditor:
    def __init__(self):
        self.client = Client()
        self.base_url = 'http://127.0.0.1:8000'
        self.results = {
            'endpoints': [],
            'templates': [],
            'performance': [],
            'errors': [],
            'recommendations': []
        }
        
    def setup_test_data(self):
        """Crée des données de test si nécessaire"""
        print("Configuration des donnees de test...")
        
        # Utilisateur de test
        user, created = User.objects.get_or_create(
            email='audit@test.com',
            defaults={'first_name': 'Audit', 'last_name': 'Test'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Organisation de test
        org, created = Organization.objects.get_or_create(
            name='Organisation Audit',
            defaults={'description': 'Organisation pour audit'}
        )
        
        # Membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': 'admin'}
        )
        
        # Quelques cépages de test
        test_cepages = [
            {'nom': 'Cabernet Sauvignon', 'couleur': 'rouge'},
            {'nom': 'Chardonnay', 'couleur': 'blanc'},
            {'nom': 'Merlot', 'couleur': 'rouge'},
            {'nom': 'Sauvignon Blanc', 'couleur': 'blanc'},
        ]
        
        for cepage_data in test_cepages:
            Cepage.objects.get_or_create(
                nom=cepage_data['nom'],
                organization=org,
                defaults=cepage_data
            )
        
        return user, org
    
    def test_endpoint(self, url, method='GET', data=None, ajax=False):
        """Teste un endpoint spécifique"""
        print(f"Test endpoint: {method} {url}")
        
        headers = {}
        if ajax:
            headers['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = self.client.get(url, data or {}, **headers)
            elif method == 'POST':
                response = self.client.post(url, data or {}, **headers)
            else:
                response = None
            
            elapsed = (time.time() - start_time) * 1000  # en ms
            
            result = {
                'url': url,
                'method': method,
                'status_code': response.status_code if response else 0,
                'elapsed_ms': round(elapsed, 2),
                'ajax': ajax,
                'success': response and response.status_code < 400,
                'content_type': response.get('Content-Type', '') if response else '',
                'content_length': len(response.content) if response else 0
            }
            
            if response and response.status_code >= 400:
                result['error'] = f"HTTP {response.status_code}"
                if hasattr(response, 'content'):
                    result['error_content'] = response.content.decode()[:200]
            
            self.results['endpoints'].append(result)
            return result
            
        except Exception as e:
            error_result = {
                'url': url,
                'method': method,
                'status_code': 0,
                'elapsed_ms': 0,
                'ajax': ajax,
                'success': False,
                'error': str(e)
            }
            self.results['endpoints'].append(error_result)
            self.results['errors'].append(f"Endpoint {url}: {str(e)}")
            return error_result
    
    def audit_referentiels_endpoints(self):
        """Audit des endpoints référentiels"""
        print("\n📋 AUDIT - Endpoints Référentiels")
        
        endpoints = [
            # Pages principales
            ('/ref/', 'GET'),
            ('/ref/cepages/', 'GET'),
            ('/ref/parcelles/', 'GET'),
            ('/ref/unites/', 'GET'),
            
            # Recherche AJAX
            ('/ref/cepages/search-ajax/', 'GET', {'search': 'sauvignon'}, True),
            ('/ref/cepages/search-ajax/', 'GET', {'search': ''}, True),
            ('/ref/cepages/search-ajax/', 'GET', {'search': 'inexistant'}, True),
            
            # Pagination AJAX
            ('/ref/cepages/search-ajax/', 'GET', {'page': '2'}, True),
        ]
        
        for endpoint in endpoints:
            url = endpoint[0]
            method = endpoint[1]
            data = endpoint[2] if len(endpoint) > 2 else None
            ajax = endpoint[3] if len(endpoint) > 3 else False
            
            self.test_endpoint(url, method, data, ajax)
    
    def audit_catalogue_endpoints(self):
        """Audit des endpoints catalogue"""
        print("\n📦 AUDIT - Endpoints Catalogue")
        
        endpoints = [
            ('/catalogue/', 'GET'),
            ('/catalogue/', 'GET', {'search': 'test'}),
            ('/catalogue/', 'GET', {'couleur': 'rouge'}),
            ('/catalogue/', 'GET', {'sort': 'nom', 'order': 'desc'}),
        ]
        
        for endpoint in endpoints:
            url = endpoint[0]
            method = endpoint[1]
            data = endpoint[2] if len(endpoint) > 2 else None
            
            self.test_endpoint(url, method, data)
    
    def audit_api_v2_endpoints(self):
        """Audit des endpoints API V2"""
        print("\n🚀 AUDIT - Endpoints API V2")
        
        endpoints = [
            ('/ref/api/v2/search/', 'GET', {'q': 'sauvignon', 'entity': 'cepage'}, True),
            ('/ref/api/v2/suggestions/', 'GET', {'q': 'sauv', 'entity': 'cepage'}, True),
            ('/ref/api/v2/facets/', 'GET', {'entity': 'cepage', 'field': 'couleur'}, True),
        ]
        
        for endpoint in endpoints:
            url = endpoint[0]
            method = endpoint[1]
            data = endpoint[2] if len(endpoint) > 2 else None
            ajax = endpoint[3] if len(endpoint) > 3 else False
            
            self.test_endpoint(url, method, data, ajax)
    
    def audit_database_performance(self):
        """Audit des performances base de données"""
        print("\n⚡ AUDIT - Performance Base de Données")
        
        # Test des requêtes lentes
        queries_to_test = [
            ("SELECT COUNT(*) FROM referentiels_cepage", "Count cépages"),
            ("SELECT * FROM referentiels_cepage ORDER BY nom LIMIT 20", "Liste cépages"),
            ("SELECT * FROM referentiels_cepage WHERE nom ILIKE '%sauvignon%'", "Recherche cépages"),
        ]
        
        for query, description in queries_to_test:
            start_time = time.time()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                
                elapsed = (time.time() - start_time) * 1000
                
                perf_result = {
                    'query': description,
                    'elapsed_ms': round(elapsed, 2),
                    'result_count': len(results),
                    'success': True
                }
                
                if elapsed > 100:  # Plus de 100ms
                    perf_result['warning'] = 'Requête lente'
                    self.results['recommendations'].append(
                        f"Optimiser la requête: {description} ({elapsed:.2f}ms)"
                    )
                
                self.results['performance'].append(perf_result)
                
            except Exception as e:
                self.results['performance'].append({
                    'query': description,
                    'elapsed_ms': 0,
                    'result_count': 0,
                    'success': False,
                    'error': str(e)
                })
                self.results['errors'].append(f"Requête {description}: {str(e)}")
    
    def audit_templates(self):
        """Audit des templates"""
        print("\n🎨 AUDIT - Templates et Partials")
        
        template_paths = [
            'templates/referentiels/cepage_list.html',
            'templates/referentiels/partials/cepage_table_rows.html',
            'templates/referentiels/partials/pagination.html',
            'templates/catalogue/catalogue_home.html',
        ]
        
        for template_path in template_paths:
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), template_path)
            
            template_result = {
                'path': template_path,
                'exists': os.path.exists(full_path),
                'size': 0,
                'issues': []
            }
            
            if template_result['exists']:
                template_result['size'] = os.path.getsize(full_path)
                
                # Vérifications basiques
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Vérifications
                    if '{% load' not in content and 'partials' not in template_path:
                        template_result['issues'].append('Aucun template tag chargé')
                    
                    if 'csrf_token' in content and 'form' in content:
                        if '{% csrf_token %}' not in content:
                            template_result['issues'].append('CSRF token manquant')
                    
                    if template_result['size'] > 10000:  # Plus de 10KB
                        template_result['issues'].append('Template volumineux (>10KB)')
                        
                except Exception as e:
                    template_result['issues'].append(f'Erreur lecture: {str(e)}')
            else:
                template_result['issues'].append('Template manquant')
                self.results['errors'].append(f'Template manquant: {template_path}')
            
            self.results['templates'].append(template_result)
    
    def login_test_user(self, user):
        """Connecte l'utilisateur de test"""
        return self.client.force_login(user)
    
    def generate_report(self):
        """Génère le rapport d'audit"""
        print("\n" + "="*60)
        print("📊 RAPPORT D'AUDIT - FONCTIONS AFFICHAGE BDD")
        print("="*60)
        
        # Statistiques générales
        total_endpoints = len(self.results['endpoints'])
        successful_endpoints = len([e for e in self.results['endpoints'] if e['success']])
        failed_endpoints = total_endpoints - successful_endpoints
        
        print(f"\n🔍 ENDPOINTS TESTÉS:")
        print(f"  • Total: {total_endpoints}")
        print(f"  • Succès: {successful_endpoints}")
        print(f"  • Échecs: {failed_endpoints}")
        
        if failed_endpoints > 0:
            print(f"\n❌ ENDPOINTS EN ÉCHEC:")
            for endpoint in self.results['endpoints']:
                if not endpoint['success']:
                    print(f"  • {endpoint['method']} {endpoint['url']} - {endpoint.get('error', 'Erreur inconnue')}")
        
        # Performance
        if self.results['performance']:
            print(f"\n⚡ PERFORMANCE:")
            for perf in self.results['performance']:
                status = "✅" if perf['success'] else "❌"
                warning = f" ⚠️ {perf.get('warning', '')}" if perf.get('warning') else ""
                print(f"  {status} {perf['query']}: {perf['elapsed_ms']}ms{warning}")
        
        # Templates
        template_issues = sum(len(t['issues']) for t in self.results['templates'])
        print(f"\n🎨 TEMPLATES:")
        print(f"  • Vérifiés: {len(self.results['templates'])}")
        print(f"  • Problèmes: {template_issues}")
        
        if template_issues > 0:
            for template in self.results['templates']:
                if template['issues']:
                    print(f"  ❌ {template['path']}:")
                    for issue in template['issues']:
                        print(f"    - {issue}")
        
        # Erreurs générales
        if self.results['errors']:
            print(f"\n🚨 ERREURS DÉTECTÉES:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        # Recommandations
        if self.results['recommendations']:
            print(f"\n💡 RECOMMANDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
        
        # Score global
        total_checks = total_endpoints + len(self.results['templates']) + len(self.results['performance'])
        successful_checks = successful_endpoints + len([t for t in self.results['templates'] if not t['issues']]) + len([p for p in self.results['performance'] if p['success']])
        
        if total_checks > 0:
            score = (successful_checks / total_checks) * 100
            print(f"\n🎯 SCORE GLOBAL: {score:.1f}% ({successful_checks}/{total_checks})")
            
            if score >= 90:
                print("🎉 EXCELLENT - Système en très bon état")
            elif score >= 75:
                print("✅ BON - Quelques améliorations possibles")
            elif score >= 60:
                print("⚠️ MOYEN - Corrections nécessaires")
            else:
                print("🚨 CRITIQUE - Intervention urgente requise")
        
        print("\n" + "="*60)
        return self.results

def main():
    print("AUDIT COMPLET - FONCTIONS AFFICHAGE BDD")
    print("="*50)
    
    auditor = DatabaseViewsAuditor()
    
    # Configuration
    user, org = auditor.setup_test_data()
    auditor.login_test_user(user)
    
    # Tests
    auditor.audit_referentiels_endpoints()
    auditor.audit_catalogue_endpoints()
    auditor.audit_api_v2_endpoints()
    auditor.audit_database_performance()
    auditor.audit_templates()
    
    # Rapport
    results = auditor.generate_report()
    
    return results

if __name__ == '__main__':
    main()
