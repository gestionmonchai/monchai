"""
Services pour la gestion des stocks - Roadmap 32
Logique métier pour transferts, balances et mouvements
"""

from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from .models import StockVracBalance, StockVracMove, StockSKUBalance, StockSKUMove


class StockService:
    """Service pour la gestion des stocks et transferts"""
    
    @staticmethod
    def get_lot_balance(organization, lot, warehouse):
        """
        Récupère le solde d'un lot dans un entrepôt
        """
        try:
            balance = StockVracBalance.objects.get(
                organization=organization,
                lot=lot,
                warehouse=warehouse
            )
            return balance.qty_l
        except StockVracBalance.DoesNotExist:
            return Decimal('0.00')
    
    @staticmethod
    def get_lot_balances_by_warehouse(organization, lot):
        """
        Récupère tous les soldes d'un lot par entrepôt
        """
        balances = StockVracBalance.objects.filter(
            organization=organization,
            lot=lot,
            qty_l__gt=0
        ).select_related('warehouse')
        
        return {
            balance.warehouse: balance.qty_l 
            for balance in balances
        }
    
    @staticmethod
    def update_balance_after_move(move):
        """
        Met à jour les balances après un mouvement
        """
        with transaction.atomic():
            # Mouvement de sortie (src_warehouse)
            if move.src_warehouse:
                balance, created = StockVracBalance.objects.get_or_create(
                    organization=move.organization,
                    lot=move.lot,
                    warehouse=move.src_warehouse,
                    defaults={'qty_l': Decimal('0.00')}
                )
                balance.qty_l -= move.qty_l
                if balance.qty_l < 0:
                    raise ValidationError(f"Solde négatif interdit: {balance.qty_l}L")
                balance.save()
            
            # Mouvement d'entrée (dst_warehouse)
            if move.dst_warehouse:
                balance, created = StockVracBalance.objects.get_or_create(
                    organization=move.organization,
                    lot=move.lot,
                    warehouse=move.dst_warehouse,
                    defaults={'qty_l': Decimal('0.00')}
                )
                balance.qty_l += move.qty_l
                balance.save()
    
    @staticmethod
    def get_warehouse_stock_summary(organization, warehouse):
        """
        Résumé des stocks d'un entrepôt
        """
        balances = StockVracBalance.objects.filter(
            organization=organization,
            warehouse=warehouse,
            qty_l__gt=0
        ).select_related('lot', 'lot__cuvee').order_by('-qty_l')
        
        total_volume = sum(balance.qty_l for balance in balances)
        
        return {
            'warehouse': warehouse,
            'total_volume_l': total_volume,
            'lot_count': balances.count(),
            'balances': balances
        }
    
    @staticmethod
    def get_organization_stock_summary(organization):
        """
        Résumé global des stocks d'une organisation
        """
        from django.db.models import Sum
        from apps.viticulture.models import Warehouse
        
        # Stocks par entrepôt
        warehouses = Warehouse.objects.filter(
            organization=organization,
            is_active=True
        )
        
        warehouse_summaries = []
        total_volume = Decimal('0.00')
        
        for warehouse in warehouses:
            summary = StockService.get_warehouse_stock_summary(organization, warehouse)
            warehouse_summaries.append(summary)
            total_volume += summary['total_volume_l']
        
        # Mouvements récents
        recent_moves = StockVracMove.objects.filter(
            organization=organization
        ).select_related(
            'lot', 'src_warehouse', 'dst_warehouse', 'user'
        ).order_by('-created_at')[:20]
        
        return {
            'organization': organization,
            'total_volume_l': total_volume,
            'warehouse_summaries': warehouse_summaries,
            'recent_moves': recent_moves
        }
    
    @staticmethod
    def validate_transfer_request(organization, lot, from_warehouse, to_warehouse, volume_l):
        """
        Valide une demande de transfert avant exécution
        """
        errors = []
        
        # Vérifications de base
        if from_warehouse == to_warehouse:
            errors.append("Les entrepôts source et destination doivent être différents")
        
        if volume_l <= 0:
            errors.append("Le volume doit être positif")
        
        # Vérifier que le lot appartient à l'organisation
        if lot.organization != organization:
            errors.append("Le lot n'appartient pas à cette organisation")
        
        # Vérifier que les entrepôts appartiennent à l'organisation
        if from_warehouse.organization != organization:
            errors.append("L'entrepôt source n'appartient pas à cette organisation")
        
        if to_warehouse.organization != organization:
            errors.append("L'entrepôt destination n'appartient pas à cette organisation")
        
        # Vérifier le solde disponible
        available_balance = StockService.get_lot_balance(organization, lot, from_warehouse)
        if available_balance < volume_l:
            errors.append(f"Solde insuffisant: {available_balance}L disponible, {volume_l}L demandé")
        
        return errors
    
    @staticmethod
    def get_transfer_history(organization, limit=50, lot=None, warehouse=None):
        """
        Historique des transferts avec filtres
        """
        from .models import StockTransfer
        
        transfers = StockTransfer.objects.filter(
            organization=organization
        ).select_related(
            'lot', 'from_warehouse', 'to_warehouse', 'created_by'
        )
        
        if lot:
            transfers = transfers.filter(lot=lot)
        
        if warehouse:
            transfers = transfers.filter(
                models.Q(from_warehouse=warehouse) | models.Q(to_warehouse=warehouse)
            )
        
        return transfers.order_by('-created_at')[:limit]
    
    @staticmethod
    def get_inventory_by_lot(organization, filters=None, sort_by=None, limit=50):
        """
        Récupère l'inventaire par lot avec filtres et tri - Roadmap 33
        
        Args:
            organization: Organisation
            filters: Dict avec cuvee_id, warehouse_id, vintage_id, status, volume_min, volume_max, q
            sort_by: 'volume_desc', 'updated_desc', 'lot_code_asc'
            limit: Nombre max de résultats
        
        Returns:
            QuerySet de StockVracBalance avec annotations
        """
        from django.db.models import Q, Max, Case, When, Value, CharField
        
        queryset = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0  # Seulement les lots avec stock
        ).select_related(
            'lot', 'lot__cuvee', 'lot__cuvee__vintage', 
            'lot__cuvee__appellation', 'warehouse'
        ).annotate(
            # Dernier mouvement
            last_move_date=Max('lot__stockvracmove__created_at'),
            # Statut du lot
            lot_status=Case(
                When(lot__status='en_cours', then=Value('En cours')),
                When(lot__status='elevage', then=Value('Élevage')),
                When(lot__status='stabilise', then=Value('Stabilisé')),
                When(lot__status='embouteille', then=Value('Embouteillé')),
                When(lot__status='archive', then=Value('Archivé')),
                default=Value('Inconnu'),
                output_field=CharField()
            )
        )
        
        # Application des filtres
        if filters:
            if filters.get('cuvee_id'):
                queryset = queryset.filter(lot__cuvee_id=filters['cuvee_id'])
            
            if filters.get('warehouse_id'):
                queryset = queryset.filter(warehouse_id=filters['warehouse_id'])
            
            if filters.get('vintage_id'):
                queryset = queryset.filter(lot__cuvee__vintage_id=filters['vintage_id'])
            
            if filters.get('status'):
                queryset = queryset.filter(lot__status=filters['status'])
            
            if filters.get('volume_min'):
                queryset = queryset.filter(qty_l__gte=filters['volume_min'])
            
            if filters.get('volume_max'):
                queryset = queryset.filter(qty_l__lte=filters['volume_max'])
            
            # Recherche textuelle
            if filters.get('q'):
                q = filters['q'].strip()
                queryset = queryset.filter(
                    Q(lot__code__icontains=q) |
                    Q(lot__cuvee__name__icontains=q)
                )
        
        # Application du tri
        if sort_by == 'volume_desc':
            queryset = queryset.order_by('-qty_l', 'lot__code')
        elif sort_by == 'updated_desc':
            queryset = queryset.order_by('-last_move_date', '-qty_l')
        elif sort_by == 'lot_code_asc':
            queryset = queryset.order_by('lot__code')
        else:
            # Tri par défaut
            queryset = queryset.order_by('-qty_l', 'lot__code')
        
        return queryset[:limit]
    
    @staticmethod
    def get_inventory_by_warehouse(organization, filters=None):
        """
        Récupère l'inventaire agrégé par entrepôt - Roadmap 33
        
        Args:
            organization: Organisation
            filters: Dict avec warehouse_id, cuvee_id, etc.
        
        Returns:
            Liste de dict avec warehouse, total_volume_l, lot_count, lots_detail
        """
        from django.db.models import Sum, Count
        
        # Requête de base
        base_queryset = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0
        ).select_related('warehouse', 'lot', 'lot__cuvee')
        
        # Application des filtres
        if filters:
            if filters.get('cuvee_id'):
                base_queryset = base_queryset.filter(lot__cuvee_id=filters['cuvee_id'])
            
            if filters.get('warehouse_id'):
                base_queryset = base_queryset.filter(warehouse_id=filters['warehouse_id'])
        
        # Agrégation par entrepôt
        warehouse_aggregates = base_queryset.values(
            'warehouse__id', 'warehouse__name'
        ).annotate(
            total_volume_l=Sum('qty_l'),
            lot_count=Count('lot', distinct=True)
        ).order_by('-total_volume_l')
        
        result = []
        for agg in warehouse_aggregates:
            warehouse_id = agg['warehouse__id']
            
            # Détail des lots pour cet entrepôt
            lots_detail = base_queryset.filter(
                warehouse_id=warehouse_id
            ).order_by('-qty_l')[:10]  # Top 10 lots
            
            result.append({
                'warehouse': {
                    'id': warehouse_id,
                    'name': agg['warehouse__name']
                },
                'total_volume_l': agg['total_volume_l'],
                'lot_count': agg['lot_count'],
                'lots_detail': lots_detail
            })
        
        return result
    
    @staticmethod
    def get_inventory_for_counting(organization, warehouse_id):
        """
        Récupère les lots d'un entrepôt pour comptage physique - Roadmap 33
        
        Args:
            organization: Organisation
            warehouse_id: ID de l'entrepôt à inventorier
        
        Returns:
            QuerySet de StockVracBalance avec infos pour comptage
        """
        from apps.viticulture.models import Warehouse
        from django.core.exceptions import ValidationError
        
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, organization=organization)
        except Warehouse.DoesNotExist:
            raise ValidationError("Entrepôt non trouvé")
        
        return StockVracBalance.objects.filter(
            organization=organization,
            warehouse=warehouse,
            qty_l__gt=0
        ).select_related(
            'lot', 'lot__cuvee', 'lot__cuvee__vintage'
        ).order_by('lot__code')
    
    @staticmethod
    def calculate_inventory_adjustments(organization, warehouse_id, counted_data):
        """
        Calcule les ajustements d'inventaire nécessaires - Roadmap 33
        
        Args:
            organization: Organisation
            warehouse_id: ID de l'entrepôt
            counted_data: Dict {lot_id: counted_volume_l}
        
        Returns:
            Liste de dict avec lot, current_balance, counted_volume, adjustment
        """
        from decimal import Decimal
        
        adjustments = []
        
        # Récupérer les balances actuelles
        balances = StockVracBalance.objects.filter(
            organization=organization,
            warehouse_id=warehouse_id,
            lot_id__in=counted_data.keys()
        ).select_related('lot', 'lot__cuvee', 'warehouse')
        
        for balance in balances:
            lot_id = str(balance.lot.id)
            current_volume = balance.qty_l
            counted_volume = Decimal(str(counted_data.get(lot_id, 0)))
            adjustment = counted_volume - current_volume
            
            if abs(adjustment) >= Decimal('0.01'):  # Seuil minimal d'ajustement
                adjustments.append({
                    'lot': balance.lot,
                    'warehouse': balance.warehouse,
                    'current_balance': current_volume,
                    'counted_volume': counted_volume,
                    'adjustment': adjustment,
                    'adjustment_type': 'increase' if adjustment > 0 else 'decrease'
                })
        
        return adjustments
    
    @staticmethod
    def apply_inventory_adjustments(organization, adjustments, user, session_notes=""):
        """
        Applique les ajustements d'inventaire via mouvements - Roadmap 33
        
        Args:
            organization: Organisation
            adjustments: Liste des ajustements calculés
            user: Utilisateur effectuant l'inventaire
            session_notes: Notes de la session d'inventaire
        
        Returns:
            Dict avec success count et erreurs
        """
        from django.db import transaction
        from .models import StockVracMove
        
        results = {
            'success_count': 0,
            'errors': [],
            'moves_created': []
        }
        
        for adjustment in adjustments:
            try:
                with transaction.atomic():
                    # Créer le mouvement d'ajustement
                    move = StockVracMove.objects.create(
                        organization=organization,
                        lot=adjustment['lot'],
                        move_type='ajustement',
                        qty_l=abs(adjustment['adjustment']),
                        src_warehouse=adjustment['warehouse'] if adjustment['adjustment'] < 0 else None,
                        dst_warehouse=adjustment['warehouse'] if adjustment['adjustment'] > 0 else None,
                        user=user,
                        notes=f"Inventaire physique - {session_notes}".strip(),
                        ref_type='inventory',
                        ref_id=None  # Pas de référence spécifique
                    )
                    
                    # Mettre à jour la balance
                    StockService.update_balance_after_move(
                        organization, adjustment['lot'], adjustment['warehouse'], 
                        adjustment['adjustment']
                    )
                    
                    results['success_count'] += 1
                    results['moves_created'].append(move)
                    
            except Exception as e:
                results['errors'].append({
                    'lot_code': adjustment['lot'].code,
                    'error': str(e)
                })
        
        return results


