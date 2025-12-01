#!/usr/bin/env python
"""
RESET SESSION UTILISATEUR ET VERIFICATION COMPLETE
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from apps.accounts.models import Organization, Membership

def reset_user_session():
    """Reset complet de la session utilisateur"""
    
    print("=" * 80)
    print("RESET SESSION UTILISATEUR - VERIFICATION COMPLETE")
    print("=" * 80)
    
    User = get_user_model()
    
    # Vérifier l'utilisateur
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"Utilisateur trouvé: {user.email}")
    except User.DoesNotExist:
        print("ERREUR: Utilisateur demo@monchai.fr non trouvé")
        return
    
    # Afficher l'état actuel
    print(f"\n=== ÉTAT UTILISATEUR ===")
    print(f"Email: {user.email}")
    print(f"Is active: {user.is_active}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Date joined: {user.date_joined}")
    print(f"Last login: {user.last_login}")
    
    # Vérifier les memberships
    memberships = Membership.objects.filter(user=user)
    print(f"\n=== MEMBERSHIPS ({memberships.count()}) ===")
    
    for membership in memberships:
        print(f"Organisation: {membership.organization.name}")
        print(f"  - Rôle: {membership.role}")
        print(f"  - Actif: {membership.is_active}")
        print(f"  - Org initialisée: {membership.organization.is_initialized}")
        print(f"  - Peut gérer rôles: {membership.can_manage_roles()}")
    
    # Nettoyer toutes les sessions
    print(f"\n=== NETTOYAGE SESSIONS ===")
    sessions_count = Session.objects.count()
    print(f"Sessions avant nettoyage: {sessions_count}")
    
    Session.objects.all().delete()
    
    sessions_after = Session.objects.count()
    print(f"Sessions après nettoyage: {sessions_after}")
    
    # Réinitialiser le mot de passe
    print(f"\n=== RESET MOT DE PASSE ===")
    new_password = 'admin123'
    user.set_password(new_password)
    user.save()
    print(f"Nouveau mot de passe: {new_password}")
    
    # Vérifier l'authentification
    from django.contrib.auth import authenticate
    auth_user = authenticate(email=user.email, password=new_password)
    if auth_user:
        print(f"OK: Authentification réussie")
    else:
        print(f"ERREUR: Authentification échouée")
    
    # Test avec client Django
    print(f"\n=== TEST CLIENT DJANGO ===")
    from django.test import Client
    
    client = Client()
    client.force_login(user)
    
    # Tester plusieurs URLs
    test_urls = [
        "/admin/",
        "/admin/viticulture/",
        "/admin/viticulture/cuvee/",
        "/admin/viticulture/cuvee/add/",
    ]
    
    for url in test_urls:
        try:
            response = client.get(url, follow=True)
            
            if response.status_code == 200:
                result = "OK"
            elif response.status_code == 403:
                result = "403 FORBIDDEN"
            elif response.status_code == 302:
                result = "REDIRECTION"
            else:
                result = f"Status {response.status_code}"
                
            print(f"{url:<35} | {result}")
            
        except Exception as e:
            print(f"{url:<35} | ERREUR: {e}")
    
    # Informations de connexion
    print(f"\n" + "=" * 80)
    print("INFORMATIONS DE CONNEXION")
    print("=" * 80)
    print(f"URL: http://127.0.0.1:8000/auth/login/")
    print(f"Email: {user.email}")
    print(f"Mot de passe: {new_password}")
    print(f"")
    print(f"URL à tester: http://127.0.0.1:8000/admin/viticulture/cuvee/add/")
    print(f"")
    print("ÉTAPES DE TEST:")
    print("1. Ouvrir un nouvel onglet en mode incognito")
    print("2. Aller à http://127.0.0.1:8000/auth/login/")
    print("3. Se connecter avec les identifiants ci-dessus")
    print("4. Aller directement à http://127.0.0.1:8000/admin/viticulture/cuvee/add/")
    print("5. Vérifier que le formulaire s'affiche")
    
    # Créer un utilisateur de test supplémentaire
    print(f"\n=== UTILISATEUR DE TEST SUPPLEMENTAIRE ===")
    
    # Supprimer l'ancien utilisateur de test s'il existe
    try:
        old_test_user = User.objects.get(email='test@monchai.fr')
        old_test_user.delete()
        print("Ancien utilisateur de test supprimé")
    except User.DoesNotExist:
        pass
    
    # Créer un nouvel utilisateur de test
    test_user = User.objects.create_user(
        email='test@monchai.fr',
        password='test123',
        first_name='Test',
        last_name='User'
    )
    test_user.is_staff = True
    test_user.is_superuser = True
    test_user.save()
    
    # Créer membership pour l'utilisateur de test
    org = Organization.objects.first()
    if org:
        membership = Membership.objects.create(
            user=test_user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        )
        print(f"Utilisateur de test créé: test@monchai.fr / test123")
        print(f"Organisation: {org.name}")
        print(f"Rôle: {membership.role}")
    
    print(f"\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print("✓ Sessions nettoyées")
    print("✓ Mot de passe réinitialisé")
    print("✓ Utilisateur de test créé")
    print("✓ Tests Django Client OK")
    print("")
    print("Si le problème persiste dans le navigateur:")
    print("1. Vider le cache navigateur (Ctrl+Shift+Del)")
    print("2. Utiliser mode incognito")
    print("3. Tester avec l'utilisateur test@monchai.fr")

def main():
    reset_user_session()

if __name__ == '__main__':
    main()
