#!/usr/bin/env python
"""
CORRECTION DES PERMISSIONS ADMIN DJANGO
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
from django.contrib.contenttypes.models import ContentType

def main():
    print("=" * 80)
    print("CORRECTION DES PERMISSIONS ADMIN DJANGO")
    print("=" * 80)
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("ERREUR: Aucun utilisateur")
        return
    
    print(f"Utilisateur: {user.email}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    
    # Option 1: Faire superuser (solution simple)
    print(f"\n=== OPTION 1: SUPERUSER ===")
    if not user.is_superuser:
        user.is_superuser = True
        user.save()
        print(f"OK {user.email} est maintenant SUPERUSER")
        print("  -> Accès total à l'admin Django")
    else:
        print(f"OK {user.email} est déjà SUPERUSER")
    
    # Option 2: Permissions spécifiques (plus sécurisé)
    print(f"\n=== OPTION 2: PERMISSIONS SPECIFIQUES ===")
    
    # Permissions pour les modèles viticulture
    viticulture_permissions = [
        'viticulture.add_cuvee',
        'viticulture.change_cuvee',
        'viticulture.delete_cuvee',
        'viticulture.view_cuvee',
        'viticulture.add_appellation',
        'viticulture.change_appellation',
        'viticulture.delete_appellation',
        'viticulture.view_appellation',
        'viticulture.add_vintage',
        'viticulture.change_vintage',
        'viticulture.delete_vintage',
        'viticulture.view_vintage',
        'viticulture.add_unitofmeasure',
        'viticulture.change_unitofmeasure',
        'viticulture.delete_unitofmeasure',
        'viticulture.view_unitofmeasure',
    ]
    
    # Permissions pour les modèles catalogue
    catalogue_permissions = [
        'catalogue.add_lot',
        'catalogue.change_lot',
        'catalogue.delete_lot',
        'catalogue.view_lot',
        'catalogue.add_mouvementlot',
        'catalogue.change_mouvementlot',
        'catalogue.delete_mouvementlot',
        'catalogue.view_mouvementlot',
    ]
    
    # Permissions pour les modèles stock
    stock_permissions = [
        'stock.add_warehouse',
        'stock.change_warehouse',
        'stock.delete_warehouse',
        'stock.view_warehouse',
        'stock.add_sku',
        'stock.change_sku',
        'stock.delete_sku',
        'stock.view_sku',
        'stock.add_stockitem',
        'stock.change_stockitem',
        'stock.delete_stockitem',
        'stock.view_stockitem',
    ]
    
    # Permissions pour les modèles sales
    sales_permissions = [
        'sales.add_customer',
        'sales.change_customer',
        'sales.delete_customer',
        'sales.view_customer',
        'sales.add_pricelist',
        'sales.change_pricelist',
        'sales.delete_pricelist',
        'sales.view_pricelist',
        'sales.add_quote',
        'sales.change_quote',
        'sales.delete_quote',
        'sales.view_quote',
        'sales.add_order',
        'sales.change_order',
        'sales.delete_order',
        'sales.view_order',
    ]
    
    all_permissions = viticulture_permissions + catalogue_permissions + stock_permissions + sales_permissions
    
    print(f"Attribution de {len(all_permissions)} permissions...")
    
    permissions_added = 0
    permissions_existing = 0
    
    for perm_codename in all_permissions:
        try:
            app_label, codename = perm_codename.split('.')
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename
            )
            
            if not user.user_permissions.filter(id=permission.id).exists():
                user.user_permissions.add(permission)
                permissions_added += 1
                print(f"  + {perm_codename}")
            else:
                permissions_existing += 1
                
        except Permission.DoesNotExist:
            print(f"  ! Permission non trouvée: {perm_codename}")
        except Exception as e:
            print(f"  ! Erreur pour {perm_codename}: {e}")
    
    print(f"\nRésumé permissions:")
    print(f"  - Ajoutées: {permissions_added}")
    print(f"  - Déjà existantes: {permissions_existing}")
    print(f"  - Total permissions utilisateur: {user.user_permissions.count()}")
    
    # Test final
    print(f"\n=== TEST FINAL ===")
    print(f"Utilisateur: {user.email}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Permissions totales: {user.user_permissions.count()}")
    
    # Test permission spécifique
    can_add_cuvee = user.has_perm('viticulture.add_cuvee')
    print(f"Peut ajouter cuvée: {can_add_cuvee}")
    
    if user.is_superuser or can_add_cuvee:
        print("OK L'utilisateur devrait maintenant pouvoir accéder à /admin/viticulture/cuvee/add/")
    else:
        print("ERREUR Problème persistant avec les permissions")

if __name__ == '__main__':
    main()
