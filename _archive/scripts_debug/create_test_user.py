#!/usr/bin/env python
"""
CREATION D'UN UTILISATEUR DE TEST AVEC MOT DE PASSE CONNU
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

def main():
    print("=" * 80)
    print("CREATION UTILISATEUR DE TEST")
    print("=" * 80)
    
    User = get_user_model()
    
    # Vérifier l'utilisateur existant
    try:
        user = User.objects.get(email='demo@monchai.fr')
        print(f"Utilisateur existant trouvé: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        
        # Changer le mot de passe
        new_password = 'test123'
        user.set_password(new_password)
        user.save()
        print(f"Mot de passe changé vers: {new_password}")
        
    except User.DoesNotExist:
        print("Utilisateur demo@monchai.fr non trouvé, création...")
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            email='demo@monchai.fr',
            password='test123',
            first_name='Demo',
            last_name='User'
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Utilisateur créé: {user.email}")
        
        # Créer une organisation si nécessaire
        org, created = Organization.objects.get_or_create(
            name='Test Organization',
            defaults={
                'siret': '12345678901234',
                'is_initialized': True
            }
        )
        
        if created:
            print(f"Organisation créée: {org.name}")
        
        # Créer le membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={
                'role': Membership.Role.OWNER,
                'is_active': True
            }
        )
        
        if created:
            print(f"Membership créé: {membership}")
    
    # Vérifier les memberships
    memberships = Membership.objects.filter(user=user)
    print(f"\nMemberships: {memberships.count()}")
    for membership in memberships:
        print(f"  - {membership.organization.name} ({membership.role})")
    
    # Test de connexion
    print(f"\n=== INFORMATIONS DE CONNEXION ===")
    print(f"Email: demo@monchai.fr")
    print(f"Mot de passe: test123")
    print(f"URL de test: http://127.0.0.1:8000/admin/viticulture/cuvee/add/")
    
    # Vérifier que l'utilisateur peut se connecter
    from django.contrib.auth import authenticate
    auth_user = authenticate(email='demo@monchai.fr', password='test123')
    if auth_user:
        print(f"OK Authentification réussie pour {auth_user.email}")
    else:
        print("ERREUR Authentification échouée")

if __name__ == '__main__':
    main()
