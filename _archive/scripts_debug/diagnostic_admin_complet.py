#!/usr/bin/env python
"""
DIAGNOSTIC COMPLET ADMIN VITICULTURE
Analyse complète pour résoudre le problème 403 sur /admin/viticulture/cuvee/add/
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
from django.urls import reverse, NoReverseMatch
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from apps.viticulture.models import Cuvee
from apps.accounts.models import Organization

User = get_user_model()

def print_section(title):
    """Affiche une section avec séparateur"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def diagnostic_admin_registration():
    """Vérifie l'enregistrement des modèles dans l'admin"""
    print_section("DIAGNOSTIC ENREGISTREMENT ADMIN")
    
    # Vérifier que Cuvee est enregistré
    registered_models = site._registry
    print(f"Nombre total de modèles enregistrés: {len(registered_models)}")
    
    viticulture_models = []
    for model, admin_class in registered_models.items():
        if model._meta.app_label == 'viticulture':
            viticulture_models.append((model.__name__, admin_class.__class__.__name__))
    
    print(f"\nModèles viticulture enregistrés: {len(viticulture_models)}")
    for model_name, admin_name in viticulture_models:
        print(f"  - {model_name}: {admin_name}")
    
    # Vérifier spécifiquement Cuvee
    if Cuvee in registered_models:
        cuvee_admin = registered_models[Cuvee]
        print(f"[OK] Cuvee est enregistre avec: {cuvee_admin.__class__.__name__}")
        print(f"  - Module: {cuvee_admin.__class__.__module__}")
        print(f"  - Permissions add: {hasattr(cuvee_admin, 'has_add_permission')}")
        print(f"  - Permissions change: {hasattr(cuvee_admin, 'has_change_permission')}")
    else:
        print("\n[ERROR] ERREUR: Cuvee n'est PAS enregistre dans l'admin!")
        return False
    
    return True

def diagnostic_urls():
    """Vérifie les URLs admin"""
    print_section("DIAGNOSTIC URLS ADMIN")
    
    try:
        # Test des URLs de base
        admin_index = reverse('admin:index')
        print(f"✓ admin:index -> {admin_index}")
        
        viticulture_index = reverse('admin:viticulture_cuvee_changelist')
        print(f"✓ admin:viticulture_cuvee_changelist -> {viticulture_index}")
        
        cuvee_add = reverse('admin:viticulture_cuvee_add')
        print(f"✓ admin:viticulture_cuvee_add -> {cuvee_add}")
        
        return True
        
    except NoReverseMatch as e:
        print(f"✗ ERREUR URL: {e}")
        return False

def diagnostic_user_permissions():
    """Vérifie les permissions utilisateur"""
    print_section("DIAGNOSTIC PERMISSIONS UTILISATEUR")
    
    # Chercher l'utilisateur de test
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"✓ Utilisateur trouvé: {user.email}")
        print(f"  - is_active: {user.is_active}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_superuser: {user.is_superuser}")
        
        # Vérifier l'organisation
        if hasattr(user, 'get_active_membership'):
            membership = user.get_active_membership()
            if membership:
                print(f"  - Organisation: {membership.organization.name}")
            else:
                print("  - ⚠️  Pas de membership actif")
        
        # Vérifier les permissions spécifiques
        content_type = ContentType.objects.get_for_model(Cuvee)
        permissions = Permission.objects.filter(content_type=content_type)
        
        print(f"\nPermissions disponibles pour Cuvee:")
        for perm in permissions:
            has_perm = user.has_perm(f'viticulture.{perm.codename}')
            status = "✓" if has_perm else "✗"
            print(f"  {status} {perm.codename}: {perm.name}")
        
        return user
        
    except User.DoesNotExist:
        print("✗ ERREUR: Utilisateur demo@monchai.fr non trouvé!")
        return None

def diagnostic_client_test(user):
    """Test avec Django Client"""
    print_section("TEST DJANGO CLIENT")
    
    if not user:
        print("✗ Pas d'utilisateur pour le test")
        return False
    
    client = Client()
    
    # Test sans authentification
    response = client.get('/admin/viticulture/cuvee/add/')
    print(f"Sans auth - Status: {response.status_code}")
    if response.status_code == 302:
        print(f"  Redirection vers: {response.get('Location', 'N/A')}")
    
    # Test avec authentification
    client.force_login(user)
    response = client.get('/admin/viticulture/cuvee/add/')
    print(f"Avec auth - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Accès réussi!")
        return True
    elif response.status_code == 302:
        print(f"  Redirection vers: {response.get('Location', 'N/A')}")
    elif response.status_code == 403:
        print("✗ ERREUR 403: Accès refusé")
        # Analyser le contenu de la réponse
        content = response.content.decode('utf-8')
        if 'permission' in content.lower():
            print("  Raison probable: Permissions insuffisantes")
        elif 'csrf' in content.lower():
            print("  Raison probable: Problème CSRF")
        else:
            print("  Raison inconnue")
    
    return response.status_code == 200

