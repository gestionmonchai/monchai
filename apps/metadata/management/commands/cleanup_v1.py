"""
Commande de cleanup V1 - GIGA ROADMAP S5
Suppression sécurisée des anciens composants V1
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from apps.metadata.models import FeatureFlag


class Command(BaseCommand):
    help = 'Nettoie les composants V1 après migration complète vers V2'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans modifications réelles'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer le cleanup même si V2 n\'est pas à 100%'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('GIGA ROADMAP S5 - Cleanup V1')
        
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune modification'))
        
        # Vérifier que V2 est complètement déployé
        if not force and not self.is_v2_fully_deployed():
            self.stdout.write(
                self.style.ERROR('V2 n\'est pas complètement déployé. Utilisez --force pour continuer.')
            )
            return
        
        try:
            with transaction.atomic():
                # 1. Supprimer les colonnes search_tsv V1 (si elles existent)
                self.cleanup_v1_columns(dry_run)
                
                # 2. Supprimer les anciens index V1
                self.cleanup_v1_indexes(dry_run)
                
                # 3. Supprimer les anciennes vues AJAX V1
                self.cleanup_v1_views(dry_run)
                
                # 4. Nettoyer les métriques anciennes (> 30 jours)
                self.cleanup_old_metrics(dry_run)
                
                # 5. Désactiver les flags de migration
                self.cleanup_migration_flags(dry_run)
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS('Cleanup V1 terminé avec succès!')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Simulation terminée. Utilisez sans --dry-run pour appliquer.')
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur durant le cleanup: {e}')
            )
            raise
    
    def is_v2_fully_deployed(self):
        """Vérifie que V2 est complètement déployé"""
        try:
            search_v2_flag = FeatureFlag.objects.get(name='search_v2_read')
            return search_v2_flag.is_enabled and search_v2_flag.rollout_percentage >= 100
        except FeatureFlag.DoesNotExist:
            return False
    
    def cleanup_v1_columns(self, dry_run):
        """Supprime les colonnes search_tsv V1"""
        self.stdout.write('Nettoyage des colonnes V1...')
        
        if connection.vendor != 'postgresql':
            self.stdout.write('PostgreSQL requis pour cleanup colonnes - ignoré')
            return
        
        tables_to_clean = [
            'referentiels_cepage',
            'referentiels_parcelle', 
            'referentiels_unite'
        ]
        
        with connection.cursor() as cursor:
            for table in tables_to_clean:
                # Vérifier si la colonne existe
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name = 'search_tsv';
                """)
                
                if cursor.fetchone():
                    if not dry_run:
                        cursor.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS search_tsv;")
                    self.stdout.write(f'  - Colonne search_tsv supprimée de {table}')
                else:
                    self.stdout.write(f'  - Colonne search_tsv déjà absente de {table}')
    
    def cleanup_v1_indexes(self, dry_run):
        """Supprime les anciens index V1"""
        self.stdout.write('Nettoyage des index V1...')
        
        if connection.vendor != 'postgresql':
            return
        
        v1_indexes = [
            'idx_referentiels_cepage_search_tsv',
            'idx_referentiels_parcelle_search_tsv',
            'idx_referentiels_unite_search_tsv',
        ]
        
        with connection.cursor() as cursor:
            for index_name in v1_indexes:
                if not dry_run:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
                self.stdout.write(f'  - Index {index_name} supprimé')
    
    def cleanup_v1_views(self, dry_run):
        """Nettoie les références aux vues V1 (documentation)"""
        self.stdout.write('Documentation des vues V1 à supprimer...')
        
        v1_views = [
            'cepage_search_ajax (V1)',
            'parcelle_search_ajax (V1)', 
            'unite_search_ajax (V1)',
        ]
        
        for view in v1_views:
            self.stdout.write(f'  - Vue à supprimer: {view}')
        
        self.stdout.write('  Note: Suppression manuelle des vues V1 recommandée')
    
    def cleanup_old_metrics(self, dry_run):
        """Nettoie les anciennes métriques (> 30 jours)"""
        self.stdout.write('Nettoyage des anciennes métriques...')
        
        from django.utils import timezone
        from datetime import timedelta
        from apps.metadata.models import SearchMetrics
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_metrics = SearchMetrics.objects.filter(created_at__lt=cutoff_date)
        count = old_metrics.count()
        
        if not dry_run:
            old_metrics.delete()
        
        self.stdout.write(f'  - {count} métriques anciennes supprimées')
    
    def cleanup_migration_flags(self, dry_run):
        """Désactive les flags de migration"""
        self.stdout.write('Nettoyage des flags de migration...')
        
        migration_flags = [
            'search_v2_write',  # Double-write plus nécessaire
        ]
        
        for flag_name in migration_flags:
            try:
                flag = FeatureFlag.objects.get(name=flag_name)
                if not dry_run:
                    flag.is_enabled = False
                    flag.rollout_percentage = 0
                    flag.save()
                self.stdout.write(f'  - Flag {flag_name} désactivé')
            except FeatureFlag.DoesNotExist:
                self.stdout.write(f'  - Flag {flag_name} déjà absent')
    
    def show_cleanup_summary(self):
        """Affiche un résumé du cleanup"""
        self.stdout.write('\nRésumé du cleanup V1:')
        self.stdout.write('  - Colonnes search_tsv V1 supprimées')
        self.stdout.write('  - Index V1 supprimés')
        self.stdout.write('  - Métriques anciennes nettoyées')
        self.stdout.write('  - Flags de migration désactivés')
        self.stdout.write('\nV2 est maintenant le seul moteur actif!')
        self.stdout.write('GIGA ROADMAP: 100% TERMINÉE')
