#!/usr/bin/env python
"""
TEST SIMPLE ADMIN VITICULTURE
Test rapide pour identifier le probleme 403
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.contrib.admin import site
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from apps.viticulture.models import Cuvee
from apps.accounts.models import Organization, Membership

User = get_user_model()

def test_admin_registration():
    """Test si Cuvee est enregistre dans l'admin"""
    print("=== TEST ENREGISTREMENT ADMIN ===")
    
    registered_models = site._registry
    if Cuvee in registered_models:
        print("[OK] Cuvee est enregistre dans l'admin")
        return True
    else:
        print("[ERROR] Cuvee n'est PAS enregistre dans l'admin")
        return False

def test_urls():
    """Test des URLs admin"""
    print("\n=== TEST URLS ===")
    
    try:
        url = reverse('admin:viticulture_cuvee_add')
        print(f"[OK] URL admin:viticulture_cuvee_add -> {url}")
        return True
    except Exception as e:
        print(f"[ERROR] URL non trouvee: {e}")
        return False

def setup_test_user():
    """Configure un utilisateur de test"""
    print("\n=== SETUP UTILISATEUR TEST ===")
    
    # Utiliser une organisation existante
    org = Organization.objects.first()
    if not org:
        print("[ERROR] Aucune organisation trouvee")
        return None
    
    print(f"[OK] Organisation: {org.name}")
    
    # Creer/mettre a jour l'utilisateur
    user, created = User.objects.get_or_create(
        email='demo@monchai.fr',
        defaults={
            'username': 'demo',
            'first_name': 'Demo',
            'last_name': 'User',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    # Forcer les permissions
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password('admin123')
    user.save()
    
    print(f"[OK] Utilisateur: {user.email}")
    print(f"  - is_staff: {user.is_staff}")
    print(f"  - is_superuser: {user.is_superuser}")
    
    # Membership
    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={
            'role': Membership.Role.OWNER,
            'is_active': True
        }
    )
    
    if not created:
        membership.role = Membership.Role.OWNER
        membership.is_active = True
        membership.save()
    
    print(f"[OK] Membership: {membership.role}")
    
    return user

def test_client_access(user):
    """Test acces avec Django Client"""
    print("\n=== TEST ACCES CLIENT ===")
    
    if not user:
        print("[ERROR] Pas d'utilisateur pour le test")
        return False
    
    client = Client()
    
    # Test sans auth
    response = client.get('/admin/viticulture/cuvee/add/')
    print(f"Sans auth: {response.status_code}")
    
    # Test avec auth
    client.force_login(user)
    response = client.get('/admin/viticulture/cuvee/add/')
    print(f"Avec auth: {response.status_code}")
    
    if response.status_code == 200:
        print("[OK] Acces reussi!")
        return True
    elif response.status_code == 302:
        location = response.get('Location', 'N/A')
        print(f"[REDIRECT] Vers: {location}")
    elif response.status_code == 403:
        print("[ERROR] 403 Forbidden")
        # Analyser le contenu
        content = response.content.decode('utf-8')[:500]
        print(f"Contenu: {content}")
    
    return response.status_code == 200

def test_admin_permissions(user):
    """Test permissions admin specifiques"""
    print("\n=== TEST PERMISSIONS ADMIN ===")
    
    if not user:
        print("[ERROR] Pas d'utilisateur")
        return False
    
    # Simuler une requete
    from django.http import HttpRequest
    request = HttpRequest()
    request.user = user
    
    # Obtenir l'admin Cuvee
    if Cuvee not in site._registry:
        print("[ERROR] Cuvee non enregistre")
        return False
    
    cuvee_admin = site._registry[Cuvee]
    
    # Tester les permissions
    perms = {
        'view': cuvee_admin.has_view_permission(request),
        'add': cuvee_admin.has_add_permission(request),
        'change': cuvee_admin.has_change_permission(request),
        'delete': cuvee_admin.has_delete_permission(request),
    }
    
    print("Permissions admin:")
    for perm_name, has_perm in perms.items():
        status = "[OK]" if has_perm else "[ERROR]"
        print(f"  {status} {perm_name}: {has_perm}")
    
    return all(perms.values())

def main():
    """Fonction principale"""
    print("TEST SIMPLE ADMIN VITICULTURE")
    print("Diagnostic du probleme 403")
    
    # Tests
    tests = [
        ("Enregistrement Admin", test_admin_registration),
        ("URLs Admin", test_urls),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"[ERROR] {test_name}: {e}")
            results[test_name] = False
    
    # Setup utilisateur
    user = setup_test_user()
    
    # Tests avec utilisateur
    if user:
        tests_user = [
            ("Permissions Admin", lambda: test_admin_permissions(user)),
            ("Acces Client", lambda: test_client_access(user)),
        ]
        
        for test_name, test_func in tests_user:
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
                results[test_name] = False
    
    # Resume
    print("\n=== RESUME ===")
    for test_name, result in results.items():
        status = "[OK]" if result else "[ERROR]"
        print(f"{status} {test_name}")
    
    # Recommandations
    if all(results.values()):
        print("\n[OK] Tous les tests passent!")
        print("Le probleme pourrait etre:")
        print("  - Cache navigateur")
        print("  - Session expiree")
        print("  - Middleware custom")
        print("\nEssayez:")
        print("  1. Onglet prive")
        print("  2. Vider cache")
        print("  3. Se reconnecter avec admin123")
    else:
        print("\n[ERROR] Des tests ont echoue")
        print("Verifiez les erreurs ci-dessus")

if __name__ == '__main__':
    main()
