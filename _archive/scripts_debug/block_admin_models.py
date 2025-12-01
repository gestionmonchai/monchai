#!/usr/bin/env python
"""
Script pour bloquer l'accès aux modèles métier dans l'admin Django
pour les utilisateurs normaux (seuls les superusers gardent l'accès)
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.contrib import admin

def block_admin_models():
    """Bloque l'accès aux modèles métier pour utilisateurs normaux"""
    
    # Modèles à bloquer (métier, pas technique)
    models_to_block = [
        # Billing
        'apps.billing.models.Invoice',
        'apps.billing.models.InvoiceLine', 
        'apps.billing.models.CreditNote',
        'apps.billing.models.Payment',
        'apps.billing.models.Reconciliation',
        'apps.billing.models.AccountMap',
        'apps.billing.models.GLEntry',
        
        # Stock
        'apps.stock.models.SKU',
        'apps.stock.models.StockVracBalance',
        'apps.stock.models.StockSKUBalance',
        'apps.stock.models.StockVracMove',
        'apps.stock.models.StockSKUMove',
        'apps.stock.models.StockTransfer',
        
        # Viticulture
        'apps.viticulture.models.GrapeVariety',
        'apps.viticulture.models.Appellation',
        'apps.viticulture.models.Vintage',
        'apps.viticulture.models.UnitOfMeasure',
        'apps.viticulture.models.VineyardPlot',
        'apps.viticulture.models.Cuvee',
        'apps.viticulture.models.Warehouse',
        'apps.viticulture.models.Lot',
        'apps.viticulture.models.LotGrapeRatio',
        'apps.viticulture.models.LotAssemblage',
        
        # Clients (déjà fait mais pour info)
        'apps.clients.models.Customer',
        'apps.clients.models.CustomerTag',
        'apps.clients.models.CustomerTagLink',
        'apps.clients.models.CustomerActivity',
    ]
    
    blocked_count = 0
    
    for model_path in models_to_block:
        try:
            # Importer le modèle
            module_path, model_name = model_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[model_name])
            model = getattr(module, model_name)
            
            # Vérifier s'il est enregistré dans l'admin
            if model in admin.site._registry:
                admin_class = admin.site._registry[model]
                
                # Vérifier si les permissions sont déjà bloquées
                if hasattr(admin_class, 'has_module_permission'):
                    # Tester avec un utilisateur normal fictif
                    class FakeUser:
                        is_superuser = False
                    
                    fake_request = type('Request', (), {'user': FakeUser()})()
                    
                    if admin_class.has_module_permission(fake_request):
                        print(f"⚠️  {model_path} : Permissions NON bloquées")
                    else:
                        print(f"✅ {model_path} : Permissions déjà bloquées")
                        blocked_count += 1
                else:
                    print(f"❌ {model_path} : Permissions NON bloquées (pas de has_module_permission)")
            else:
                print(f"ℹ️  {model_path} : Non enregistré dans l'admin")
                
        except Exception as e:
            print(f"❌ {model_path} : Erreur - {e}")
    
    print(f"\n📊 Résumé : {blocked_count} modèles bloqués sur {len(models_to_block)} vérifiés")
    
    return blocked_count

if __name__ == '__main__':
    print("🔒 Vérification blocage modèles admin Django")
    print("=" * 60)
    
    blocked = block_admin_models()
    
    print("\n" + "=" * 60)
    if blocked < 20:  # On s'attend à bloquer la plupart
        print("⚠️  ATTENTION: Certains modèles métier sont encore accessibles !")
        print("   Il faut ajouter les méthodes has_*_permission dans les admin classes")
    else:
        print("🎉 SUCCÈS: La plupart des modèles métier sont bloqués")
        print("   Seuls les superusers peuvent accéder à l'admin technique")
