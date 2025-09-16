"""
Commande pour créer des données de démonstration
Usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from monchai.apps.accounts.models import Domaine, Profile
from monchai.apps.core.models import Parcelle, Cuve, Vendange, Lot
from monchai.apps.core.services import MouvementService, MiseEnBouteilleService

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour Mon Chai'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime toutes les données existantes avant de créer les nouvelles',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Suppression des données existantes...')
            # Supprimer dans l'ordre inverse des dépendances
            from monchai.apps.core.models import BouteilleLot, Mouvement
            BouteilleLot.objects.all().delete()
            Mouvement.objects.all().delete()
            Lot.objects.all().delete()
            Vendange.objects.all().delete()
            Cuve.objects.all().delete()
            Parcelle.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Domaine.objects.all().delete()

        self.stdout.write('Création des données de démonstration...')

        # 1. Créer le domaine
        domaine, created = Domaine.objects.get_or_create(
            nom="Domaine des Coteaux",
            defaults={
                'siret': '12345678901234',
                'adresse': '123 Route des Vignes',
                'code_postal': '44000',
                'ville': 'Nantes',
                'telephone': '02.40.12.34.56',
                'email_contact': 'contact@domainedescoteaux.fr'
            }
        )
        if created:
            self.stdout.write(f'[OK] Domaine cree: {domaine.nom}')

        # 2. Créer l'utilisateur de démo
        user, created = User.objects.get_or_create(
            email='demo@monchai.fr',
            defaults={
                'first_name': 'Jean',
                'last_name': 'Vigneron',
                'is_staff': True
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'[OK] Utilisateur cree: {user.email} (mot de passe: demo123)')

        # 3. Créer le profil
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'domaine': domaine,
                'role': 'admin_domaine'
            }
        )
        if created:
            self.stdout.write(f'[OK] Profil cree: {profile.get_role_display()}')

        # 4. Créer les parcelles
        parcelles_data = [
            {
                'nom': 'Les Carrières',
                'cepage': 'Melon B.',
                'surface_ha': Decimal('1.2'),
                'lat': 47.1234,
                'lng': -1.5678,
                'annee_plantation': 2008
            },
            {
                'nom': 'La Côte',
                'cepage': 'Chardonnay',
                'surface_ha': Decimal('0.8'),
                'lat': 47.1245,
                'lng': -1.5689,
                'annee_plantation': 2012
            },
            {
                'nom': 'Le Clos',
                'cepage': 'Sauvignon Blanc',
                'surface_ha': Decimal('1.5'),
                'lat': 47.1256,
                'lng': -1.5700,
                'annee_plantation': 2005
            }
        ]

        parcelles = []
        for data in parcelles_data:
            parcelle, created = Parcelle.objects.get_or_create(
                domaine=domaine,
                nom=data['nom'],
                defaults=data
            )
            parcelles.append(parcelle)
            if created:
                self.stdout.write(f'[OK] Parcelle creee: {parcelle.nom} - {parcelle.cepage}')

        # 5. Créer les cuves
        cuves_data = [
            {
                'nom': 'Cuve Inox 1',
                'capacite_hl': Decimal('100'),
                'materiau': 'inox'
            },
            {
                'nom': 'Cuve Inox 2',
                'capacite_hl': Decimal('80'),
                'materiau': 'inox'
            },
            {
                'nom': 'Cuve Béton',
                'capacite_hl': Decimal('150'),
                'materiau': 'beton'
            },
            {
                'nom': 'Fût Chêne',
                'capacite_hl': Decimal('2.25'),
                'materiau': 'bois'
            }
        ]

        cuves = []
        for data in cuves_data:
            cuve, created = Cuve.objects.get_or_create(
                domaine=domaine,
                nom=data['nom'],
                defaults=data
            )
            cuves.append(cuve)
            if created:
                self.stdout.write(f'[OK] Cuve créée: {cuve.nom} ({cuve.capacite_hl} hl)')

        # 6. Créer des vendanges récentes
        vendanges_data = [
            {
                'parcelle': parcelles[0],  # Les Carrières - Melon B.
                'date': date.today() - timedelta(days=10),
                'volume_hl': Decimal('25.4'),
                'dechets_hl': Decimal('0.8'),
                'commentaire': 'Belle vendange, raisins sains'
            },
            {
                'parcelle': parcelles[1],  # La Côte - Chardonnay
                'date': date.today() - timedelta(days=8),
                'volume_hl': Decimal('18.2'),
                'dechets_hl': Decimal('0.5'),
                'commentaire': 'Vendange précoce, bon potentiel'
            },
            {
                'parcelle': parcelles[2],  # Le Clos - Sauvignon Blanc
                'date': date.today() - timedelta(days=5),
                'volume_hl': Decimal('32.1'),
                'dechets_hl': Decimal('1.2'),
                'commentaire': 'Vendange tardive, concentration optimale'
            }
        ]

        vendanges = []
        for data in vendanges_data:
            vendange, created = Vendange.objects.get_or_create(
                parcelle=data['parcelle'],
                date=data['date'],
                defaults=data
            )
            vendanges.append(vendange)
            if created:
                self.stdout.write(f'[OK] Vendange créée: {vendange.parcelle.nom} - {vendange.date}')

        # 7. Créer des mouvements vendange → cuve et les valider
        mouvements_data = [
            (vendanges[0], cuves[0]),  # Melon B. → Cuve Inox 1
            (vendanges[1], cuves[1]),  # Chardonnay → Cuve Inox 2
            (vendanges[2], cuves[2]),  # Sauvignon → Cuve Béton
        ]

        lots_crees = []
        for vendange, cuve in mouvements_data:
            try:
                # Créer le mouvement vendange vers cuve
                mouvement = MouvementService.create_vendange_vers_cuve(
                    vendange_id=vendange.id,
                    destination_cuve_id=cuve.id,
                    date=vendange.date
                )
                
                # Valider le mouvement
                mouvement_valide = MouvementService.valider_mouvement(mouvement.id)
                
                # Récupérer le lot créé
                lot = Lot.objects.filter(cuve=cuve).first()
                if lot:
                    lots_crees.append(lot)
                
                self.stdout.write(f'[OK] Mouvement validé: {vendange.parcelle.nom} → {cuve.nom} ({mouvement_valide.volume_hl} hl)')
                
            except Exception as e:
                self.stdout.write(f'[ERROR] Erreur mouvement {vendange.parcelle.nom}: {str(e)}')

        # 8. Créer quelques mouvements inter-cuves
        if len(lots_crees) >= 2:
            try:
                # Transfert partiel du lot 1 vers le fût de chêne
                mouvement_inter = MouvementService.create_inter_cuves(
                    source_lot_id=lots_crees[0].id,
                    destination_cuve_id=cuves[3].id,  # Fût Chêne
                    volume_hl=Decimal('2.0'),
                    date=date.today() - timedelta(days=3),
                    commentaire='Élevage en fût de chêne',
                    domaine=domaine
                )
                
                MouvementService.valider_mouvement(mouvement_inter.id)
                self.stdout.write(f'[OK] Mouvement inter-cuves validé: 2.0 hl vers fût chêne')
                
            except Exception as e:
                self.stdout.write(f'[ERROR] Erreur mouvement inter-cuves: {str(e)}')

        # 9. Créer une mise en bouteille
        if lots_crees:
            try:
                # Mise en bouteille d'une partie du premier lot
                mouvement_bouteille, bouteille_lot = MiseEnBouteilleService.executer_mise_en_bouteille(
                    source_lot_id=lots_crees[0].id,
                    nb_bouteilles=1000,
                    contenance_ml=750,
                    taux_perte_hl=Decimal('0.15'),
                    date=date.today() - timedelta(days=1),
                    domaine=domaine
                )
                
                self.stdout.write(f'[OK] Mise en bouteille réalisée: {bouteille_lot.nb_bouteilles} bouteilles de {bouteille_lot.contenance_ml}ml')
                
            except Exception as e:
                self.stdout.write(f'[ERROR] Erreur mise en bouteille: {str(e)}')

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Donnees de demonstration creees avec succes !'))
        self.stdout.write('\nResume:')
        self.stdout.write(f'   - Domaine: {domaine.nom}')
        self.stdout.write(f'   - Utilisateur: {user.email} (mot de passe: demo123)')
        self.stdout.write(f'   - Parcelles: {Parcelle.objects.filter(domaine=domaine).count()}')
        self.stdout.write(f'   - Cuves: {Cuve.objects.filter(domaine=domaine).count()}')
        self.stdout.write(f'   - Vendanges: {Vendange.objects.filter(parcelle__domaine=domaine).count()}')
        self.stdout.write(f'   - Lots actifs: {Lot.objects.filter(domaine=domaine, volume_disponible_hl__gt=0).count()}')
        self.stdout.write(f'   - Mouvements: {domaine.mouvements.count()}')
        self.stdout.write(f'   - Lots bouteilles: {domaine.bouteille_lots.count()}')
        
        self.stdout.write('\nAccedez au dashboard: http://127.0.0.1:8000/')
        self.stdout.write('Connexion admin: http://127.0.0.1:8000/admin/')
