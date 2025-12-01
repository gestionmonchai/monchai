"""
Commande pour créer les seeds minimaux viticoles
DB Roadmap 01 - Seeds minimaux (UoM L/hL/BT ; 2-3 cépages démo)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.accounts.models import Organization
from apps.viticulture.models import (
    UnitOfMeasure, GrapeVariety, Appellation, Vintage, Warehouse
)


class Command(BaseCommand):
    help = 'Crée les seeds minimaux pour le cœur viticole'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=str,
            help='ID de l\'organisation (optionnel, prend la première si non spécifié)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la recréation des seeds existants'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creation des seeds minimaux viticoles - DB Roadmap 01')
        
        # Récupérer l'organisation
        if options['org_id']:
            try:
                organization = Organization.objects.get(id=options['org_id'])
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Organisation {options["org_id"]} non trouvée')
                )
                return
        else:
            organization = Organization.objects.first()
            if not organization:
                self.stdout.write(
                    self.style.ERROR('Aucune organisation trouvée. Créez d\'abord une organisation.')
                )
                return
        
        self.stdout.write(f'Organisation: {organization.name}')
        
        try:
            with transaction.atomic():
                # 1. Unités de mesure (UoM)
                self.create_units_of_measure(organization, options['force'])
                
                # 2. Cépages démo
                self.create_grape_varieties(organization, options['force'])
                
                # 3. Appellations de base
                self.create_appellations(organization, options['force'])
                
                # 4. Millésimes récents
                self.create_vintages(organization, options['force'])
                
                # 5. Entrepôt par défaut
                self.create_default_warehouse(organization, options['force'])
                
                self.stdout.write(
                    self.style.SUCCESS('Seeds viticoles créés avec succès!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création des seeds: {e}')
            )
            raise
    
    def create_units_of_measure(self, organization, force=False):
        """Crée les unités de mesure de base"""
        self.stdout.write('Creation des unités de mesure...')
        
        units_data = [
            {
                'code': 'L',
                'name': 'Litre',
                'base_ratio_to_l': Decimal('1.000000'),
                'is_default': True
            },
            {
                'code': 'hL',
                'name': 'Hectolitre',
                'base_ratio_to_l': Decimal('100.000000'),
                'is_default': False
            },
            {
                'code': 'BT',
                'name': 'Bouteille (75cl)',
                'base_ratio_to_l': Decimal('0.750000'),
                'is_default': False
            },
            {
                'code': 'MAG',
                'name': 'Magnum (1.5L)',
                'base_ratio_to_l': Decimal('1.500000'),
                'is_default': False
            },
        ]
        
        for unit_data in units_data:
            unit, created = UnitOfMeasure.objects.get_or_create(
                organization=organization,
                code=unit_data['code'],
                defaults=unit_data
            )
            
            if created:
                self.stdout.write(f'  Unité créée: {unit.name} ({unit.code})')
            elif force:
                for key, value in unit_data.items():
                    setattr(unit, key, value)
                unit.save()
                self.stdout.write(f'  Unité mise à jour: {unit.name} ({unit.code})')
            else:
                self.stdout.write(f'  Unité existante: {unit.name} ({unit.code})')
    
    def create_grape_varieties(self, organization, force=False):
        """Crée les cépages de démonstration"""
        self.stdout.write('Creation des cépages démo...')
        
        grapes_data = [
            {
                'name': 'Cabernet Sauvignon',
                'color': 'rouge'
            },
            {
                'name': 'Merlot',
                'color': 'rouge'
            },
            {
                'name': 'Chardonnay',
                'color': 'blanc'
            },
            {
                'name': 'Sauvignon Blanc',
                'color': 'blanc'
            },
            {
                'name': 'Pinot Noir',
                'color': 'rouge'
            },
            {
                'name': 'Syrah',
                'color': 'rouge'
            },
        ]
        
        for grape_data in grapes_data:
            # La normalisation se fait automatiquement dans le modèle
            grape, created = GrapeVariety.objects.get_or_create(
                organization=organization,
                name_norm=grape_data['name'].lower().strip(),
                defaults=grape_data
            )
            
            if created:
                self.stdout.write(f'  Cépage créé: {grape.name} ({grape.get_color_display()})')
            elif force:
                for key, value in grape_data.items():
                    setattr(grape, key, value)
                grape.save()
                self.stdout.write(f'  Cépage mis à jour: {grape.name}')
            else:
                self.stdout.write(f'  Cépage existant: {grape.name}')
    
    def create_appellations(self, organization, force=False):
        """Crée les appellations de base"""
        self.stdout.write('Creation des appellations...')
        
        appellations_data = [
            {
                'name': 'Bordeaux',
                'type': 'aoc',
                'region': 'Bordeaux'
            },
            {
                'name': 'Côtes du Rhône',
                'type': 'aoc',
                'region': 'Vallée du Rhône'
            },
            {
                'name': 'Languedoc',
                'type': 'aoc',
                'region': 'Languedoc-Roussillon'
            },
            {
                'name': 'IGP Pays d\'Oc',
                'type': 'igp',
                'region': 'Languedoc-Roussillon'
            },
            {
                'name': 'Vin de France',
                'type': 'vsig',
                'region': 'France'
            },
        ]
        
        for appellation_data in appellations_data:
            appellation, created = Appellation.objects.get_or_create(
                organization=organization,
                name_norm=appellation_data['name'].lower().strip(),
                defaults=appellation_data
            )
            
            if created:
                self.stdout.write(f'  Appellation créée: {appellation.name} ({appellation.get_type_display()})')
            elif force:
                for key, value in appellation_data.items():
                    setattr(appellation, key, value)
                appellation.save()
                self.stdout.write(f'  Appellation mise à jour: {appellation.name}')
            else:
                self.stdout.write(f'  Appellation existante: {appellation.name}')
    
    def create_vintages(self, organization, force=False):
        """Crée les millésimes récents"""
        self.stdout.write('Creation des millésimes...')
        
        from django.utils import timezone
        current_year = timezone.now().year
        
        # Créer les 5 dernières années + année courante + année suivante
        years = list(range(current_year - 4, current_year + 2))
        
        for year in years:
            vintage, created = Vintage.objects.get_or_create(
                organization=organization,
                year=year
            )
            
            if created:
                self.stdout.write(f'  Millésime créé: {vintage.year}')
            else:
                self.stdout.write(f'  Millésime existant: {vintage.year}')
    
    def create_default_warehouse(self, organization, force=False):
        """Crée un entrepôt par défaut"""
        self.stdout.write('Creation de l\'entrepôt par défaut...')
        
        warehouse_data = {
            'name': 'Chai principal',
            'location': 'Site principal'
        }
        
        warehouse, created = Warehouse.objects.get_or_create(
            organization=organization,
            name=warehouse_data['name'],
            defaults=warehouse_data
        )
        
        if created:
            self.stdout.write(f'  Entrepôt créé: {warehouse.name}')
        elif force:
            for key, value in warehouse_data.items():
                setattr(warehouse, key, value)
            warehouse.save()
            self.stdout.write(f'  Entrepôt mis à jour: {warehouse.name}')
        else:
            self.stdout.write(f'  Entrepôt existant: {warehouse.name}')
    
    def show_summary(self, organization):
        """Affiche un résumé des seeds créés"""
        self.stdout.write('\nRésumé des seeds viticoles:')
        
        counts = {
            'Unités de mesure': UnitOfMeasure.objects.filter(organization=organization).count(),
            'Cépages': GrapeVariety.objects.filter(organization=organization).count(),
            'Appellations': Appellation.objects.filter(organization=organization).count(),
            'Millésimes': Vintage.objects.filter(organization=organization).count(),
            'Entrepôts': Warehouse.objects.filter(organization=organization).count(),
        }
        
        for category, count in counts.items():
            self.stdout.write(f'  • {category}: {count}')
        
        self.stdout.write('\nPrêt pour la création de parcelles, cuvées et lots!')
