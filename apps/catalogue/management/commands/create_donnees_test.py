"""
Commande Django pour créer des données de test complètes
Roadmap Cut #4 : Test des fonctionnalités catalogue et lots
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal

from apps.accounts.models import Organization
from apps.referentiels.models import Cepage, Parcelle, Unite, Cuvee, Entrepot
from apps.catalogue.models import Lot, MouvementLot


class Command(BaseCommand):
    help = 'Crée des données de test complètes pour valider le fonctionnement'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=int,
            help='ID de l\'organisation (optionnel, sinon toutes les orgs)',
        )

    def handle(self, *args, **options):
        org_id = options.get('org_id')
        
        if org_id:
            try:
                organizations = [Organization.objects.get(id=org_id)]
                self.stdout.write(f"Traitement de l'organisation ID {org_id}")
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Organisation avec ID {org_id} introuvable')
                )
                return
        else:
            organizations = Organization.objects.all()
            self.stdout.write(f"Traitement de {organizations.count()} organisations")

        total_created = 0

        with transaction.atomic():
            for org in organizations:
                self.stdout.write(f"\n--- Organisation: {org.name} ---")
                org_created = 0
                
                # 1. Créer des cépages de test
                cepages_data = [
                    {'nom': 'Chardonnay', 'code': 'CHAR', 'couleur': 'blanc'},
                    {'nom': 'Sauvignon Blanc', 'code': 'SAUV', 'couleur': 'blanc'},
                    {'nom': 'Cabernet Sauvignon', 'code': 'CABS', 'couleur': 'rouge'},
                    {'nom': 'Merlot', 'code': 'MERL', 'couleur': 'rouge'},
                    {'nom': 'Pinot Noir', 'code': 'PINO', 'couleur': 'rouge'},
                ]
                
                cepages = []
                for cepage_data in cepages_data:
                    cepage, created = Cepage.objects.get_or_create(
                        organization=org,
                        nom=cepage_data['nom'],
                        defaults={
                            'code': cepage_data['code'],
                            'couleur': cepage_data['couleur'],
                        }
                    )
                    cepages.append(cepage)
                    if created:
                        org_created += 1
                        self.stdout.write(f"  + Cepage: {cepage.nom}")
                
                # 2. Créer des entrepôts de test
                entrepots_data = [
                    {'nom': 'Chai Principal', 'type_entrepot': 'chai', 'capacite': 10000},
                    {'nom': 'Cave de Vieillissement', 'type_entrepot': 'cave', 'capacite': 5000},
                    {'nom': 'Depot Commercial', 'type_entrepot': 'depot', 'capacite': 15000},
                ]
                
                entrepots = []
                for entrepot_data in entrepots_data:
                    entrepot, created = Entrepot.objects.get_or_create(
                        organization=org,
                        nom=entrepot_data['nom'],
                        defaults={
                            'type_entrepot': entrepot_data['type_entrepot'],
                            'capacite': entrepot_data['capacite'],
                        }
                    )
                    entrepots.append(entrepot)
                    if created:
                        org_created += 1
                        self.stdout.write(f"  + Entrepot: {entrepot.nom}")
                
                # 3. Créer des cuvées de test
                try:
                    litre = Unite.objects.get(organization=org, nom='Litre')
                except Unite.DoesNotExist:
                    self.stdout.write("  ! Unite Litre non trouvee, creation...")
                    litre = Unite.objects.create(
                        organization=org,
                        nom='Litre',
                        symbole='L',
                        type_unite='volume',
                        facteur_conversion=1.0
                    )
                
                cuvees_data = [
                    {
                        'nom': 'Chardonnay Reserve',
                        'couleur': 'blanc',
                        'classification': 'aoc',
                        'appellation': 'Chablis',
                        'degre_alcool': 13.5,
                        'cepages': [cepages[0]],  # Chardonnay
                    },
                    {
                        'nom': 'Assemblage Rouge',
                        'couleur': 'rouge',
                        'classification': 'igp',
                        'appellation': 'Languedoc',
                        'degre_alcool': 14.0,
                        'cepages': [cepages[2], cepages[3]],  # Cabernet + Merlot
                    },
                    {
                        'nom': 'Pinot Noir Tradition',
                        'couleur': 'rouge',
                        'classification': 'aoc',
                        'appellation': 'Bourgogne',
                        'degre_alcool': 12.5,
                        'cepages': [cepages[4]],  # Pinot Noir
                    },
                ]
                
                cuvees = []
                for cuvee_data in cuvees_data:
                    cuvee, created = Cuvee.objects.get_or_create(
                        organization=org,
                        nom=cuvee_data['nom'],
                        defaults={
                            'couleur': cuvee_data['couleur'],
                            'classification': cuvee_data['classification'],
                            'appellation': cuvee_data['appellation'],
                            'degre_alcool': cuvee_data['degre_alcool'],
                        }
                    )
                    if created:
                        cuvee.cepages.set(cuvee_data['cepages'])
                        org_created += 1
                        self.stdout.write(f"  + Cuvee: {cuvee.nom}")
                    cuvees.append(cuvee)
                
                # 4. Créer des lots de test
                lots_data = [
                    {
                        'cuvee': cuvees[0],
                        'entrepot': entrepots[0],
                        'numero_lot': 'LOT-2024-001',
                        'millesime': 2024,
                        'volume_initial': Decimal('1000.00'),
                        'degre_alcool': Decimal('13.5'),
                        'statut': 'fermentation',
                        'date_creation': date.today() - timedelta(days=30),
                    },
                    {
                        'cuvee': cuvees[1],
                        'entrepot': entrepots[1],
                        'numero_lot': 'LOT-2023-015',
                        'millesime': 2023,
                        'volume_initial': Decimal('1500.00'),
                        'degre_alcool': Decimal('14.0'),
                        'statut': 'stock',
                        'date_creation': date.today() - timedelta(days=180),
                    },
                    {
                        'cuvee': cuvees[2],
                        'entrepot': entrepots[1],
                        'numero_lot': 'LOT-2023-008',
                        'millesime': 2023,
                        'volume_initial': Decimal('800.00'),
                        'degre_alcool': Decimal('12.5'),
                        'statut': 'elevage',
                        'date_creation': date.today() - timedelta(days=120),
                    },
                ]
                
                for lot_data in lots_data:
                    lot, created = Lot.objects.get_or_create(
                        organization=org,
                        numero_lot=lot_data['numero_lot'],
                        millesime=lot_data['millesime'],
                        defaults={
                            'cuvee': lot_data['cuvee'],
                            'entrepot': lot_data['entrepot'],
                            'volume_initial': lot_data['volume_initial'],
                            'unite_volume': litre,
                            'volume_actuel': lot_data['volume_initial'],
                            'degre_alcool': lot_data['degre_alcool'],
                            'statut': lot_data['statut'],
                            'date_creation': lot_data['date_creation'],
                        }
                    )
                    if created:
                        org_created += 1
                        self.stdout.write(f"  + Lot: {lot.numero_lot}")
                        
                        # Créer le mouvement initial
                        MouvementLot.objects.create(
                            lot=lot,
                            type_mouvement='creation',
                            description=f'Creation du lot {lot.numero_lot}',
                            volume_avant=0,
                            volume_mouvement=lot.volume_initial,
                            volume_apres=lot.volume_initial,
                            date_mouvement=lot.created_at,
                        )
                
                self.stdout.write(f"  -> {org_created} elements crees pour {org.name}")
                total_created += org_created

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTermine ! {total_created} elements de test crees au total'
            )
        )
        
        if total_created > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    'Les donnees de test sont maintenant disponibles !'
                )
            )
            self.stdout.write(
                'Vous pouvez maintenant tester :'
            )
            self.stdout.write('  - /catalogue/ : Grille des cuvees')
            self.stdout.write('  - /catalogue/lots/ : Liste des lots')
            self.stdout.write('  - /ref/ : Referentiels complets')
