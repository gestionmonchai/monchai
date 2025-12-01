#!/usr/bin/env python
"""
CREATION DONNEES DEMO VITICULTURE
Cree des donnees de test pour valider le fonctionnement de l'admin
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from decimal import Decimal
from apps.accounts.models import Organization, User, Membership
from apps.viticulture.models import (
    GrapeVariety, Appellation, Vintage, UnitOfMeasure,
    VineyardPlot, Cuvee, Warehouse, Lot
)

def create_demo_data():
    """Cree des donnees de demonstration pour viticulture"""
    print("=== CREATION DONNEES DEMO VITICULTURE ===")
    
    # Utiliser l'organisation existante
    org = Organization.objects.first()
    if not org:
        print("[ERROR] Aucune organisation trouvee")
        return
    
    print(f"[OK] Organisation: {org.name}")
    
    # 1. Unites de mesure standard viticoles
    print("\n1. Creation unites de mesure...")
    units_data = [
        ('L', 'Litre', Decimal('1.0')),
        ('hL', 'Hectolitre', Decimal('100.0')),
        ('BT', 'Bouteille 75cl', Decimal('0.75')),
        ('MAG', 'Magnum 1.5L', Decimal('1.5')),
        ('JER', 'Jeroboam 3L', Decimal('3.0')),
        ('REH', 'Rehoboam 4.5L', Decimal('4.5')),
        ('MAT', 'Mathusalem 6L', Decimal('6.0')),
    ]
    
    for code, name, ratio in units_data:
        unit, created = UnitOfMeasure.objects.get_or_create(
            organization=org,
            code=code,
            defaults={
                'name': name,
                'base_ratio_to_l': ratio,
                'is_default': (code == 'L')
            }
        )
        status = "[CREATED]" if created else "[EXISTS]"
        print(f"  {status} {code}: {name}")
    
    # 2. Cepages
    print("\n2. Creation cepages...")
    grape_varieties_data = [
        ('Chardonnay', 'blanc'),
        ('Sauvignon Blanc', 'blanc'),
        ('Pinot Noir', 'rouge'),
        ('Merlot', 'rouge'),
        ('Cabernet Sauvignon', 'rouge'),
        ('Syrah', 'rouge'),
    ]
    
    for name, color in grape_varieties_data:
        grape, created = GrapeVariety.objects.get_or_create(
            organization=org,
            name_norm=name.lower(),
            defaults={
                'name': name,
                'color': color
            }
        )
        status = "[CREATED]" if created else "[EXISTS]"
        print(f"  {status} {name} ({color})")
    
    # 3. Appellations
    print("\n3. Creation appellations...")
    appellations_data = [
        ('Bordeaux', 'aoc'),
        ('Languedoc', 'aoc'),
        ('IGP Pays d\'Oc', 'igp'),
        ('Vin de France', 'autre'),
    ]
    
    for name, type_app in appellations_data:
        appellation, created = Appellation.objects.get_or_create(
            organization=org,
            name_norm=name.lower(),
            defaults={
                'name': name,
                'type': type_app
            }
        )
        status = "[CREATED]" if created else "[EXISTS]"
        print(f"  {status} {name} ({type_app})")
    
    # 4. Millesimes
    print("\n4. Creation millesimes...")
    years = [2020, 2021, 2022, 2023, 2024]
    
    for year in years:
        vintage, created = Vintage.objects.get_or_create(
            organization=org,
            year=year
        )
        status = "[CREATED]" if created else "[EXISTS]"
        print(f"  {status} {year}")
    
    # 5. Entrepots
    print("\n5. Creation entrepots...")
    warehouses_data = [
        ('Chai Principal', 'Batiment principal de vinification'),
        ('Cave de Vieillissement', 'Cave souterraine pour elevage'),
        ('Entrepot Bouteilles', 'Stockage produits finis'),
    ]
    
    for name, location in warehouses_data:
        warehouse, created = Warehouse.objects.get_or_create(
            organization=org,
            name=name,
            defaults={'location': location}
        )
        status = "[CREATED]" if created else "[EXISTS]"
        print(f"  {status} {name}")
    
    # 6. Parcelles
    print("\n6. Creation parcelles...")
    chardonnay = GrapeVariety.objects.filter(organization=org, name='Chardonnay').first()
    pinot_noir = GrapeVariety.objects.filter(organization=org, name='Pinot Noir').first()
    bordeaux = Appellation.objects.filter(organization=org, name='Bordeaux').first()
    
    if chardonnay and pinot_noir and bordeaux:
        plots_data = [
            ('Parcelle des Coteaux', Decimal('2.5'), chardonnay, bordeaux, 2018),
            ('Vignes du Sud', Decimal('1.8'), pinot_noir, bordeaux, 2015),
            ('Plateau Est', Decimal('3.2'), chardonnay, None, 2020),
        ]
        
        for name, area, grape, appellation, planting_year in plots_data:
            plot, created = VineyardPlot.objects.get_or_create(
                organization=org,
                name=name,
                defaults={
                    'area_ha': area,
                    'grape_variety': grape,
                    'appellation': appellation,
                    'planting_year': planting_year
                }
            )
            status = "[CREATED]" if created else "[EXISTS]"
            print(f"  {status} {name} ({area} ha)")
    
    # 7. Cuvees
    print("\n7. Creation cuvees...")
    litre = UnitOfMeasure.objects.filter(organization=org, code='L').first()
    vintage_2023 = Vintage.objects.filter(organization=org, year=2023).first()
    
    if litre and vintage_2023 and bordeaux:
        cuvees_data = [
            ('Cuvee Prestige', 'PRES', bordeaux, vintage_2023),
            ('Cuvee Tradition', 'TRAD', bordeaux, vintage_2023),
            ('Cuvee Reserve', 'RESE', None, vintage_2023),
        ]
        
        for name, code, appellation, vintage in cuvees_data:
            cuvee, created = Cuvee.objects.get_or_create(
                organization=org,
                name=name,
                defaults={
                    'code': code,
                    'default_uom': litre,
                    'appellation': appellation,
                    'vintage': vintage
                }
            )
            status = "[CREATED]" if created else "[EXISTS]"
            print(f"  {status} {name} ({code})")
    
    # 8. Lots
    print("\n8. Creation lots...")
    chai_principal = Warehouse.objects.filter(organization=org, name='Chai Principal').first()
    cuvee_prestige = Cuvee.objects.filter(organization=org, name='Cuvee Prestige').first()
    
    if chai_principal and cuvee_prestige:
        lots_data = [
            ('LOT-2023-001', cuvee_prestige, Decimal('5000.0'), Decimal('13.5')),
            ('LOT-2023-002', cuvee_prestige, Decimal('3500.0'), Decimal('13.2')),
        ]
        
        for code, cuvee, volume, alcohol in lots_data:
            lot, created = Lot.objects.get_or_create(
                organization=org,
                code=code,
                defaults={
                    'cuvee': cuvee,
                    'warehouse': chai_principal,
                    'volume_l': volume,
                    'alcohol_pct': alcohol,
                    'status': 'elevage'
                }
            )
            status = "[CREATED]" if created else "[EXISTS]"
            print(f"  {status} {code} ({volume}L)")
    
    print("\n[OK] Donnees demo creees avec succes!")
    print("\nVous pouvez maintenant:")
    print("  1. Acceder a /admin/viticulture/cuvee/add/")
    print("  2. Tester la creation de nouvelles cuvees")
    print("  3. Explorer tous les modeles viticulture")

def main():
    """Fonction principale"""
    try:
        create_demo_data()
    except Exception as e:
        print(f"[ERROR] Erreur lors de la creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
