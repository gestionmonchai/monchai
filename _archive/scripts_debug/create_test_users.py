#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test pour Mon Chai V1
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import User, Organization, Membership

def create_test_users():
    """Créer des utilisateurs de test avec différents scénarios"""
    
    print("Creation des utilisateurs de test pour Mon Chai...")
    
    # 1. Superuser admin
    if not User.objects.filter(email='admin@monchai.fr').exists():
        admin = User.objects.create_superuser(
            username='admin@monchai.fr',
            email='admin@monchai.fr',
            password='admin123',
            first_name='Admin',
            last_name='MonChai'
        )
        print(f"[OK] Superuser cree: {admin.email} / admin123")
    else:
        print("[INFO] Superuser admin@monchai.fr existe deja")
    
    # 2. Utilisateur sans organisation (pour tester onboarding)
    if not User.objects.filter(email='nouveau@test.fr').exists():
        nouveau = User.objects.create_user(
            username='nouveau@test.fr',
            email='nouveau@test.fr',
            password='test123',
            first_name='Nouveau',
            last_name='Utilisateur'
        )
        print(f"[OK] Utilisateur nouveau cree: {nouveau.email} / test123")
        print("   -> Pas d'organisation (testera l'onboarding)")
    else:
        print("[INFO] Utilisateur nouveau@test.fr existe deja")
    
    # 3. Propriétaire d'exploitation avec organisation complète
    if not User.objects.filter(email='proprietaire@vignoble.fr').exists():
        proprietaire = User.objects.create_user(
            username='proprietaire@vignoble.fr',
            email='proprietaire@vignoble.fr',
            password='vigneron123',
            first_name='Jean',
            last_name='Vigneron'
        )
        
        # Créer son exploitation
        exploitation = Organization.objects.create(
            name='Vignoble des Coteaux',
            siret='12345678901234',
            tva_number='FR12345678901',
            currency='EUR',
            is_initialized=True
        )
        
        # Créer le membership owner
        Membership.objects.create(
            user=proprietaire,
            organization=exploitation,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        print(f"[OK] Proprietaire cree: {proprietaire.email} / vigneron123")
        print(f"   -> Exploitation: {exploitation.name}")
        print(f"   -> Role: Owner")
    else:
        print("[INFO] Utilisateur proprietaire@vignoble.fr existe deja")
    
    # 4. Éditeur dans une exploitation
    if not User.objects.filter(email='editeur@vignoble.fr').exists():
        editeur = User.objects.create_user(
            username='editeur@vignoble.fr',
            email='editeur@vignoble.fr',
            password='editeur123',
            first_name='Marie',
            last_name='Caviste'
        )
        
        # L'ajouter à l'exploitation existante
        try:
            exploitation = Organization.objects.get(name='Vignoble des Coteaux')
            Membership.objects.create(
                user=editeur,
                organization=exploitation,
                role=Membership.Role.EDITOR,
                is_active=True
            )
            print(f"[OK] Editeur cree: {editeur.email} / editeur123")
            print(f"   -> Exploitation: {exploitation.name}")
            print(f"   -> Role: Editor")
        except Organization.DoesNotExist:
            print("[WARN] Exploitation non trouvee pour l'editeur")
    else:
        print("[INFO] Utilisateur editeur@vignoble.fr existe deja")
    
    # 5. Lecteur seul
    if not User.objects.filter(email='lecteur@vignoble.fr').exists():
        lecteur = User.objects.create_user(
            username='lecteur@vignoble.fr',
            email='lecteur@vignoble.fr',
            password='lecteur123',
            first_name='Paul',
            last_name='Consultant'
        )
        
        # L'ajouter à l'exploitation existante
        try:
            exploitation = Organization.objects.get(name='Vignoble des Coteaux')
            Membership.objects.create(
                user=lecteur,
                organization=exploitation,
                role=Membership.Role.READ_ONLY,
                is_active=True
            )
            print(f"[OK] Lecteur cree: {lecteur.email} / lecteur123")
            print(f"   -> Exploitation: {exploitation.name}")
            print(f"   -> Role: Read Only")
        except Organization.DoesNotExist:
            print("[WARN] Exploitation non trouvee pour le lecteur")
    else:
        print("[INFO] Utilisateur lecteur@vignoble.fr existe deja")
    
    print("\nIdentifiants de test crees !")
    print("\nRESUME DES COMPTES DE TEST :")
    print("=" * 50)
    print("ADMIN (superuser)")
    print("   Email: admin@monchai.fr")
    print("   Mot de passe: admin123")
    print("   Acces: /admin/ + toutes fonctionnalites")
    print()
    print("NOUVEAU UTILISATEUR (onboarding)")
    print("   Email: nouveau@test.fr")
    print("   Mot de passe: test123")
    print("   Statut: Aucune organisation -> testera l'onboarding")
    print()
    print("PROPRIETAIRE (owner)")
    print("   Email: proprietaire@vignoble.fr")
    print("   Mot de passe: vigneron123")
    print("   Organisation: Vignoble des Coteaux")
    print("   Role: Owner (tous droits)")
    print()
    print("EDITEUR (editor)")
    print("   Email: editeur@vignoble.fr")
    print("   Mot de passe: editeur123")
    print("   Organisation: Vignoble des Coteaux")
    print("   Role: Editor (modification des donnees)")
    print()
    print("LECTEUR (read-only)")
    print("   Email: lecteur@vignoble.fr")
    print("   Mot de passe: lecteur123")
    print("   Organisation: Vignoble des Coteaux")
    print("   Role: Read Only (consultation uniquement)")
    print()
    print("URL de test: http://127.0.0.1:8000")
    print("Admin Django: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    create_test_users()
