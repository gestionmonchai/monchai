#!/usr/bin/env python
"""
DIAGNOSTIC DES PROBLÈMES DE PERMISSIONS
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from apps.accounts.models import Organization, Membership

def main():
    print("=" * 80)
    print("DIAGNOSTIC DES PROBLEMES DE PERMISSIONS")
    print("=" * 80)
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("ERREUR: Aucun utilisateur trouvé")
        return
    
    print(f"Utilisateur analysé: {user.email}")
    print(f"Is active: {user.is_active}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    
    # Vérifier les memberships
    memberships = Membership.objects.filter(user=user)
    print(f"\nMemberships: {memberships.count()}")
    for membership in memberships:
        print(f"  - Organisation: {membership.organization.name}")
        print(f"  - Rôle: {membership.role}")
        print(f"  - Actif: {membership.is_active}")
    
    # Vérifier les permissions Django
    print(f"\nPermissions utilisateur:")
    print(f"  - User permissions: {user.user_permissions.count()}")
    print(f"  - Group permissions: {sum(group.permissions.count() for group in user.groups.all())}")
    
    # Problèmes identifiés
    print("\n" + "=" * 50)
    print("PROBLEMES IDENTIFIES")
    print("=" * 50)
    
    problems = []
    
    # 1. Utilisateur pas staff pour admin Django
    if not user.is_staff:
        problems.append("L'utilisateur n'est pas 'staff' - ne peut pas accéder à l'admin Django")
    
    # 2. URLs catalogue redirigent vers login
    problems.append("Les URLs catalogue redirigent vers login même avec utilisateur authentifié")
    problems.append("Problème probable: middleware ou décorateur de permissions trop restrictif")
    
    # 3. URLs référentiels n'existent pas
    problems.append("Les URLs référentiels retournent 404 - routes non définies")
    
    if problems:
        print("PROBLEMES DETECTES:")
        for i, problem in enumerate(problems, 1):
            print(f"  {i}. {problem}")
    
    # Solutions proposées
    print("\n" + "=" * 50)
    print("SOLUTIONS PROPOSEES")
    print("=" * 50)
    
    print("1. CORRIGER PERMISSIONS ADMIN:")
    print(f"   user = User.objects.get(email='{user.email}')")
    print("   user.is_staff = True")
    print("   user.save()")
    
    print("\n2. VERIFIER MIDDLEWARES:")
    print("   - Vérifier apps.accounts.middleware.OrganizationMiddleware")
    print("   - Vérifier les décorateurs @require_membership")
    
    print("\n3. AJOUTER ROUTES REFERENTIELS:")
    print("   - Créer les vues pour /referentiels/")
    print("   - Ajouter les URLs dans urls.py")
    
    # Correction automatique
    print("\n" + "=" * 50)
    print("CORRECTION AUTOMATIQUE")
    print("=" * 50)
    
    if not user.is_staff:
        print("Correction du statut staff...")
        user.is_staff = True
        user.save()
        print(f"✓ {user.email} est maintenant staff")
    else:
        print("✓ L'utilisateur est déjà staff")
    
    print(f"\nSTATUT FINAL:")
    print(f"  - Is staff: {user.is_staff}")
    print(f"  - Is superuser: {user.is_superuser}")
    print(f"  - Memberships actifs: {memberships.filter(is_active=True).count()}")

if __name__ == '__main__':
    main()
