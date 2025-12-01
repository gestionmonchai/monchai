"""
Commande pour créer des données de démonstration pour les référentiels
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from apps.accounts.models import Organization
from apps.referentiels.models import Cepage, Parcelle, Unite, Cuvee, Entrepot


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour les référentiels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-name',
            type=str,
            help='Nom de l\'organisation (optionnel)',
        )

    def handle(self, *args, **options):
        org_name = options.get('org_name')
        
        if org_name:
            try:
                organization = Organization.objects.get(name=org_name)
                self.stdout.write(f"Organisation trouvée: {organization.name}")
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Organisation "{org_name}" introuvable')
                )
                return
        else:
            organization = Organization.objects.first()
            if not organization:
                self.stdout.write(
                    self.style.ERROR('Aucune organisation trouvée')
                )
                return
            self.stdout.write(f"Utilisation de l'organisation: {organization.name}")

        with transaction.atomic():
            self.create_cepages(organization)
            self.create_parcelles(organization)
            self.create_unites(organization)
            self.create_entrepots(organization)
            self.create_cuvees(organization)
        
        self.stdout.write(
            self.style.SUCCESS('Données de référentiels créées avec succès!')
        )

    def create_cepages(self, organization):
        self.stdout.write('Création des cépages...')
        
        cepages_data = [
            {'nom': 'Cabernet Sauvignon', 'code': 'CS', 'couleur': 'rouge'},
            {'nom': 'Merlot', 'code': 'ME', 'couleur': 'rouge'},
            {'nom': 'Cabernet Franc', 'code': 'CF', 'couleur': 'rouge'},
            {'nom': 'Petit Verdot', 'code': 'PV', 'couleur': 'rouge'},
            {'nom': 'Chardonnay', 'code': 'CH', 'couleur': 'blanc'},
            {'nom': 'Sauvignon Blanc', 'code': 'SB', 'couleur': 'blanc'},
            {'nom': 'Sémillon', 'code': 'SE', 'couleur': 'blanc'},
            {'nom': 'Muscadelle', 'code': 'MU', 'couleur': 'blanc'},
            {'nom': 'Malbec', 'code': 'MA', 'couleur': 'rouge'},
            {'nom': 'Syrah', 'code': 'SY', 'couleur': 'rouge'},
        ]
        
        for data in cepages_data:
            cepage, created = Cepage.objects.get_or_create(
                organization=organization,
                nom=data['nom'],
                defaults={
                    'code': data['code'],
                    'couleur': data['couleur'],
                    'notes': f"Cépage {data['couleur']} traditionnel"
                }
            )
            if created:
                self.stdout.write(f"  [OK] {cepage.nom}")
            else:
                self.stdout.write(f"  [EXIST] {cepage.nom}")

    def create_parcelles(self, organization):
        self.stdout.write('Création des parcelles...')
        
        parcelles_data = [
            {'nom': 'Les Graves', 'surface': Decimal('2.5'), 'commune': 'Pessac', 'appellation': 'Pessac-Léognan'},
            {'nom': 'Côte Sud', 'surface': Decimal('1.8'), 'commune': 'Léognan', 'appellation': 'Pessac-Léognan'},
            {'nom': 'Plateau Central', 'surface': Decimal('3.2'), 'commune': 'Martillac', 'appellation': 'Pessac-Léognan'},
            {'nom': 'Les Cailloux', 'surface': Decimal('1.2'), 'commune': 'Cadaujac', 'appellation': 'Pessac-Léognan'},
            {'nom': 'Vignes Hautes', 'surface': Decimal('2.1'), 'commune': 'Villenave', 'appellation': 'Graves'},
            {'nom': 'Clos du Moulin', 'surface': Decimal('0.9'), 'commune': 'Portets', 'appellation': 'Graves'},
        ]
        
        for data in parcelles_data:
            parcelle, created = Parcelle.objects.get_or_create(
                organization=organization,
                nom=data['nom'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  [OK] {parcelle.nom} ({parcelle.surface} ha)")
            else:
                self.stdout.write(f"  [EXIST] {parcelle.nom}")

    def create_unites(self, organization):
        self.stdout.write('Création des unités...')
        
        unites_data = [
            {'nom': 'Litre', 'symbole': 'L', 'type_unite': 'volume', 'facteur_conversion': Decimal('1.0')},
            {'nom': 'Hectolitre', 'symbole': 'hL', 'type_unite': 'volume', 'facteur_conversion': Decimal('100.0')},
            {'nom': 'Bouteille', 'symbole': 'BT', 'type_unite': 'volume', 'facteur_conversion': Decimal('0.75')},
            {'nom': 'Magnum', 'symbole': 'MAG', 'type_unite': 'volume', 'facteur_conversion': Decimal('1.5')},
            {'nom': 'Jéroboam', 'symbole': 'JER', 'type_unite': 'volume', 'facteur_conversion': Decimal('3.0')},
            {'nom': 'Réhoboam', 'symbole': 'REH', 'type_unite': 'volume', 'facteur_conversion': Decimal('4.5')},
            {'nom': 'Mathusalem', 'symbole': 'MAT', 'type_unite': 'volume', 'facteur_conversion': Decimal('6.0')},
            {'nom': 'Kilogramme', 'symbole': 'kg', 'type_unite': 'poids', 'facteur_conversion': Decimal('1.0')},
            {'nom': 'Hectare', 'symbole': 'ha', 'type_unite': 'surface', 'facteur_conversion': Decimal('1.0')},
            {'nom': 'Unité', 'symbole': 'u', 'type_unite': 'quantite', 'facteur_conversion': Decimal('1.0')},
        ]
        
        for data in unites_data:
            unite, created = Unite.objects.get_or_create(
                organization=organization,
                nom=data['nom'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  [OK] {unite.nom} ({unite.symbole})")
            else:
                self.stdout.write(f"  [EXIST] {unite.nom}")

    def create_entrepots(self, organization):
        self.stdout.write('Création des entrepôts...')
        
        entrepots_data = [
            {
                'nom': 'Chai Principal',
                'type_entrepot': 'chai',
                'capacite': 50000,
                'temperature_min': Decimal('12.0'),
                'temperature_max': Decimal('18.0'),
                'adresse': 'Bâtiment principal, zone de vinification'
            },
            {
                'nom': 'Cave de Vieillissement',
                'type_entrepot': 'cave',
                'capacite': 30000,
                'temperature_min': Decimal('10.0'),
                'temperature_max': Decimal('14.0'),
                'adresse': 'Sous-sol, zone climatisée'
            },
            {
                'nom': 'Entrepôt Bouteilles',
                'type_entrepot': 'depot',
                'capacite': 100000,
                'temperature_min': Decimal('8.0'),
                'temperature_max': Decimal('16.0'),
                'adresse': 'Hangar B, stockage produits finis'
            },
            {
                'nom': 'Boutique',
                'type_entrepot': 'boutique',
                'capacite': 2000,
                'adresse': 'Accueil visiteurs, vente directe'
            },
        ]
        
        for data in entrepots_data:
            entrepot, created = Entrepot.objects.get_or_create(
                organization=organization,
                nom=data['nom'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  [OK] {entrepot.nom} ({entrepot.get_type_entrepot_display()})")
            else:
                self.stdout.write(f"  [EXIST] {entrepot.nom}")

    def create_cuvees(self, organization):
        self.stdout.write('Création des cuvées...')
        
        # Récupérer les cépages créés
        cabernet_s = Cepage.objects.filter(organization=organization, nom='Cabernet Sauvignon').first()
        merlot = Cepage.objects.filter(organization=organization, nom='Merlot').first()
        chardonnay = Cepage.objects.filter(organization=organization, nom='Chardonnay').first()
        sauvignon = Cepage.objects.filter(organization=organization, nom='Sauvignon Blanc').first()
        
        cuvees_data = [
            {
                'nom': 'Château Rouge Tradition',
                'couleur': 'rouge',
                'classification': 'aoc',
                'appellation': 'Pessac-Léognan',
                'degre_alcool': Decimal('13.5'),
                'description': 'Assemblage traditionnel de Cabernet Sauvignon et Merlot',
                'cepages': [cabernet_s, merlot] if cabernet_s and merlot else []
            },
            {
                'nom': 'Blanc de Blanc Premium',
                'couleur': 'blanc',
                'classification': 'aoc',
                'appellation': 'Pessac-Léognan',
                'degre_alcool': Decimal('12.8'),
                'description': 'Chardonnay pur, élevé en fût de chêne',
                'cepages': [chardonnay] if chardonnay else []
            },
            {
                'nom': 'Sauvignon Frais',
                'couleur': 'blanc',
                'classification': 'igp',
                'appellation': 'IGP Atlantique',
                'degre_alcool': Decimal('12.2'),
                'description': 'Sauvignon Blanc fruité et minéral',
                'cepages': [sauvignon] if sauvignon else []
            },
            {
                'nom': 'Cuvée Prestige',
                'couleur': 'rouge',
                'classification': 'aoc',
                'appellation': 'Pessac-Léognan',
                'degre_alcool': Decimal('14.2'),
                'description': 'Sélection parcellaire, élevage 18 mois',
                'cepages': [cabernet_s, merlot] if cabernet_s and merlot else []
            },
            {
                'nom': 'Rosé d\'Été',
                'couleur': 'rose',
                'classification': 'vdf',
                'appellation': 'Vin de France',
                'degre_alcool': Decimal('11.8'),
                'description': 'Rosé de saignée, fruité et léger',
                'cepages': [merlot] if merlot else []
            },
        ]
        
        for data in cuvees_data:
            cepages = data.pop('cepages', [])
            cuvee, created = Cuvee.objects.get_or_create(
                organization=organization,
                nom=data['nom'],
                defaults=data
            )
            
            if created and cepages:
                cuvee.cepages.set(cepages)
                
            if created:
                self.stdout.write(f"  [OK] {cuvee.nom} ({cuvee.get_couleur_display()})")
            else:
                self.stdout.write(f"  [EXIST] {cuvee.nom}")
