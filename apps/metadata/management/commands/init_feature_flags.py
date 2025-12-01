"""
Commande pour initialiser les feature flags
GIGA ROADMAP S0: search_v2_read, search_v2_write, inline_edit_v2_enabled
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.metadata.models import FeatureFlag


class Command(BaseCommand):
    help = 'Initialise les feature flags pour la GIGA ROADMAP'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remet tous les flags à False'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Initialisation des feature flags - GIGA ROADMAP S0')
        
        flags_data = [
            {
                'name': 'search_v2_read',
                'description': 'Utiliser le moteur de recherche V2 (FTS + trigram) pour la lecture',
                'is_enabled': False,
                'rollout_percentage': 0,
            },
            {
                'name': 'search_v2_write',
                'description': 'Écrire dans les index V2 (double-write phase)',
                'is_enabled': False,
                'rollout_percentage': 0,
            },
            {
                'name': 'inline_edit_v2_enabled',
                'description': 'Activer l\'édition inline dans les listes (double-clic)',
                'is_enabled': False,
                'rollout_percentage': 0,
            },
            {
                'name': 'search_metrics_enabled',
                'description': 'Capturer les métriques de recherche pour monitoring',
                'is_enabled': True,  # Activé par défaut pour S0
                'rollout_percentage': 100,
            },
            {
                'name': 'search_cache_enabled',
                'description': 'Utiliser le cache Redis pour les résultats de recherche',
                'is_enabled': False,
                'rollout_percentage': 0,
            },
        ]
        
        try:
            with transaction.atomic():
                for flag_data in flags_data:
                    flag, created = FeatureFlag.objects.get_or_create(
                        name=flag_data['name'],
                        defaults=flag_data
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Flag cree: {flag.name}')
                        )
                    else:
                        if options['reset']:
                            flag.is_enabled = flag_data['is_enabled']
                            flag.rollout_percentage = flag_data['rollout_percentage']
                            flag.description = flag_data['description']
                            flag.save()
                            self.stdout.write(
                                self.style.WARNING(f'Flag reinitialise: {flag.name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f'Flag existant: {flag.name}')
                            )
                
                self.stdout.write('\nEtat des feature flags:')
                for flag in FeatureFlag.objects.all().order_by('name'):
                    status = "ON" if flag.is_enabled else "OFF"
                    percentage = f" ({flag.rollout_percentage}%)" if flag.rollout_percentage > 0 else ""
                    self.stdout.write(f'  - {flag.name}: {status}{percentage}')
                
                self.stdout.write(
                    self.style.SUCCESS('\nFeature flags initialises avec succes!')
                )
                self.stdout.write(
                    'Prochaine étape: S1 - Schéma v2 add-only'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de l initialisation: {e}')
            )
            raise
