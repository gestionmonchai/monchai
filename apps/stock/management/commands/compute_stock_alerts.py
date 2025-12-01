"""
Commande de gestion pour calculer les alertes de stock - Roadmap 34
Usage: python manage.py compute_stock_alerts [--org-id UUID] [--dry-run]
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.accounts.models import Organization
from apps.stock.services import StockAlertService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calcule et met à jour les alertes de stock pour toutes les organisations ou une organisation spécifique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=str,
            help='ID de l\'organisation à traiter (optionnel, toutes par défaut)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation sans modifications en base'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - Aucune modification ne sera effectuée')
            )
        
        # Déterminer les organisations à traiter
        if options['org_id']:
            try:
                organizations = [Organization.objects.get(id=options['org_id'])]
            except Organization.DoesNotExist:
                raise CommandError(f"Organisation {options['org_id']} non trouvée")
        else:
            organizations = Organization.objects.all()
        
        total_created = 0
        total_resolved = 0
        total_active = 0
        
        self.stdout.write(f"Traitement de {organizations.count()} organisation(s)...")
        
        for org in organizations:
            if options['verbose']:
                self.stdout.write(f"\n--- Organisation: {org.name} ({org.id}) ---")
            
            try:
                if not options['dry_run']:
                    # Exécution réelle
                    result = StockAlertService.compute_stock_alerts(org)
                else:
                    # Mode dry-run : simulation
                    result = self._simulate_compute_alerts(org)
                
                org_created = result['created_count']
                org_resolved = result['resolved_count']
                org_active = result['total_active']
                
                total_created += org_created
                total_resolved += org_resolved
                total_active += org_active
                
                if options['verbose'] or org_created > 0 or org_resolved > 0:
                    self.stdout.write(
                        f"  {org.name}: "
                        f"{org_created} créées, "
                        f"{org_resolved} résolues, "
                        f"{org_active} actives"
                    )
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'organisation {org.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"Erreur pour {org.name}: {e}")
                )
                continue
        
        # Résumé final
        elapsed = timezone.now() - start_time
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Traitement terminé en {elapsed.total_seconds():.2f}s"
            )
        )
        self.stdout.write(f"Total alertes créées: {total_created}")
        self.stdout.write(f"Total alertes résolues: {total_resolved}")
        self.stdout.write(f"Total alertes actives: {total_active}")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("Mode DRY-RUN - Aucune modification effectuée")
            )
    
    def _simulate_compute_alerts(self, organization):
        """
        Simule le calcul des alertes sans modifications en base
        """
        from apps.stock.models import StockVracBalance, StockAlert
        
        created_count = 0
        resolved_count = 0
        
        # Simuler le traitement des balances
        balances = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0
        ).select_related('lot', 'warehouse', 'lot__cuvee')
        
        for balance in balances:
            threshold_value, threshold_source = StockAlertService.get_applicable_threshold(
                organization, balance.lot, balance.warehouse
            )
            
            if threshold_value is None:
                # Compter les alertes qui seraient résolues
                existing_alerts = StockAlert.objects.filter(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                )
                resolved_count += existing_alerts.count()
                continue
            
            if balance.qty_l < threshold_value:
                # Vérifier si une alerte serait créée
                existing = StockAlert.objects.filter(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                ).exists()
                
                if not existing:
                    created_count += 1
            else:
                # Compter les alertes qui seraient résolues
                existing_alerts = StockAlert.objects.filter(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                )
                resolved_count += existing_alerts.count()
        
        # Compter les alertes actuellement actives
        total_active = StockAlert.objects.filter(
            organization=organization,
            acknowledged_at__isnull=True,
            auto_resolved_at__isnull=True
        ).count()
        
        return {
            'created_count': created_count,
            'resolved_count': resolved_count,
            'total_active': total_active + created_count - resolved_count
        }
