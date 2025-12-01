"""
Commande pour créer des données de démonstration pour le système de stock
DB Roadmap 02 - Validation avec données réelles
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import Organization, Membership
from apps.viticulture.models import (
    GrapeVariety, Appellation, Vintage, UnitOfMeasure, 
    Cuvee, Warehouse, Lot
)
from apps.stock.models import SKU, StockManager

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour le système de stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-name',
            type=str,
            default='Domaine de Démonstration',
            help='Nom de l\'organisation de test'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            default='demo@monchai.fr',
            help='Email de l\'utilisateur de test'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        org_name = options['org_name']
        user_email = options['user_email']
        
        self.stdout.write(
            self.style.SUCCESS(f'Création des données de démonstration pour "{org_name}"')
        )
        
        # 1. Organisation et utilisateur
        import random
        siret_demo = f"9876543210{random.randint(1000, 9999)}"
        
        org, created = Organization.objects.get_or_create(
            name=org_name,
            defaults={
                'siret': siret_demo,  # SIRET fictif unique pour démo
                'address': '123 Route des Vignes',
                'postal_code': '33000',
                'city': 'Bordeaux',
                'country': 'France'
            }
        )
        
        if created:
            self.stdout.write(f'[OK] Organisation créée: {org.name}')
        else:
            self.stdout.write(f'[OK] Organisation existante: {org.name}')
        
        # Utilisateur
        user, created = User.objects.get_or_create(
            email=user_email,
            defaults={
                'username': user_email.split('@')[0],
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'[OK] Utilisateur créé: {user.email}')
        else:
            self.stdout.write(f'[OK] Utilisateur existant: {user.email}')
        
        # Membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': 'admin'}
        )
        
        # 2. Unités de mesure standard viticoles
        self.stdout.write('\n[UNITES] Création des unités de mesure...')
        
        units_data = [
            {'name': 'Litre', 'code': 'L', 'ratio': Decimal('1.0')},
            {'name': 'Hectolitre', 'code': 'hL', 'ratio': Decimal('100.0')},
            {'name': 'Bouteille 75cl', 'code': 'BT', 'ratio': Decimal('0.75')},
            {'name': 'Magnum 1.5L', 'code': 'MAG', 'ratio': Decimal('1.5')},
            {'name': 'Jéroboam 3L', 'code': 'JER', 'ratio': Decimal('3.0')},
            {'name': 'Réhoboam 4.5L', 'code': 'REH', 'ratio': Decimal('4.5')},
            {'name': 'Mathusalem 6L', 'code': 'MAT', 'ratio': Decimal('6.0')},
        ]
        
        uoms = {}
        for unit_data in units_data:
            uom, created = UnitOfMeasure.objects.get_or_create(
                organization=org,
                code=unit_data['code'],
                defaults={
                    'name': unit_data['name'],
                    'base_ratio_to_l': unit_data['ratio'],
                    'is_default': unit_data['code'] == 'L'
                }
            )
            uoms[unit_data['code']] = uom
            status = '[OK] Créée' if created else '[OK] Existante'
            self.stdout.write(f'  {status}: {uom.name} ({uom.code})')
        
        # 3. Référentiels viticoles
        self.stdout.write('\n[REFERENTIELS] Création des référentiels...')
        
        # Cépages
        grape_varieties = {}
        grapes_data = [
            {'name': 'Cabernet Sauvignon', 'color': 'rouge'},
            {'name': 'Merlot', 'color': 'rouge'},
            {'name': 'Cabernet Franc', 'color': 'rouge'},
            {'name': 'Sauvignon Blanc', 'color': 'blanc'},
            {'name': 'Chardonnay', 'color': 'blanc'},
            {'name': 'Sémillon', 'color': 'blanc'},
        ]
        
        for grape_data in grapes_data:
            grape, created = GrapeVariety.objects.get_or_create(
                organization=org,
                name=grape_data['name'],
                defaults={'color': grape_data['color']}
            )
            grape_varieties[grape_data['name']] = grape
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {grape.name} ({grape.color})')
        
        # Appellations
        appellations = {}
        appellations_data = [
            {'name': 'Bordeaux AOC', 'region': 'Bordeaux'},
            {'name': 'Saint-Émilion AOC', 'region': 'Bordeaux'},
            {'name': 'Pauillac AOC', 'region': 'Bordeaux'},
            {'name': 'Sauternes AOC', 'region': 'Bordeaux'},
        ]
        
        for app_data in appellations_data:
            appellation, created = Appellation.objects.get_or_create(
                organization=org,
                name=app_data['name'],
                defaults={'region': app_data['region']}
            )
            appellations[app_data['name']] = appellation
            status = '[OK] Créée' if created else '[OK] Existante'
            self.stdout.write(f'  {status}: {appellation.name}')
        
        # Millésimes
        vintages = {}
        for year in [2021, 2022, 2023, 2024]:
            vintage, created = Vintage.objects.get_or_create(
                organization=org,
                year=year
            )
            vintages[year] = vintage
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: Millésime {year}')
        
        # 4. Infrastructure (Entrepôts)
        self.stdout.write('\n[ENTREPOTS] Création des entrepôts...')
        
        warehouses = {}
        warehouses_data = [
            {'name': 'Chai Principal'},
            {'name': 'Chai de Vieillissement'},
            {'name': 'Entrepôt Bouteilles'},
        ]
        
        for wh_data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                organization=org,
                name=wh_data['name']
            )
            warehouses[wh_data['name']] = warehouse
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {warehouse.name}')
        
        # 5. Cuvées
        self.stdout.write('\n[CUVEES] Création des cuvées...')
        
        cuvees = {}
        cuvees_data = [
            {
                'name': 'Réserve Rouge 2023',
                'vintage': 2023,
                'appellation': 'Bordeaux AOC'
            },
            {
                'name': 'Grande Cuvée 2022',
                'vintage': 2022,
                'appellation': 'Saint-Émilion AOC'
            },
            {
                'name': 'Blanc de Blanc 2023',
                'vintage': 2023,
                'appellation': 'Bordeaux AOC'
            },
        ]
        
        for cuvee_data in cuvees_data:
            cuvee, created = Cuvee.objects.get_or_create(
                organization=org,
                name=cuvee_data['name'],
                defaults={
                    'vintage': vintages[cuvee_data['vintage']],
                    'appellation': appellations[cuvee_data['appellation']],
                    'default_uom': uoms['L']
                }
            )
            cuvees[cuvee_data['name']] = cuvee
            status = '[OK] Créée' if created else '[OK] Existante'
            self.stdout.write(f'  {status}: {cuvee.name}')
        
        # 6. Lots de production
        self.stdout.write('\n[LOTS] Création des lots...')
        
        lots = {}
        lots_data = [
            {
                'code': 'LOT-2023-001',
                'cuvee': 'Réserve Rouge 2023',
                'warehouse': 'Chai Principal',
                'volume_l': Decimal('5000.0'),
                'status': 'elevage'
            },
            {
                'code': 'LOT-2022-015',
                'cuvee': 'Grande Cuvée 2022',
                'warehouse': 'Chai de Vieillissement',
                'volume_l': Decimal('3000.0'),
                'status': 'stabilise'
            },
            {
                'code': 'LOT-2023-008',
                'cuvee': 'Blanc de Blanc 2023',
                'warehouse': 'Chai Principal',
                'volume_l': Decimal('2000.0'),
                'status': 'en_cours'
            },
        ]
        
        for lot_data in lots_data:
            lot, created = Lot.objects.get_or_create(
                organization=org,
                code=lot_data['code'],
                defaults={
                    'cuvee': cuvees[lot_data['cuvee']],
                    'warehouse': warehouses[lot_data['warehouse']],
                    'volume_l': lot_data['volume_l'],
                    'status': lot_data['status']
                }
            )
            lots[lot_data['code']] = lot
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {lot.code} - {lot.volume_l}L')
        
        # 7. SKUs (Produits finis)
        self.stdout.write('\n[SKUS] Création des SKUs...')
        
        skus = {}
        skus_data = [
            {
                'label': 'Réserve Rouge 2023 - Bouteille',
                'cuvee': 'Réserve Rouge 2023',
                'uom': 'BT',
                'volume': Decimal('0.75')
            },
            {
                'label': 'Réserve Rouge 2023 - Magnum',
                'cuvee': 'Réserve Rouge 2023',
                'uom': 'MAG',
                'volume': Decimal('1.5')
            },
            {
                'label': 'Grande Cuvée 2022 - Bouteille',
                'cuvee': 'Grande Cuvée 2022',
                'uom': 'BT',
                'volume': Decimal('0.75')
            },
            {
                'label': 'Blanc de Blanc 2023 - Bouteille',
                'cuvee': 'Blanc de Blanc 2023',
                'uom': 'BT',
                'volume': Decimal('0.75')
            },
        ]
        
        for sku_data in skus_data:
            sku, created = SKU.objects.get_or_create(
                organization=org,
                cuvee=cuvees[sku_data['cuvee']],
                uom=uoms[sku_data['uom']],
                defaults={
                    'label': sku_data['label'],
                    'volume_by_uom_to_l': sku_data['volume'],
                    'is_active': True
                }
            )
            skus[sku_data['label']] = sku
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {sku.label}')
        
        # 8. Mouvements de stock initiaux
        self.stdout.write('\n[STOCKS] Création des stocks initiaux...')
        
        # Stock vrac initial
        stock_moves = [
            {
                'type': 'vrac',
                'lot': 'LOT-2023-001',
                'warehouse': 'Chai Principal',
                'qty': Decimal('5000.0'),
                'move_type': 'entree',
                'notes': 'Stock initial - Récolte 2023'
            },
            {
                'type': 'vrac',
                'lot': 'LOT-2022-015',
                'warehouse': 'Chai de Vieillissement',
                'qty': Decimal('3000.0'),
                'move_type': 'entree',
                'notes': 'Stock initial - Élevage terminé'
            },
            {
                'type': 'vrac',
                'lot': 'LOT-2023-008',
                'warehouse': 'Chai Principal',
                'qty': Decimal('2000.0'),
                'move_type': 'entree',
                'notes': 'Stock initial - Fermentation'
            },
        ]
        
        for move_data in stock_moves:
            if move_data['type'] == 'vrac':
                try:
                    move = StockManager.move_vrac(
                        lot=lots[move_data['lot']],
                        src_warehouse=None,
                        dst_warehouse=warehouses[move_data['warehouse']],
                        qty_l=move_data['qty'],
                        move_type=move_data['move_type'],
                        user=user,
                        notes=move_data['notes']
                    )
                    self.stdout.write(f'  [OK] Stock vrac: {move_data["lot"]} - {move_data["qty"]}L')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  [WARN] Stock vrac existant: {move_data["lot"]}')
                    )
        
        # 9. Fabrication de quelques bouteilles
        self.stdout.write('\n[FABRICATION] Fabrication de bouteilles de démonstration...')
        
        fabrications = [
            {
                'lot': 'LOT-2022-015',
                'sku': 'Grande Cuvée 2022 - Bouteille',
                'warehouse': 'Entrepôt Bouteilles',
                'qty_units': 500,
                'notes': 'Premier embouteillage - Lot stabilisé'
            },
        ]
        
        for fab_data in fabrications:
            try:
                # Transfert du vrac vers l'entrepôt bouteilles
                StockManager.move_vrac(
                    lot=lots[fab_data['lot']],
                    src_warehouse=warehouses['Chai de Vieillissement'],
                    dst_warehouse=warehouses[fab_data['warehouse']],
                    qty_l=Decimal('375.0'),  # 500 bouteilles * 0.75L
                    move_type='transfert',
                    user=user,
                    notes='Transfert pour embouteillage'
                )
                
                # Fabrication des bouteilles
                vrac_move, sku_move = StockManager.fabrication_sku(
                    lot=lots[fab_data['lot']],
                    sku=skus[fab_data['sku']],
                    warehouse=warehouses[fab_data['warehouse']],
                    qty_units=fab_data['qty_units'],
                    user=user,
                    notes=fab_data['notes']
                )
                
                self.stdout.write(
                    f'  [OK] Fabrication: {fab_data["qty_units"]} x {fab_data["sku"]}'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  [WARN] Fabrication échouée: {str(e)}')
                )
        
        # 10. Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] DONNÉES DE DÉMONSTRATION CRÉÉES'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'[STATS] Organisation: {org.name}')
        self.stdout.write(f'[STATS] Utilisateur: {user.email} (mot de passe: demo123)')
        self.stdout.write(f'[STATS] Unités de mesure: {UnitOfMeasure.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Cépages: {GrapeVariety.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Appellations: {Appellation.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Millésimes: {Vintage.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Entrepôts: {Warehouse.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Cuvées: {Cuvee.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Lots: {Lot.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] SKUs: {SKU.objects.filter(organization=org).count()}')
        
        self.stdout.write('\n[INFO] Utilisez l\'admin Django pour explorer les données créées')
        self.stdout.write('[INFO] Testez les mouvements de stock via l\'interface')
