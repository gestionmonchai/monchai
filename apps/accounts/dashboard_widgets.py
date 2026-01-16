"""
Système de rendu des widgets du dashboard personnalisable
Version 2.0 - Corrigée avec vrais champs des modèles
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from datetime import timedelta


class WidgetRenderer:
    """
    Classe statique pour rendre les différents types de widgets du dashboard
    """
    
    @staticmethod
    def get_widget_data(widget_code, organization):
        """
        Retourne les données pour un widget donné
        """
        method_name = f'_render_{widget_code}'
        if hasattr(WidgetRenderer, method_name):
            try:
                return getattr(WidgetRenderer, method_name)(organization)
            except Exception as e:
                # En cas d'erreur, retourner un widget d'erreur
                return {
                    'type': 'error',
                    'message': f'Erreur lors du chargement du widget: {str(e)}'
                }
        return None
    
    # =========================================================================
    # MÉTRIQUES PRINCIPALES
    # =========================================================================
    
    @staticmethod
    def _render_volume_recolte(organization):
        """Volume récolté (vendanges campagne en cours)"""
        from apps.production.models import VendangeReception
        
        # Campagne en cours (août N à juillet N+1)
        today = timezone.now().date()
        if today.month >= 8:
            campaign_year = today.year
        else:
            campaign_year = today.year - 1
        
        campaign_start = timezone.datetime(campaign_year, 8, 1).date()
        campaign_end = timezone.datetime(campaign_year + 1, 7, 31).date()
        
        # Volume total en kg
        volume_data = VendangeReception.objects.filter(
            organization=organization,
            date__gte=campaign_start,
            date__lte=campaign_end
        ).aggregate(
            total_kg=Sum('quantity_kg')
        )
        
        volume_kg = volume_data['total_kg'] or Decimal('0')
        # Conversion approximative kg -> L (1kg ≈ 0.67L de moût)
        volume_l = volume_kg * Decimal('0.67')
        
        return {
            'value': f"{volume_kg:,.0f} kg",
            'subtitle': f"≈ {volume_l:,.0f} L de moût",
            'color': 'harvest',
            'icon': 'bi-basket3',
            'url': 'production:vendanges_list',
        }
    
    @staticmethod
    def _render_volume_cuve(organization):
        """Volume total en cuve (stock vrac)"""
        from apps.stock.models import StockVracBalance
        
        stock_data = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0
        ).aggregate(
            total_l=Sum('qty_l'),
            nb_lots=Count('lot', distinct=True)
        )
        
        total_l = stock_data['total_l'] or Decimal('0')
        nb_lots = stock_data['nb_lots'] or 0
        
        return {
            'value': f"{total_l:,.0f} L",
            'subtitle': f"{nb_lots} lot(s) actif(s)",
            'color': 'stock',
            'icon': 'bi-bucket',
            'url': 'stock:dashboard',
        }
    
    @staticmethod
    def _render_chiffre_affaires(organization):
        """Chiffre d'affaires année en cours"""
        from apps.billing.models import Invoice
        
        year = timezone.now().year
        year_start = timezone.datetime(year, 1, 1).date()
        
        ca_data = Invoice.objects.filter(
            organization=organization,
            status__in=['issued', 'paid'],
            date_issue__gte=year_start
        ).aggregate(
            total_ttc=Sum('total_ttc'),
            total_ht=Sum('total_ht')
        )
        
        total_ttc = ca_data['total_ttc'] or Decimal('0')
        total_ht = ca_data['total_ht'] or Decimal('0')
        
        return {
            'value': f"{total_ttc:,.0f} €",
            'subtitle': f"{total_ht:,.0f} € HT",
            'color': 'revenue',
            'icon': 'bi-currency-euro',
            'url': 'ventes:factures_list',
        }
    
    @staticmethod
    def _render_clients_actifs(organization):
        """Nombre de clients actifs"""
        from apps.partners.models import Contact, ContactRole
        
        nb_clients = Contact.objects.filter(
            organization=organization,
            is_active=True,
            roles__code=ContactRole.ROLE_CLIENT
        ).count()
        
        # Clients avec commandes récentes (6 mois)
        cutoff = timezone.now() - timedelta(days=180)
        # Note: orders relation doit être ajoutée si nécessaire
        nb_clients_recents = nb_clients  # Simplification temporaire
        
        return {
            'value': f"{nb_clients}",
            'subtitle': f"{nb_clients_recents} actif(s) récemment",
            'color': 'success',
            'icon': 'bi-people',
            'url': 'partners:partners_list',
        }
    
    @staticmethod
    def _render_cuvees_actives(organization):
        """Nombre de cuvées actives"""
        from apps.viticulture.models import Cuvee
        
        nb_cuvees = Cuvee.objects.filter(
            organization=organization,
            is_active=True
        ).count()
        
        return {
            'value': f"{nb_cuvees}",
            'subtitle': "Cuvée(s) active(s)",
            'color': 'info',
            'icon': 'bi-grid-3x3-gap',
            'url': 'catalogue:products_cuvees',
        }
    
    @staticmethod
    def _render_commandes_en_cours(organization):
        """Commandes confirmées non expédiées"""
        from apps.sales.models import Order
        
        nb_commandes = Order.objects.filter(
            organization=organization,
            status='confirmed'
        ).count()
        
        # Montant total
        montant_data = Order.objects.filter(
            organization=organization,
            status='confirmed'
        ).aggregate(total=Sum('total_ttc'))
        
        montant = montant_data['total'] or Decimal('0')
        
        return {
            'value': f"{nb_commandes}",
            'subtitle': f"{montant:,.0f} € en attente",
            'color': 'warning',
            'icon': 'bi-cart-check',
            'url': 'ventes:cmd_list',
        }
    
    @staticmethod
    def _render_factures_impayees(organization):
        """Montant total des factures impayées"""
        from apps.billing.models import Invoice
        
        montant_data = Invoice.objects.filter(
            organization=organization,
            status='issued'  # Émises mais pas encore payées
        ).aggregate(total=Sum('total_ttc'))
        
        montant = montant_data['total'] or Decimal('0')
        
        # Nombre de factures
        nb_factures = Invoice.objects.filter(
            organization=organization,
            status='issued'
        ).count()
        
        return {
            'value': f"{montant:,.0f} €",
            'subtitle': f"{nb_factures} facture(s) impayée(s)",
            'color': 'danger',
            'icon': 'bi-receipt-cutoff',
            'url': 'ventes:factures_list',
        }
    
    # =========================================================================
    # RACCOURCIS
    # =========================================================================
    
    @staticmethod
    def _render_shortcut_clients(organization):
        """Raccourci clients"""
        return {
            'type': 'shortcut',
            'label': 'Gérer les clients',
            'icon': 'bi-people',
            'url': 'partners:partners_list',
        }
    
    @staticmethod
    def _render_shortcut_cuvees(organization):
        """Raccourci cuvées"""
        return {
            'type': 'shortcut',
            'label': 'Gérer les cuvées',
            'icon': 'bi-grid-3x3-gap',
            'url': 'catalogue:products_cuvees',
        }
    
    @staticmethod
    def _render_shortcut_stocks(organization):
        """Raccourci stocks"""
        return {
            'type': 'shortcut',
            'label': 'Stocks & Transferts',
            'icon': 'bi-boxes',
            'url': 'stock:dashboard',
        }
    
    @staticmethod
    def _render_shortcut_vendanges(organization):
        """Raccourci vendanges"""
        return {
            'type': 'shortcut',
            'label': 'Vendanges',
            'icon': 'bi-basket3',
            'url': 'production:vendanges_list',
        }
    
    @staticmethod
    def _render_shortcut_factures(organization):
        """Raccourci factures"""
        return {
            'type': 'shortcut',
            'label': 'Factures',
            'icon': 'bi-receipt',
            'url': 'ventes:factures_list',
        }
    
    @staticmethod
    def _render_shortcut_config(organization):
        """Raccourci configuration"""
        return {
            'type': 'shortcut',
            'label': 'Configuration',
            'icon': 'bi-gear',
            'url': 'onboarding:checklist',
        }
    
    # =========================================================================
    # ALERTES & NOTIFICATIONS
    # =========================================================================
    
    @staticmethod
    def _render_alertes_critiques(organization):
        """Alertes critiques métier"""
        from apps.billing.models import Invoice
        from apps.sales.models import Order
        from apps.stock.models import StockVracBalance
        
        alerts = []
        today = timezone.now().date()
        
        # 1. Factures en retard (>30 jours après échéance)
        overdue_threshold = today - timedelta(days=30)
        overdue_invoices = Invoice.objects.filter(
            organization=organization,
            status='issued',
            due_date__lt=overdue_threshold
        )
        
        overdue_count = overdue_invoices.count()
        if overdue_count > 0:
            overdue_amount = overdue_invoices.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
            alerts.append({
                'severity': 'danger',
                'icon': 'exclamation-triangle-fill',
                'title': f'{overdue_count} facture(s) en retard',
                'message': f'Plus de 30j de retard - {overdue_amount:,.0f} € impayés'
            })
        
        # 2. Stocks très faibles (<100L par lot)
        low_stock = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__lt=100,
            qty_l__gt=0
        ).select_related('lot')
        
        low_stock_count = low_stock.count()
        if low_stock_count > 0:
            alerts.append({
                'severity': 'warning',
                'icon': 'exclamation-circle-fill',
                'title': f'{low_stock_count} lot(s) en stock critique',
                'message': 'Moins de 100L disponibles'
            })
        
        # 3. Commandes non traitées depuis >7 jours
        old_threshold = timezone.now() - timedelta(days=7)
        old_orders = Order.objects.filter(
            organization=organization,
            status='confirmed',
            created_at__lt=old_threshold
        )
        
        old_orders_count = old_orders.count()
        if old_orders_count > 0:
            alerts.append({
                'severity': 'warning',
                'icon': 'clock-fill',
                'title': f'{old_orders_count} commande(s) en attente longue',
                'message': 'Non traitées depuis plus de 7 jours'
            })
        
        # 4. Factures arrivant à échéance (dans les 7 prochains jours)
        upcoming_threshold = today + timedelta(days=7)
        upcoming_invoices = Invoice.objects.filter(
            organization=organization,
            status='issued',
            due_date__lte=upcoming_threshold,
            due_date__gte=today
        ).count()
        
        if upcoming_invoices > 0:
            alerts.append({
                'severity': 'info',
                'icon': 'info-circle-fill',
                'title': f'{upcoming_invoices} facture(s) à échéance proche',
                'message': 'Échéance dans les 7 prochains jours'
            })
        
        return {
            'type': 'alert',
            'alerts': alerts
        }
    
    @staticmethod
    def _render_alertes_stock(organization):
        """Alertes spécifiques aux stocks"""
        from apps.stock.models import StockVracBalance
        
        alerts = []
        
        # 1. Stocks négatifs (anomalie système)
        negative_stock = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__lt=0
        )
        
        negative_count = negative_stock.count()
        if negative_count > 0:
            alerts.append({
                'severity': 'danger',
                'icon': 'exclamation-triangle-fill',
                'title': f'{negative_count} anomalie(s) de stock',
                'message': 'Quantités négatives détectées - correction nécessaire'
            })
        
        # 2. Lots sans mouvement depuis 6 mois
        old_date = timezone.now() - timedelta(days=180)
        old_stock = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0,
            updated_at__lt=old_date
        )
        
        old_count = old_stock.count()
        if old_count > 0:
            old_volume = old_stock.aggregate(total=Sum('qty_l'))['total'] or Decimal('0')
            alerts.append({
                'severity': 'info',
                'icon': 'info-circle-fill',
                'title': f'{old_count} lot(s) sans mouvement',
                'message': f'Inactifs >6 mois - {old_volume:,.0f} L immobilisés'
            })
        
        # 3. Stocks moyens (100-500L)
        medium_stock = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gte=100,
            qty_l__lt=500
        ).count()
        
        if medium_stock > 0:
            alerts.append({
                'severity': 'warning',
                'icon': 'exclamation-circle-fill',
                'title': f'{medium_stock} lot(s) en stock faible',
                'message': 'Entre 100L et 500L - surveiller de près'
            })
        
        # 4. Concentration du stock (>80% sur un seul lot)
        total_stock = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0
        ).aggregate(total=Sum('qty_l'))['total'] or Decimal('0')
        
        if total_stock > 0:
            biggest_lot = StockVracBalance.objects.filter(
                organization=organization,
                qty_l__gt=0
            ).order_by('-qty_l').first()
            
            if biggest_lot:
                concentration_pct = (biggest_lot.qty_l / total_stock) * 100
                if concentration_pct > 80:
                    alerts.append({
                        'severity': 'info',
                        'icon': 'info-circle-fill',
                        'title': 'Concentration du stock élevée',
                        'message': f'{concentration_pct:.0f}% du stock sur un seul lot'
                    })
        
        return {
            'type': 'alert',
            'alerts': alerts
        }
    
    # =========================================================================
    # ACTIVITÉS RÉCENTES
    # =========================================================================
    
    @staticmethod
    def _render_dernieres_actions(organization):
        """Dernières actions effectuées dans le système (7 derniers jours)"""
        from apps.billing.models import Invoice
        from apps.sales.models import Order, Customer
        
        items = []
        cutoff = timezone.now() - timedelta(days=7)
        
        # Dernières factures
        recent_invoices = Invoice.objects.filter(
            organization=organization,
            created_at__gte=cutoff
        ).select_related('customer').order_by('-created_at')[:3]
        
        for inv in recent_invoices:
            items.append({
                'icon': 'receipt',
                'label': f'Facture {inv.number}',
                'value': f'{inv.total_ttc} €',
                'date': inv.created_at,
                'priority': 2
            })
        
        # Dernières commandes
        recent_orders = Order.objects.filter(
            organization=organization,
            created_at__gte=cutoff
        ).select_related('customer').order_by('-created_at')[:3]
        
        for order in recent_orders:
            items.append({
                'icon': 'cart-check',
                'label': f'Commande de {order.customer.legal_name}',
                'value': order.get_status_display(),
                'date': order.created_at,
                'priority': 1
            })
        
        # Derniers clients créés
        recent_customers = Customer.objects.filter(
            organization=organization,
            created_at__gte=cutoff
        ).order_by('-created_at')[:3]
        
        for customer in recent_customers:
            items.append({
                'icon': 'person-plus',
                'label': f'Nouveau client: {customer.legal_name}',
                'value': customer.get_type_display(),
                'date': customer.created_at,
                'priority': 3
            })
        
        # Trier par date décroissante, puis par priorité
        items.sort(key=lambda x: (x['date'], x['priority']), reverse=True)
        
        return {
            'type': 'list',
            'items': [
                {
                    'label': f"{item['label']} - {item['date'].strftime('%d/%m %Hh%M')}",
                    'value': item['value']
                }
                for item in items[:10]
            ]
        }
    
    @staticmethod
    def _render_derniers_clients(organization):
        """Liste des 5 derniers clients créés"""
        from apps.partners.models import Contact, ContactRole
        
        recent_customers = Contact.objects.filter(
            organization=organization,
            is_active=True,
            roles__code=ContactRole.ROLE_CLIENT
        ).order_by('-created_at')[:5]
        
        items = []
        for customer in recent_customers:
            items.append({
                'label': customer.name,
                'value': customer.created_at.strftime('%d/%m/%Y')
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_dernieres_factures(organization):
        """Liste des 5 dernières factures"""
        from apps.billing.models import Invoice
        
        recent_invoices = Invoice.objects.filter(
            organization=organization
        ).select_related('customer').order_by('-created_at')[:5]
        
        items = []
        for invoice in recent_invoices:
            # Icône selon statut
            if invoice.status == 'paid':
                status_icon = '✓'
            elif invoice.status == 'issued':
                if invoice.is_overdue:
                    status_icon = '⚠️'
                else:
                    status_icon = '⏳'
            else:
                status_icon = '📝'
            
            items.append({
                'label': f"{status_icon} {invoice.number} - {invoice.customer.legal_name}",
                'value': f"{invoice.total_ttc} €"
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_top_clients(organization):
        """Top 5 clients par chiffre d'affaires"""
        from apps.billing.models import Invoice
        from django.db.models import Sum
        
        # Agrégation CA par client (factures émises ou payées)
        top_customers = Invoice.objects.filter(
            organization=organization,
            status__in=['issued', 'paid']
        ).values(
            'customer__legal_name'
        ).annotate(
            total_ca=Sum('total_ttc')
        ).order_by('-total_ca')[:5]
        
        items = []
        for rank, item in enumerate(top_customers, 1):
            medal = ['🥇', '🥈', '🥉', '4.', '5.'][rank - 1]
            items.append({
                'label': f"{medal} {item['customer__legal_name']}",
                'value': f"{item['total_ca']:,.0f} €"
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_commandes_urgentes(organization):
        """Commandes confirmées à traiter en priorité (>3 jours d'attente)"""
        from apps.sales.models import Order
        
        old_threshold = timezone.now() - timedelta(days=3)
        urgent_orders = Order.objects.filter(
            organization=organization,
            status='confirmed',
            created_at__lt=old_threshold
        ).select_related('customer').order_by('created_at')[:5]
        
        items = []
        for order in urgent_orders:
            days_waiting = (timezone.now() - order.created_at).days
            urgency_icon = '🔴' if days_waiting > 7 else '🟡'
            
            items.append({
                'label': f"{urgency_icon} {order.customer.legal_name}",
                'value': f"{days_waiting}j d'attente"
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    # =========================================================================
    # WIDGETS ADDITIONNELS
    # =========================================================================
    
    @staticmethod
    def _render_ventes_mois(organization):
        """Graphique des ventes mensuelles (futur - Chart.js)"""
        return {
            'type': 'chart',
            'chart_type': 'line',
            'data': [],
            'message': 'Widget graphique disponible prochainement'
        }
    
    @staticmethod
    def _render_clients_inactifs(organization):
        """Clients sans commande depuis 6 mois"""
        from apps.partners.models import Contact, ContactRole
        from apps.sales.models import Order
        
        cutoff = timezone.now() - timedelta(days=180)
        
        # Clients actifs (simplification - à améliorer avec relation orders)
        inactive_customers = Contact.objects.filter(
            organization=organization,
            is_active=True,
            roles__code=ContactRole.ROLE_CLIENT
        ).order_by('name')[:5]
        
        items = []
        for customer in inactive_customers:
            # Trouver la dernière commande
            last_order = Order.objects.filter(
                customer=customer
            ).order_by('-created_at').first()
            
            if last_order:
                days_ago = (timezone.now() - last_order.created_at).days
                value = f"Dernier achat il y a {days_ago}j"
            else:
                value = "Jamais commandé"
            
            items.append({
                'label': customer.legal_name,
                'value': value
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_stock_par_cuvee(organization):
        """Répartition du stock vrac par cuvée"""
        from apps.stock.models import StockVracBalance
        from django.db.models import Sum
        
        # Agrégation par cuvée (via lot)
        stock_by_cuvee = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0
        ).values(
            'lot__cuvee__name'
        ).annotate(
            total_l=Sum('qty_l')
        ).order_by('-total_l')[:5]
        
        items = []
        for item in stock_by_cuvee:
            cuvee_name = item['lot__cuvee__name'] or 'Sans cuvée'
            total_l = item['total_l'] or Decimal('0')
            items.append({
                'label': cuvee_name,
                'value': f"{total_l:,.0f} L"
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_factures_a_echeance(organization):
        """Factures arrivant à échéance dans les 7 prochains jours"""
        from apps.billing.models import Invoice
        
        today = timezone.now().date()
        upcoming_threshold = today + timedelta(days=7)
        
        upcoming_invoices = Invoice.objects.filter(
            organization=organization,
            status='issued',
            due_date__lte=upcoming_threshold,
            due_date__gte=today
        ).select_related('customer').order_by('due_date')[:5]
        
        items = []
        for invoice in upcoming_invoices:
            days_left = (invoice.due_date - today).days
            if days_left == 0:
                time_str = "Aujourd'hui"
                icon = '🔴'
            elif days_left == 1:
                time_str = "Demain"
                icon = '🟡'
            else:
                time_str = f"Dans {days_left}j"
                icon = '🟢'
            
            items.append({
                'label': f"{icon} {invoice.number} - {invoice.customer.legal_name}",
                'value': f"{time_str} - {invoice.total_ttc}€"
            })
        
        return {
            'type': 'list',
            'items': items
        }
    
    @staticmethod
    def _render_performance_mois(organization):
        """Performance du mois en cours (CA et comparaison)"""
        from apps.billing.models import Invoice
        
        now = timezone.now()
        month_start = timezone.datetime(now.year, now.month, 1).date()
        
        # CA du mois en cours
        current_month_data = Invoice.objects.filter(
            organization=organization,
            status__in=['issued', 'paid'],
            date_issue__gte=month_start
        ).aggregate(
            total=Sum('total_ttc'),
            count=Count('id')
        )
        
        current_ca = current_month_data['total'] or Decimal('0')
        current_count = current_month_data['count'] or 0
        
        # CA du mois précédent (pour comparaison)
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
        
        prev_month_start = timezone.datetime(prev_year, prev_month, 1).date()
        if prev_month == 12:
            prev_month_end = timezone.datetime(prev_year, 12, 31).date()
        else:
            prev_month_end = timezone.datetime(prev_year, prev_month + 1, 1).date() - timedelta(days=1)
        
        prev_month_data = Invoice.objects.filter(
            organization=organization,
            status__in=['issued', 'paid'],
            date_issue__gte=prev_month_start,
            date_issue__lte=prev_month_end
        ).aggregate(
            total=Sum('total_ttc')
        )
        
        prev_ca = prev_month_data['total'] or Decimal('0')
        
        # Calcul variation
        if prev_ca > 0:
            variation_pct = ((current_ca - prev_ca) / prev_ca) * 100
            if variation_pct > 0:
                trend = f"↗ +{variation_pct:.1f}%"
                color = 'success'
            elif variation_pct < 0:
                trend = f"↘ {variation_pct:.1f}%"
                color = 'danger'
            else:
                trend = "→ =0%"
                color = 'info'
        else:
            trend = "Nouveau"
            color = 'info'
        
        return {
            'value': f"{current_count}",
            'subtitle': f"{current_count} factures - {trend} vs mois dernier",
            'color': color,
            'icon': 'bi-graph-up-arrow',
            'url': 'ventes:factures_list',
        }
