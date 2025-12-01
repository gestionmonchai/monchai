"""
Script de test rapide des endpoints critiques
Vérifie que tous les modules principaux sont accessibles
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()

def test_endpoints():
    """Teste tous les endpoints critiques"""
    
    print("=" * 60)
    print("TEST DES ENDPOINTS CRITIQUES - MON CHAI")
    print("=" * 60)
    print()
    
    # Créer un client de test
    client = Client()
    
    # Créer un utilisateur de test
    try:
        user = User.objects.filter(email='test@test.com').first()
        if not user:
            user = User.objects.create_user(
                username='testuser',
                email='test@test.com',
                password='testpass123'
            )
            user.full_name = 'Test User'
            user.save()
            print("[OK] Utilisateur de test cree")
        else:
            print("[OK] Utilisateur de test existant")
        
        # Créer une organisation de test
        org = Organization.objects.filter(name='Test Org').first()
        if not org:
            org = Organization.objects.create(
                name='Test Org',
                slug='test-org'
            )
            print("[OK] Organisation de test creee")
        else:
            print("[OK] Organisation de test existante")
        
        # Créer un membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': 'admin', 'is_active': True}
        )
        if created:
            print("[OK] Membership cree")
        else:
            print("[OK] Membership existant")
        
        # Connexion
        logged_in = client.login(email='test@test.com', password='testpass123')
        if logged_in:
            print("[OK] Connexion reussie")
        else:
            print("[ERREUR] Echec connexion")
            return
        
    except Exception as e:
        print(f"[ERREUR] Erreur setup: {e}")
        return
    
    print()
    print("-" * 60)
    print("TESTS DES ENDPOINTS")
    print("-" * 60)
    print()
    
    # Liste des endpoints à tester
    endpoints = [
        # Dashboard
        ('Dashboard Viticole', '/dashboard/', 200),
        
        # Devis
        ('Liste Devis', '/ventes/devis/', 200),
        ('Nouveau Devis', '/ventes/devis/nouveau/', 200),
        
        # Clients
        ('Liste Clients', '/ventes/clients/', 200),
        ('Nouveau Client', '/ventes/clients/nouveau/', 200),
        
        # Commandes (placeholders)
        ('Liste Commandes', '/ventes/commandes/', 200),
        ('Nouvelle Commande', '/ventes/commandes/nouveau/', 200),
        
        # Factures (admin)
        ('Admin Factures', '/admin/billing/invoice/', 200),
        
        # Stocks
        ('Dashboard Stocks', '/stocks/', 200),
        ('Liste Transferts', '/stocks/transferts/', 200),
        
        # Catalogue
        ('Liste Cuvées', '/catalogue/cuvees/', 200),
        
        # Configuration
        ('Checklist Onboarding', '/onboarding/checklist/', 200),
        ('Paramètres Facturation', '/settings/billing/', 200),
        ('Paramètres Généraux', '/settings/general/', 200),
        
        # Production
        ('Admin Vendanges', '/admin/production/vendangereception/', 200),
    ]
    
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for name, url, expected_status in endpoints:
        try:
            response = client.get(url, follow=True)
            status = response.status_code
            
            if status == expected_status:
                print(f"[OK] {name:30s} {url:40s} [{status}]")
                results['success'] += 1
            else:
                print(f"[ERREUR] {name:30s} {url:40s} [{status}] (attendu: {expected_status})")
                results['failed'] += 1
                results['errors'].append({
                    'name': name,
                    'url': url,
                    'status': status,
                    'expected': expected_status
                })
        except Exception as e:
            print(f"[ERREUR] {name:30s} {url:40s} [ERREUR: {str(e)[:50]}]")
            results['failed'] += 1
            results['errors'].append({
                'name': name,
                'url': url,
                'error': str(e)
            })
    
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"[OK] Succes: {results['success']}/{len(endpoints)}")
    print(f"[ERREUR] Echecs: {results['failed']}/{len(endpoints)}")
    
    if results['failed'] > 0:
        print()
        print("DETAILS DES ECHECS:")
        print("-" * 60)
        for error in results['errors']:
            print(f"  - {error['name']}")
            print(f"    URL: {error['url']}")
            if 'status' in error:
                print(f"    Status: {error['status']} (attendu: {error['expected']})")
            if 'error' in error:
                print(f"    Erreur: {error['error']}")
            print()
    
    print()
    if results['failed'] == 0:
        print("*** TOUS LES TESTS SONT PASSES ! ***")
    else:
        print(f"*** {results['failed']} test(s) ont echoue ***")
    
    print("=" * 60)

if __name__ == '__main__':
    test_endpoints()
