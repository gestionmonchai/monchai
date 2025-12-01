"""
Commande d'audit de l'admin registry - Sentinelle anti-régression
Vérifie qu'aucun modèle métier n'est enregistré dans l'admin Django
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib import admin


class Command(BaseCommand):
    help = 'Audit de l\'admin registry pour détecter les modèles métier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-metier',
            action='store_true',
            help='Échouer si des modèles métier sont détectés',
        )
        parser.add_argument(
            '--show-all',
            action='store_true',
            help='Afficher tous les modèles enregistrés',
        )

    def handle(self, *args, **options):
        # Apps métier interdites dans l'admin
        metier_apps = ['billing', 'sales', 'stock', 'viticulture', 'clients', 'catalogue', 'referentiels', 'imports']
        
        # Apps techniques autorisées
        technique_apps = ['auth', 'accounts', 'sites', 'admin', 'redirects', 'django_celery_beat']
        
        metier_models = []
        technique_models = []
        other_models = []
        
        # Analyser tous les modèles enregistrés
        for model in admin.site._registry:
            app_label = model._meta.app_label
            model_name = f'{app_label}.{model.__name__}'
            
            if app_label in metier_apps:
                # Exception: sales.Customer est autorisé pour redirection
                if model_name == 'sales.Customer':
                    continue
                metier_models.append(model_name)
            elif app_label in technique_apps:
                technique_models.append(model_name)
            else:
                other_models.append(model_name)
        
        # Affichage des résultats
        self.stdout.write(
            self.style.SUCCESS(f'=== AUDIT ADMIN REGISTRY ===')
        )
        
        if options['show_all']:
            self.stdout.write(f'\nModèles techniques ({len(technique_models)}):')
            for model in sorted(technique_models):
                self.stdout.write(f'  + {model}')
            
            if other_models:
                self.stdout.write(f'\nAutres modèles ({len(other_models)}):')
                for model in sorted(other_models):
                    self.stdout.write(f'  ? {model}')
        
        # Vérification des modèles métier
        if metier_models:
            self.stdout.write(
                self.style.ERROR(f'\nMODELES METIER DETECTES ({len(metier_models)}):')
            )
            for model in sorted(metier_models):
                self.stdout.write(self.style.ERROR(f'  - {model}'))
            
            self.stdout.write(
                self.style.ERROR('\nVIOLATION DE LA LISTE BLANCHE ADMIN!')
            )
            self.stdout.write(
                self.style.ERROR('Les modèles métier doivent utiliser les interfaces back-office dédiées.')
            )
            
            if options['fail_on_metier']:
                raise CommandError('Modèles métier détectés dans l\'admin registry')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nAUDIT REUSSI: Aucun modèle métier dans l\'admin')
            )
        
        # Statistiques finales
        total_models = len(admin.site._registry)
        self.stdout.write(f'\nStatistiques:')
        self.stdout.write(f'  - Total modèles: {total_models}')
        self.stdout.write(f'  - Techniques: {len(technique_models)}')
        self.stdout.write(f'  - Autres: {len(other_models)}')
        self.stdout.write(f'  - Métier (interdits): {len(metier_models)}')
        
        if metier_models == 0:
            self.stdout.write(
                self.style.SUCCESS('\nCONFORMITE LISTE BLANCHE: 100%')
            )