def diagnostic_admin_permissions(user):
    """Test des permissions admin spécifiques"""
    print_section("TEST PERMISSIONS ADMIN SPECIFIQUES")
    
    if not user:
        print("✗ Pas d'utilisateur pour le test")
        return False
    
    # Simuler une requête
    from django.http import HttpRequest
    request = HttpRequest()
    request.user = user
    
    # Obtenir l'admin Cuvee
    cuvee_admin = site._registry[Cuvee]
    
    # Tester les permissions
    permissions = {
        'has_view_permission': cuvee_admin.has_view_permission(request),
        'has_add_permission': cuvee_admin.has_add_permission(request),
        'has_change_permission': cuvee_admin.has_change_permission(request),
        'has_delete_permission': cuvee_admin.has_delete_permission(request),
    }
    
    print("Permissions admin:")
    for perm_name, has_perm in permissions.items():
        status = "✓" if has_perm else "✗"
        print(f"  {status} {perm_name}: {has_perm}")
    
    return all(permissions.values())

def create_test_data():
    """Crée les données de test nécessaires"""
    print_section("CREATION DONNEES DE TEST")
    
    # Utiliser une organisation existante ou en créer une nouvelle
    try:
        org = Organization.objects.first()
        if org:
            print(f"[OK] Organisation existante utilisee: {org.name}")
        else:
            # Créer une nouvelle organisation avec un SIRET unique
            import random
            siret = f"{random.randint(10000000000000, 99999999999999)}"
            org = Organization.objects.create(
                name="Test Organization",
                siret=siret,
                currency='EUR',
                is_initialized=True
            )
            print(f"[OK] Organisation creee: {org.name}")
    except Exception as e:
        print(f"[ERROR] Erreur creation organisation: {e}")
        return None, None
    
    # Créer/mettre à jour l'utilisateur de test
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
    
    if not created:
        # Mettre à jour les permissions
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"[OK] Utilisateur mis a jour: {user.email}")
    else:
        print(f"[OK] Utilisateur cree: {user.email}")
    
    # Définir le mot de passe
    user.set_password('admin123')
    user.save()
    print("[OK] Mot de passe defini: admin123")
    
    # Créer un membership si nécessaire
    from apps.accounts.models import Membership
    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={
            'role': Membership.Role.OWNER,
            'is_active': True
        }
    )
    if not created:
        # Mettre à jour le membership existant
        membership.role = Membership.Role.OWNER
        membership.is_active = True
        membership.save()
        print(f"[OK] Membership mis a jour: {user.email} -> {org.name}")
    else:
        print(f"[OK] Membership cree: {user.email} -> {org.name}")
    
    return user, org

def main():
    """Fonction principale de diagnostic"""
    print("DIAGNOSTIC COMPLET ADMIN VITICULTURE")
    print("Analyse du problème 403 sur /admin/viticulture/cuvee/add/")
    
    # Créer les données de test
    user, org = create_test_data()
    
    # Tests de diagnostic
    tests = [
        ("Enregistrement Admin", diagnostic_admin_registration),
        ("URLs Admin", diagnostic_urls),
        ("Permissions Utilisateur", lambda: diagnostic_user_permissions()),
        ("Permissions Admin", lambda: diagnostic_admin_permissions(user)),
        ("Test Client Django", lambda: diagnostic_client_test(user)),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ ERREUR dans {test_name}: {e}")
            results[test_name] = False
    
    # Résumé
    print_section("RESUME DES TESTS")
    for test_name, result in results.items():
        status = "✓ REUSSI" if result else "✗ ECHEC"
        print(f"{status}: {test_name}")
    
    # Recommandations
    print_section("RECOMMANDATIONS")
    if all(results.values()):
        print("✓ Tous les tests sont passés!")
        print("Le problème pourrait être lié à:")
        print("  - Cache du navigateur")
        print("  - Session expirée")
        print("  - Middleware personnalisé")
        print("\nEssayez:")
        print("  1. Vider le cache du navigateur")
        print("  2. Utiliser un onglet privé")
        print("  3. Se reconnecter avec admin123")
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"✗ Tests échoués: {', '.join(failed_tests)}")
        print("\nActions recommandées:")
        if not results.get("Enregistrement Admin"):
            print("  - Vérifier apps/viticulture/admin.py")
            print("  - Redémarrer le serveur Django")
        if not results.get("Permissions Utilisateur"):
            print("  - Créer un superutilisateur")
            print("  - Vérifier les permissions Django")

if __name__ == '__main__':
    main()