class StockAlertService:
    """Service pour la gestion des alertes de stock - Roadmap 34"""
    
    @staticmethod
    def get_applicable_threshold(organization, lot, warehouse):
        """
        Détermine le seuil applicable selon la priorité : lot > cuvée > entrepôt > global
        Retourne (threshold_value, source_scope) ou (None, None) si aucun seuil
        """
        from .models import StockThreshold
        
        # Priorité 1: Seuil spécifique au lot
        threshold = StockThreshold.objects.filter(
            organization=organization,
            scope='lot',
            ref_id=lot.id,
            is_active=True
        ).first()
        
        if threshold:
            return threshold.threshold_l, 'lot'
        
        # Priorité 2: Seuil spécifique à la cuvée
        threshold = StockThreshold.objects.filter(
            organization=organization,
            scope='cuvee',
            ref_id=lot.cuvee.id,
            is_active=True
        ).first()
        
        if threshold:
            return threshold.threshold_l, 'cuvee'
        
        # Priorité 3: Seuil spécifique à l'entrepôt
        threshold = StockThreshold.objects.filter(
            organization=organization,
            scope='warehouse',
            ref_id=warehouse.id,
            is_active=True
        ).first()
        
        if threshold:
            return threshold.threshold_l, 'warehouse'
        
        # Priorité 4: Seuil global
        threshold = StockThreshold.objects.filter(
            organization=organization,
            scope='global',
            is_active=True
        ).first()
        
        if threshold:
            return threshold.threshold_l, 'global'
        
        return None, None
    
    @staticmethod
    def compute_stock_alerts(organization):
        """
        Job planifié : calcule et met à jour les alertes de stock pour une organisation
        Retourne le nombre d'alertes créées et résolues
        """
        from .models import StockAlert
        from django.utils import timezone
        
        created_count = 0
        resolved_count = 0
        
        # Récupérer tous les soldes de stock vrac pour l'organisation
        balances = StockVracBalance.objects.filter(
            organization=organization,
            qty_l__gt=0  # Seulement les soldes positifs
        ).select_related('lot', 'warehouse', 'lot__cuvee')
        
        for balance in balances:
            threshold_value, threshold_source = StockAlertService.get_applicable_threshold(
                organization, balance.lot, balance.warehouse
            )
            
            if threshold_value is None:
                # Pas de seuil configuré, on résout les alertes existantes
                existing_alerts = StockAlert.objects.filter(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                )
                
                for alert in existing_alerts:
                    alert.auto_resolve()
                    resolved_count += 1
                
                continue
            
            # Vérifier si le stock est en dessous du seuil
            if balance.qty_l < threshold_value:
                # Stock bas : créer ou mettre à jour l'alerte
                alert, created = StockAlert.objects.get_or_create(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True,
                    defaults={
                        'balance_l': balance.qty_l,
                        'threshold_l': threshold_value,
                        'threshold_source': threshold_source,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    # Mettre à jour les valeurs si l'alerte existe déjà
                    alert.balance_l = balance.qty_l
                    alert.threshold_l = threshold_value
                    alert.threshold_source = threshold_source
                    alert.save()
            
            else:
                # Stock suffisant : résoudre les alertes actives
                existing_alerts = StockAlert.objects.filter(
                    organization=organization,
                    lot=balance.lot,
                    warehouse=balance.warehouse,
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                )
                
                for alert in existing_alerts:
                    alert.auto_resolve()
                    resolved_count += 1
        
        return {
            'created_count': created_count,
            'resolved_count': resolved_count,
            'total_active': StockAlert.objects.filter(
                organization=organization,
                acknowledged_at__isnull=True,
                auto_resolved_at__isnull=True
            ).count()
        }
    
    @staticmethod
    def get_active_alerts_count(organization):
        """
        Retourne le nombre d'alertes actives pour le badge
        """
        from .models import StockAlert
        
        return StockAlert.objects.filter(
            organization=organization,
            acknowledged_at__isnull=True,
            auto_resolved_at__isnull=True
        ).count()
    
    @staticmethod
    def get_alerts_list(organization, filters=None, sort_by='criticality'):
        """
        Retourne la liste des alertes avec filtres et tri
        """
        from .models import StockAlert
        from django.db.models import Case, When, Value, FloatField
        
        queryset = StockAlert.objects.filter(
            organization=organization
        ).select_related('lot', 'warehouse', 'lot__cuvee', 'acknowledged_by')
        
        # Appliquer les filtres
        if filters:
            if filters.get('status') == 'active':
                queryset = queryset.filter(
                    acknowledged_at__isnull=True,
                    auto_resolved_at__isnull=True
                )
            elif filters.get('status') == 'acknowledged':
                queryset = queryset.filter(acknowledged_at__isnull=False)
            elif filters.get('status') == 'resolved':
                queryset = queryset.filter(auto_resolved_at__isnull=False)
            
            if filters.get('cuvee_id'):
                queryset = queryset.filter(lot__cuvee_id=filters['cuvee_id'])
            
            if filters.get('warehouse_id'):
                queryset = queryset.filter(warehouse_id=filters['warehouse_id'])
            
            if filters.get('criticality'):
                if filters['criticality'] == 'high':
                    # Criticité haute : ratio < 0.2 (moins de 20% du seuil)
                    queryset = queryset.extra(
                        where=["balance_l / threshold_l < 0.2"]
                    )
                elif filters['criticality'] == 'medium':
                    # Criticité moyenne : 0.2 <= ratio < 0.5
                    queryset = queryset.extra(
                        where=["balance_l / threshold_l >= 0.2 AND balance_l / threshold_l < 0.5"]
                    )
                elif filters['criticality'] == 'low':
                    # Criticité faible : ratio >= 0.5
                    queryset = queryset.extra(
                        where=["balance_l / threshold_l >= 0.5"]
                    )
        
        # Récupérer les résultats pour le tri
        alerts_list = list(queryset.order_by('-first_seen_at'))
        
        # Appliquer le tri
        if sort_by == 'criticality' or sort_by is None:
            # Tri par criticité (ratio balance/threshold croissant)
            alerts_list.sort(key=lambda alert: (alert.criticality_ratio, -alert.first_seen_at.timestamp()))
        elif sort_by == 'first_seen_desc':
            alerts_list.sort(key=lambda alert: alert.first_seen_at, reverse=True)
        elif sort_by == 'first_seen_asc':
            alerts_list.sort(key=lambda alert: alert.first_seen_at)
        elif sort_by == 'lot_code':
            alerts_list.sort(key=lambda alert: alert.lot.code)
        
        # Retourner une liste plutôt qu'un QuerySet
        return alerts_list
    
    @staticmethod
    def acknowledge_alert(alert_id, user, organization):
        """
        Acquitte une alerte
        """
        from .models import StockAlert
        
        try:
            alert = StockAlert.objects.get(
                id=alert_id,
                organization=organization,
                acknowledged_at__isnull=True
            )
            alert.acknowledge(user)
            return True, "Alerte acquittée avec succès"
        except StockAlert.DoesNotExist:
            return False, "Alerte non trouvée ou déjà acquittée"
    
    @staticmethod
    def acknowledge_multiple_alerts(alert_ids, user, organization):
        """
        Acquitte plusieurs alertes en une fois
        """
        from .models import StockAlert
        from django.utils import timezone
        
        count = StockAlert.objects.filter(
            id__in=alert_ids,
            organization=organization,
            acknowledged_at__isnull=True
        ).update(
            acknowledged_by=user,
            acknowledged_at=timezone.now()
        )
        
        return count
