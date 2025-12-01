"""
Commande pour créer les widgets par défaut du dashboard
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import DashboardWidget


class Command(BaseCommand):
    help = 'Crée les widgets par défaut pour le dashboard personnalisable'

    def handle(self, *args, **options):
        widgets_data = [
            # Métriques principales
            {
                'code': 'volume_recolte',
                'name': 'Volume Récolté',
                'description': 'Volume récolté de la campagne en cours (vendanges)',
                'widget_type': 'metric',
                'icon': 'bi-basket3',
            },
            {
                'code': 'volume_cuve',
                'name': 'Volume en Cuve',
                'description': 'Volume total en stock (cuves)',
                'widget_type': 'metric',
                'icon': 'bi-droplet-fill',
            },
            {
                'code': 'chiffre_affaires',
                'name': 'Chiffre d\'Affaires',
                'description': 'CA de l\'année en cours (factures)',
                'widget_type': 'metric',
                'icon': 'bi-currency-euro',
            },
            
            # Statistiques
            {
                'code': 'clients_actifs',
                'name': 'Clients Actifs',
                'description': 'Nombre de clients actifs',
                'widget_type': 'metric',
                'icon': 'bi-people',
            },
            {
                'code': 'cuvees_actives',
                'name': 'Cuvées Actives',
                'description': 'Nombre de cuvées actives',
                'widget_type': 'metric',
                'icon': 'bi-grid-3x3-gap',
            },
            {
                'code': 'commandes_en_cours',
                'name': 'Commandes en Cours',
                'description': 'Commandes non expédiées',
                'widget_type': 'metric',
                'icon': 'bi-cart',
            },
            {
                'code': 'factures_impayees',
                'name': 'Factures Impayées',
                'description': 'Montant total des factures impayées',
                'widget_type': 'metric',
                'icon': 'bi-exclamation-triangle',
            },
            
            # Raccourcis actions rapides
            {
                'code': 'shortcut_clients',
                'name': 'Gérer les Clients',
                'description': 'Accès rapide à la gestion clients',
                'widget_type': 'shortcut',
                'icon': 'bi-people',
            },
            {
                'code': 'shortcut_cuvees',
                'name': 'Gérer les Cuvées',
                'description': 'Accès rapide au catalogue',
                'widget_type': 'shortcut',
                'icon': 'bi-grid-3x3-gap',
            },
            {
                'code': 'shortcut_stocks',
                'name': 'Stocks & Transferts',
                'description': 'Gestion des stocks',
                'widget_type': 'shortcut',
                'icon': 'bi-boxes',
            },
            {
                'code': 'shortcut_vendanges',
                'name': 'Vendanges',
                'description': 'Gestion des vendanges',
                'widget_type': 'shortcut',
                'icon': 'bi-basket3',
            },
            {
                'code': 'shortcut_factures',
                'name': 'Factures',
                'description': 'Gestion des factures',
                'widget_type': 'shortcut',
                'icon': 'bi-receipt',
            },
            {
                'code': 'shortcut_config',
                'name': 'Configuration',
                'description': 'Paramètres et configuration',
                'widget_type': 'shortcut',
                'icon': 'bi-gear',
            },
            
            # Listes et graphiques (future)
            {
                'code': 'derniers_clients',
                'name': 'Derniers Clients',
                'description': 'Liste des derniers clients créés',
                'widget_type': 'list',
                'icon': 'bi-person-plus',
            },
            {
                'code': 'dernieres_factures',
                'name': 'Dernières Factures',
                'description': 'Liste des dernières factures',
                'widget_type': 'list',
                'icon': 'bi-receipt-cutoff',
            },
            {
                'code': 'ventes_mois',
                'name': 'Ventes du Mois',
                'description': 'Graphique des ventes mensuelles',
                'widget_type': 'chart',
                'icon': 'bi-bar-chart',
            },
            
            # Alertes
            {
                'code': 'alertes_critiques',
                'name': 'Alertes Critiques',
                'description': 'Factures en retard, stocks faibles, commandes urgentes',
                'widget_type': 'alert',
                'icon': 'bi-exclamation-triangle',
            },
            {
                'code': 'alertes_stock',
                'name': 'Alertes Stocks',
                'description': 'Anomalies et alertes liées aux stocks',
                'widget_type': 'alert',
                'icon': 'bi-box-seam',
            },
            
            # Activités récentes
            {
                'code': 'dernieres_actions',
                'name': 'Dernières Actions',
                'description': 'Activité récente sur le système (7 derniers jours)',
                'widget_type': 'list',
                'icon': 'bi-clock-history',
            },
            {
                'code': 'top_clients',
                'name': 'Top Clients',
                'description': 'Meilleurs clients par chiffre d\'affaires',
                'widget_type': 'list',
                'icon': 'bi-trophy',
            },
            {
                'code': 'commandes_urgentes',
                'name': 'Commandes Urgentes',
                'description': 'Commandes à traiter en priorité',
                'widget_type': 'list',
                'icon': 'bi-exclamation-circle',
            },
            
            # Nouveaux widgets intelligents
            {
                'code': 'clients_inactifs',
                'name': 'Clients Inactifs',
                'description': 'Clients sans commande depuis 6 mois',
                'widget_type': 'list',
                'icon': 'bi-person-x',
            },
            {
                'code': 'stock_par_cuvee',
                'name': 'Stock par Cuvée',
                'description': 'Répartition du stock vrac par cuvée',
                'widget_type': 'list',
                'icon': 'bi-pie-chart',
            },
            {
                'code': 'factures_a_echeance',
                'name': 'Factures à Échéance',
                'description': 'Factures arrivant à échéance dans 7 jours',
                'widget_type': 'list',
                'icon': 'bi-calendar-event',
            },
            {
                'code': 'performance_mois',
                'name': 'Performance du Mois',
                'description': 'Statistiques du mois en cours',
                'widget_type': 'metric',
                'icon': 'bi-graph-up-arrow',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for widget_data in widgets_data:
            widget, created = DashboardWidget.objects.update_or_create(
                code=widget_data['code'],
                defaults=widget_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'[OK] Cree: {widget.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'[MAJ] Mis a jour: {widget.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] Total: {created_count} crees, {updated_count} mis a jour'))
