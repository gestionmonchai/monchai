"""
Commande Django pour créer des unités par défaut
Roadmap item 16: /ref/unites – Liste unités (bouteille, hl, L)
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Organization
from apps.referentiels.models import Unite


class Command(BaseCommand):
    help = 'Crée des unités par défaut pour toutes les organisations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=int,
            help='ID de l\'organisation (optionnel, sinon toutes les organisations)',
        )

    def handle(self, *args, **options):
        org_id = options.get('org_id')
        
        if org_id:
            organizations = Organization.objects.filter(id=org_id)
            if not organizations.exists():
                self.stdout.write(
                    self.style.ERROR(f'Organisation avec ID {org_id} non trouvée')
                )
                return
        else:
            organizations = Organization.objects.all()

        # Unités par défaut selon roadmap
        default_units = [
            # Volume
            {'nom': 'Bouteille', 'symbole': 'btl', 'type_unite': 'volume', 'facteur_conversion': 0.75},
            {'nom': 'Magnum', 'symbole': 'mag', 'type_unite': 'volume', 'facteur_conversion': 1.5},
            {'nom': 'Litre', 'symbole': 'L', 'type_unite': 'volume', 'facteur_conversion': 1.0},
            {'nom': 'Hectolitre', 'symbole': 'hL', 'type_unite': 'volume', 'facteur_conversion': 100.0},
            
            # Quantité
            {'nom': 'Carton 6', 'symbole': 'crt6', 'type_unite': 'quantite', 'facteur_conversion': 6.0},
            {'nom': 'Carton 12', 'symbole': 'crt12', 'type_unite': 'quantite', 'facteur_conversion': 12.0},
            {'nom': 'Palette', 'symbole': 'plt', 'type_unite': 'quantite', 'facteur_conversion': 600.0},
            
            # Poids
            {'nom': 'Kilogramme', 'symbole': 'kg', 'type_unite': 'poids', 'facteur_conversion': 1.0},
            
            # Surface
            {'nom': 'Hectare', 'symbole': 'ha', 'type_unite': 'surface', 'facteur_conversion': 10000.0},
        ]

        total_created = 0
        total_skipped = 0

        with transaction.atomic():
            for org in organizations:
                self.stdout.write(f'Traitement organisation: {org.name}')
                
                for unit_data in default_units:
                    unite, created = Unite.objects.get_or_create(
                        organization=org,
                        nom=unit_data['nom'],
                        defaults={
                            'symbole': unit_data['symbole'],
                            'type_unite': unit_data['type_unite'],
                            'facteur_conversion': unit_data['facteur_conversion'],
                        }
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(
                            f'  ✓ Créé: {unite.nom} ({unite.symbole})'
                        )
                    else:
                        total_skipped += 1
                        self.stdout.write(
                            f'  - Existe: {unite.nom} ({unite.symbole})'
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTerminé! {total_created} unités créées, {total_skipped} ignorées (déjà existantes)'
            )
        )
