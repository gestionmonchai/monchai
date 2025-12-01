#!/usr/bin/env python
"""
Script pour créer des données de test pour les alertes de stock - Roadmap 34
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, User
from apps.stock.models import StockThreshold, StockVracBalance
from apps.viticulture.models import Lot, Warehouse
from apps.stock.services import StockAlertService

def create_test_thresholds():
    """Crée des seuils de test pour déclencher des alertes"""
    
    # Récupérer une organisation de test avec des données de stock
    org = Organization.objects.filter(name="Domaine de Démonstration").first()
    if not org:
        org = Organization.objects.first()
    if not org:
        print("Aucune organisation trouvee")
        return
    
    # Récupérer un utilisateur admin
    user = User.objects.filter(memberships__organization=org, memberships__role='owner').first()
    if not user:
        user = User.objects.filter(memberships__organization=org).first()
    
    if not user:
        print("Aucun utilisateur trouve pour l'organisation")
        return
    
    print(f"Organisation: {org.name}")
    print(f"Utilisateur: {user.email}")
    
    # Créer un seuil global élevé pour déclencher des alertes
    global_threshold, created = StockThreshold.objects.get_or_create(
        organization=org,
        scope='global',
        ref_id=None,
        defaults={
            'threshold_l': Decimal('20000.00'),
            'created_by': user,
            'notes': 'Seuil global de test pour déclencher des alertes'
        }
    )
    
    if created:
        print(f"Seuil global cree: {global_threshold.threshold_l}L")
    else:
        print(f"Seuil global existant: {global_threshold.threshold_l}L")
    
    # Vérifier les balances de stock existantes
    balances = StockVracBalance.objects.filter(organization=org, qty_l__gt=0)
    print(f"\nBalances de stock trouvees: {balances.count()}")
    
    for balance in balances[:5]:  # Afficher les 5 premières
        print(f"  - {balance.lot.code} @ {balance.warehouse.name}: {balance.qty_l}L")
    
    # Créer un seuil spécifique pour une cuvée si possible
    if balances.exists():
        first_balance = balances.first()
        cuvee_threshold, created = StockThreshold.objects.get_or_create(
            organization=org,
            scope='cuvee',
            ref_id=first_balance.lot.cuvee.id,
            defaults={
                'threshold_l': Decimal('10000.00'),
                'created_by': user,
                'notes': f'Seuil spécifique pour la cuvée {first_balance.lot.cuvee.name}'
            }
        )
        
        if created:
            print(f"Seuil cuvee cree: {cuvee_threshold.threshold_l}L pour {first_balance.lot.cuvee.name}")
        else:
            print(f"Seuil cuvee existant: {cuvee_threshold.threshold_l}L pour {first_balance.lot.cuvee.name}")

def test_alert_computation():
    """Test le calcul des alertes"""
    
    org = Organization.objects.filter(name="Domaine de Démonstration").first()
    if not org:
        org = Organization.objects.first()
    if not org:
        print("Aucune organisation trouvee")
        return
    
    print(f"\nTest du calcul des alertes pour {org.name}...")
    
    # Exécuter le calcul des alertes
    result = StockAlertService.compute_stock_alerts(org)
    
    print(f"Resultat:")
    print(f"  - Alertes creees: {result['created_count']}")
    print(f"  - Alertes resolues: {result['resolved_count']}")
    print(f"  - Alertes actives: {result['total_active']}")
    
    # Afficher les alertes actives
    if result['total_active'] > 0:
        alerts = StockAlertService.get_alerts_list(org, {'status': 'active'})
        print(f"\nAlertes actives:")
        for alert in alerts[:5]:
            print(f"  - {alert.lot.code} @ {alert.warehouse.name}: {alert.balance_l}L < {alert.threshold_l}L (source: {alert.threshold_source})")

def main():
    print("Configuration des alertes de stock - Roadmap 34")
    print("=" * 50)
    
    try:
        create_test_thresholds()
        test_alert_computation()
        
        print("\nConfiguration terminee avec succes!")
        print("\nProchaines etapes:")
        print("  1. Acceder a /stocks/alertes/ pour voir l'interface")
        print("  2. Tester l'API /stocks/api/alertes/")
        print("  3. Programmer la commande: python manage.py compute_stock_alerts")
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
