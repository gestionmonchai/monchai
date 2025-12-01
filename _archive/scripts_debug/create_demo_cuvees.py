#!/usr/bin/env python
"""
Script pour créer des cuvées de démonstration
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Organization
from apps.viticulture.models import Cuvee, UnitOfMeasure, Appellation, Vintage

def create_demo_cuvees():
    """Créer des cuvées de démonstration"""
    try:
        org = Organization.objects.first()
        if not org:
            print("Aucune organisation trouvée")
            return
        
        print(f"Création de cuvées pour: {org.name}")
        
        # Récupérer les références
        uom_bt = UnitOfMeasure.objects.filter(organization=org, code='BT').first()
        uom_l = UnitOfMeasure.objects.filter(organization=org, code='L').first()
        
        app_bordeaux = Appellation.objects.filter(organization=org, name='Bordeaux').first()
        app_languedoc = Appellation.objects.filter(organization=org, name='Languedoc').first()
        app_igp = Appellation.objects.filter(organization=org, name='IGP Pays d\'Oc').first()
        
        vintage_2023 = Vintage.objects.filter(organization=org, year=2023).first()
        vintage_2024 = Vintage.objects.filter(organization=org, year=2024).first()
        
        if not uom_bt:
            print("UOM Bouteille non trouvée")
            return
        
        # Créer les cuvées
        cuvees_data = [
            {
                'name': 'Cuvée Prestige Rouge',
                'code': 'CPR-2023',
                'default_uom': uom_bt,
                'appellation': app_bordeaux,
                'vintage': vintage_2023,
            },
            {
                'name': 'Blanc de Blancs',
                'code': 'BDB-2024',
                'default_uom': uom_bt,
                'appellation': app_languedoc,
                'vintage': vintage_2024,
            },
            {
                'name': 'Rosé d\'Été',
                'code': 'RDE-2024',
                'default_uom': uom_bt,
                'appellation': app_igp,
                'vintage': vintage_2024,
            },
            {
                'name': 'Cuvée Tradition',
                'code': 'CTR-2023',
                'default_uom': uom_l,
                'appellation': app_bordeaux,
                'vintage': vintage_2023,
            },
        ]
        
        for data in cuvees_data:
            cuvee, created = Cuvee.objects.get_or_create(
                organization=org,
                name=data['name'],
                defaults=data
            )
            
            if created:
                print(f"  ✓ Cuvée créée: {cuvee.name}")
            else:
                print(f"  - Cuvée existante: {cuvee.name}")
        
        print(f"Total cuvées: {Cuvee.objects.filter(organization=org).count()}")
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_demo_cuvees()
