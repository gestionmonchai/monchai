"""
Commande pour initialiser les métadonnées
Roadmap Meta Base de Données - Phase P1
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.metadata.services import metadata_service
from apps.metadata.utils import create_search_index, create_trigram_index


class Command(BaseCommand):
    help = 'Initialise les métadonnées et index de recherche'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-indexes',
            action='store_true',
            help='Ignorer la création des index de recherche'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la recréation des métadonnées existantes'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Initialisation des métadonnées - Roadmap Meta Base de Données')
        )
        
        try:
            with transaction.atomic():
                # Phase P1: Découverte automatique des entités
                self.stdout.write('Phase P1: Découverte des entités métier...')
                metadata_service.auto_discover_entities()
                
                if not options['skip_indexes']:
                    # Phase P2: Création des index de recherche
                    self.stdout.write('Phase P2: Création des index de recherche...')
                    self.create_search_indexes()
                
                self.stdout.write(
                    self.style.SUCCESS('Métadonnées initialisées avec succès!')
                )
                
                # Statistiques
                self.show_statistics()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de l\'initialisation: {e}')
            )
            raise
    
    def create_search_indexes(self):
        """Crée les index de recherche pour les entités"""
        from django.apps import apps
        
        # Configuration des index par modèle
        index_config = {
            'referentiels.Cuvee': {
                'fulltext_fields': ['nom', 'appellation', 'description', 'notes_degustation'],
                'trigram_fields': ['nom', 'appellation']
            },
            'catalogue.Lot': {
                'fulltext_fields': ['numero_lot', 'notes'],
                'trigram_fields': ['numero_lot']
            },
            'referentiels.Cepage': {
                'fulltext_fields': ['nom', 'notes'],
                'trigram_fields': ['nom']
            },
            'referentiels.Parcelle': {
                'fulltext_fields': ['nom', 'lieu_dit', 'commune', 'appellation'],
                'trigram_fields': ['nom', 'commune']
            },
            'referentiels.Unite': {
                'fulltext_fields': ['nom'],
                'trigram_fields': ['nom']
            },
            'referentiels.Entrepot': {
                'fulltext_fields': ['nom', 'adresse', 'notes'],
                'trigram_fields': ['nom']
            },
            'accounts.Organization': {
                'fulltext_fields': ['name', 'email', 'address'],
                'trigram_fields': ['name']
            },
        }
        
        for model_path, config in index_config.items():
            try:
                app_label, model_name = model_path.split('.')
                model_class = apps.get_model(app_label, model_name)
                
                # Index full-text
                if config.get('fulltext_fields'):
                    self.stdout.write(f'  Index full-text pour {model_name}...')
                    create_search_index(model_class, config['fulltext_fields'])
                
                # Index trigrammes
                if config.get('trigram_fields'):
                    for field in config['trigram_fields']:
                        self.stdout.write(f'  Index trigramme pour {model_name}.{field}...')
                        create_trigram_index(model_class, field)
                
                self.stdout.write(f'  Index créés pour {model_name}')
                
            except Exception as e:
                self.stdout.write(f'  Erreur index {model_path}: {e}')
    
    def show_statistics(self):
        """Affiche les statistiques des métadonnées"""
        from apps.metadata.models import MetaEntity, MetaAttribute
        
        entities_count = MetaEntity.objects.filter(is_active=True).count()
        attributes_count = MetaAttribute.objects.filter(is_active=True).count()
        searchable_count = MetaEntity.objects.filter(is_searchable=True, is_active=True).count()
        facet_count = MetaAttribute.objects.filter(is_facet=True, is_active=True).count()
        
        self.stdout.write('\nStatistiques des métadonnées:')
        self.stdout.write(f'  • Entités métier: {entities_count}')
        self.stdout.write(f'  • Attributs: {attributes_count}')
        self.stdout.write(f'  • Entités recherchables: {searchable_count}')
        self.stdout.write(f'  • Attributs facettes: {facet_count}')
        
        # Détail par domaine
        from django.db.models import Count
        domains = MetaEntity.objects.filter(is_active=True).values('domain').annotate(
            count=Count('id')
        ).order_by('domain')
        
        if domains:
            self.stdout.write('\nRépartition par domaine:')
            for domain in domains:
                self.stdout.write(f'  • {domain["domain"]}: {domain["count"]} entité(s)')
        
        self.stdout.write('\nPrêt pour la Phase P3: API de recherche unifiée!')
