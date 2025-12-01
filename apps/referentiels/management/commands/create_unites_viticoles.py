"""
Commande Django pour créer les unités viticoles standard
Roadmap Cut #4 : Données test et unités standard
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Organization
from apps.referentiels.models import Unite


class Command(BaseCommand):
    help = 'Crée les unités viticoles standard pour toutes les organisations'

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

        # Unités viticoles standard
        unites_standard = [
            # Volumes de base
            {
                'nom': 'Litre',
                'symbole': 'L',
                'type_unite': 'volume',
                'facteur_conversion': 1.0,
                'description': 'Unité de base pour les volumes'
            },
            {
                'nom': 'Hectolitre',
                'symbole': 'hL',
                'type_unite': 'volume',
                'facteur_conversion': 100.0,
                'description': 'Unité courante en viticulture (100 litres)'
            },
            {
                'nom': 'Centilitre',
                'symbole': 'cL',
                'type_unite': 'volume',
                'facteur_conversion': 0.01,
                'description': 'Centilitre (1/100 de litre)'
            },
            
            # Bouteilles standard
            {
                'nom': 'Bouteille 75cL',
                'symbole': 'btl',
                'type_unite': 'volume',
                'facteur_conversion': 0.75,
                'description': 'Bouteille standard de 75 centilitres'
            },
            {
                'nom': 'Demi-bouteille',
                'symbole': '1/2 btl',
                'type_unite': 'volume',
                'facteur_conversion': 0.375,
                'description': 'Demi-bouteille de 37,5 centilitres'
            },
            {
                'nom': 'Quart de bouteille',
                'symbole': '1/4 btl',
                'type_unite': 'volume',
                'facteur_conversion': 0.1875,
                'description': 'Piccolo ou quart de bouteille (18,75 cL)'
            },
            
            # Grands formats
            {
                'nom': 'Magnum',
                'symbole': 'Mg',
                'type_unite': 'volume',
                'facteur_conversion': 1.5,
                'description': 'Magnum - 2 bouteilles (1,5 L)'
            },
            {
                'nom': 'Double Magnum',
                'symbole': 'DMg',
                'type_unite': 'volume',
                'facteur_conversion': 3.0,
                'description': 'Double Magnum - 4 bouteilles (3 L)'
            },
            {
                'nom': 'Jéroboam',
                'symbole': 'Jér',
                'type_unite': 'volume',
                'facteur_conversion': 4.5,
                'description': 'Jéroboam - 6 bouteilles (4,5 L)'
            },
            {
                'nom': 'Impériale',
                'symbole': 'Imp',
                'type_unite': 'volume',
                'facteur_conversion': 6.0,
                'description': 'Impériale - 8 bouteilles (6 L)'
            },
            {
                'nom': 'Salmanazar',
                'symbole': 'Sal',
                'type_unite': 'volume',
                'facteur_conversion': 9.0,
                'description': 'Salmanazar - 12 bouteilles (9 L)'
            },
            {
                'nom': 'Balthazar',
                'symbole': 'Bal',
                'type_unite': 'volume',
                'facteur_conversion': 12.0,
                'description': 'Balthazar - 16 bouteilles (12 L)'
            },
            {
                'nom': 'Nabuchodonosor',
                'symbole': 'Nab',
                'type_unite': 'volume',
                'facteur_conversion': 15.0,
                'description': 'Nabuchodonosor - 20 bouteilles (15 L)'
            },
            
            # Unités de poids
            {
                'nom': 'Kilogramme',
                'symbole': 'kg',
                'type_unite': 'poids',
                'facteur_conversion': 1.0,
                'description': 'Unité de base pour les poids'
            },
            {
                'nom': 'Gramme',
                'symbole': 'g',
                'type_unite': 'poids',
                'facteur_conversion': 0.001,
                'description': 'Gramme (1/1000 de kg)'
            },
            {
                'nom': 'Tonne',
                'symbole': 't',
                'type_unite': 'poids',
                'facteur_conversion': 1000.0,
                'description': 'Tonne métrique (1000 kg)'
            },
            
            # Unités de surface
            {
                'nom': 'Hectare',
                'symbole': 'ha',
                'type_unite': 'surface',
                'facteur_conversion': 1.0,
                'description': 'Unité de base pour les surfaces viticoles'
            },
            {
                'nom': 'Are',
                'symbole': 'a',
                'type_unite': 'surface',
                'facteur_conversion': 0.01,
                'description': 'Are (1/100 d\'hectare)'
            },
            {
                'nom': 'Mètre carré',
                'symbole': 'm²',
                'type_unite': 'surface',
                'facteur_conversion': 0.0001,
                'description': 'Mètre carré (1/10000 d\'hectare)'
            },
            
            # Unités de quantité
            {
                'nom': 'Unité',
                'symbole': 'u',
                'type_unite': 'quantite',
                'facteur_conversion': 1.0,
                'description': 'Unité de base pour les quantités'
            },
            {
                'nom': 'Caisse 6 bouteilles',
                'symbole': 'C6',
                'type_unite': 'quantite',
                'facteur_conversion': 6.0,
                'description': 'Caisse de 6 bouteilles'
            },
            {
                'nom': 'Caisse 12 bouteilles',
                'symbole': 'C12',
                'type_unite': 'quantite',
                'facteur_conversion': 12.0,
                'description': 'Caisse de 12 bouteilles'
            },
            {
                'nom': 'Palette',
                'symbole': 'Pal',
                'type_unite': 'quantite',
                'facteur_conversion': 600.0,
                'description': 'Palette standard (50 caisses de 12)'
            },
        ]

        total_created = 0
        total_existing = 0

        with transaction.atomic():
            for org in organizations:
                org_created = 0
                org_existing = 0
                
                self.stdout.write(f"\n--- Organisation: {org.name} ---")
                
                for unite_data in unites_standard:
                    unite, created = Unite.objects.get_or_create(
                        organization=org,
                        nom=unite_data['nom'],
                        defaults={
                            'symbole': unite_data['symbole'],
                            'type_unite': unite_data['type_unite'],
                            'facteur_conversion': unite_data['facteur_conversion'],
                        }
                    )
                    
                    if created:
                        org_created += 1
                        self.stdout.write(
                            f"  + Cree: {unite.nom} ({unite.symbole})"
                        )
                    else:
                        org_existing += 1
                        self.stdout.write(
                            f"  - Existe: {unite.nom} ({unite.symbole})"
                        )
                
                self.stdout.write(
                    f"  -> {org_created} creees, {org_existing} existantes"
                )
                total_created += org_created
                total_existing += org_existing

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTermine ! {total_created} unites creees, {total_existing} existantes'
            )
        )
        
        if total_created > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    'Les unites viticoles standard sont maintenant disponibles !'
                )
            )
