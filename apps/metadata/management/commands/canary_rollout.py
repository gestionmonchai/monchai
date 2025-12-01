"""
Commande pour gérer le canary rollout
GIGA ROADMAP S3: activation progressive par pourcentage
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.metadata.models import FeatureFlag


class Command(BaseCommand):
    help = 'Gère le canary rollout des feature flags'
    
    def add_arguments(self, parser):
        parser.add_argument('flag_name', type=str, help='Nom du feature flag')
        parser.add_argument('percentage', type=int, help='Pourcentage d\'activation (0-100)')
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Activer le flag globalement'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Désactiver le flag globalement'
        )
    
    def handle(self, *args, **options):
        flag_name = options['flag_name']
        percentage = options['percentage']
        
        if percentage < 0 or percentage > 100:
            self.stdout.write(
                self.style.ERROR('Le pourcentage doit être entre 0 et 100')
            )
            return
        
        try:
            with transaction.atomic():
                flag = FeatureFlag.objects.get(name=flag_name)
                
                if options['enable']:
                    flag.is_enabled = True
                    flag.rollout_percentage = percentage
                    flag.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Flag {flag_name} ACTIVÉ à {percentage}%')
                    )
                elif options['disable']:
                    flag.is_enabled = False
                    flag.rollout_percentage = 0
                    flag.save()
                    self.stdout.write(
                        self.style.WARNING(f'Flag {flag_name} DÉSACTIVÉ')
                    )
                else:
                    # Juste changer le pourcentage
                    if flag.is_enabled:
                        flag.rollout_percentage = percentage
                        flag.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Flag {flag_name} mis à jour: {percentage}%')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Flag {flag_name} est désactivé. Utilisez --enable pour l\'activer.')
                        )
                
                # Afficher l'état actuel
                self.show_flag_status(flag)
                
        except FeatureFlag.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Feature flag "{flag_name}" non trouvé')
            )
            self.stdout.write('Flags disponibles:')
            for flag in FeatureFlag.objects.all():
                self.stdout.write(f'  - {flag.name}')
    
    def show_flag_status(self, flag):
        """Affiche l'état détaillé du flag"""
        self.stdout.write('\nÉtat du flag:')
        self.stdout.write(f'  Nom: {flag.name}')
        self.stdout.write(f'  Activé: {"OUI" if flag.is_enabled else "NON"}')
        self.stdout.write(f'  Rollout: {flag.rollout_percentage}%')
        self.stdout.write(f'  Organisations spécifiques: {flag.enabled_organizations.count()}')
        self.stdout.write(f'  Dernière MAJ: {flag.updated_at.strftime("%d/%m/%Y %H:%M")}')
        
        if flag.is_enabled and flag.rollout_percentage > 0:
            estimated_users = int(flag.rollout_percentage * 10)  # Estimation
            self.stdout.write(f'  Utilisateurs estimés: ~{estimated_users}')
        
        self.stdout.write(f'\nDescription: {flag.description}')
