"""
=====================================================================
SERVICE TIMELAPSE PRODUCTION - AGRÉGATION ÉVÉNEMENTS UNIFIÉE
=====================================================================
Centralise l'agrégation des événements de production pour la timelapse.
Option B (MVP rapide) : agrégation de querysets existants sans table dédiée.
=====================================================================
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Literal
from django.db.models import Q
from django.utils import timezone


@dataclass
class TimelapseItem:
    """Item normalisé pour la timelapse."""
    date: datetime
    type: str  # operation, analyse, sanitaire, alerte, system, mouvement
    title: str
    url: Optional[str] = None
    meta: Optional[str] = None
    icon: str = 'circle-fill'
    badge_class: str = 'bg-secondary'
    
    def to_dict(self):
        return {
            'date': self.date,
            'type': self.type,
            'title': self.title,
            'url': self.url,
            'meta': self.meta,
            'icon': self.icon,
            'badge_class': self.badge_class,
        }


# Mapping type -> (icon, badge_class)
TYPE_STYLES = {
    'operation': ('gear-fill', 'bg-primary'),
    'analyse': ('droplet-fill', 'bg-info'),
    'sanitaire': ('shield-check', 'bg-success'),
    'alerte': ('bell-fill', 'bg-warning'),
    'vendange': ('basket-fill', 'bg-orange'),
    'mouvement': ('arrow-left-right', 'bg-secondary'),
    'encuvage': ('box-arrow-in-down', 'bg-purple'),
    'soutirage': ('arrow-down-up', 'bg-indigo'),
    'assemblage': ('layers-fill', 'bg-dark'),
    'mise': ('upc-scan', 'bg-teal'),
    'system': ('info-circle-fill', 'bg-light text-dark'),
}


class TimelapseService:
    """Service d'agrégation des événements pour la timelapse Production."""
    
    def __init__(self, organization):
        self.organization = organization
    
    def get_events_for_context(
        self,
        context_type: Literal['parcelle', 'lot', 'cuve', 'production_home', 'vendange', 'analyse'],
        context_id: Optional[int] = None,
        limit: int = 30
    ) -> List[TimelapseItem]:
        """
        Récupère les événements pour un contexte donné.
        
        Args:
            context_type: Type de contexte (parcelle, lot, cuve, production_home, etc.)
            context_id: ID de l'objet (optionnel pour production_home)
            limit: Nombre max d'événements à retourner
            
        Returns:
            Liste de TimelapseItem triée par date décroissante
        """
        events = []
        
        if context_type == 'production_home':
            events = self._get_all_recent_events(limit)
        elif context_type == 'parcelle' and context_id:
            events = self._get_parcelle_events(context_id, limit)
        elif context_type == 'lot' and context_id:
            events = self._get_lot_events(context_id, limit)
        elif context_type == 'cuve' and context_id:
            events = self._get_cuve_events(context_id, limit)
        elif context_type == 'vendange' and context_id:
            events = self._get_vendange_events(context_id, limit)
        else:
            events = self._get_all_recent_events(limit)
        
        # Tri par date décroissante
        events.sort(key=lambda x: x.date, reverse=True)
        return events[:limit]
    
    def _get_all_recent_events(self, limit: int) -> List[TimelapseItem]:
        """Récupère tous les événements récents (vue d'ensemble)."""
        events = []
        
        # Opérations de cave
        events.extend(self._fetch_operations(limit=limit))
        
        # Analyses
        events.extend(self._fetch_analyses(limit=limit))
        
        # Alertes
        events.extend(self._fetch_alerts(limit=limit))
        
        # Vendanges
        events.extend(self._fetch_vendanges(limit=limit))
        
        # Mouvements de stock / Soutirages
        events.extend(self._fetch_soutirages(limit=limit))
        
        return events
    
    def _get_parcelle_events(self, parcelle_id: int, limit: int) -> List[TimelapseItem]:
        """Événements liés à une parcelle."""
        events = []
        
        # Vendanges de cette parcelle
        events.extend(self._fetch_vendanges(parcelle_id=parcelle_id, limit=limit))
        
        # Journal cultural (interventions sur parcelle)
        events.extend(self._fetch_journal_cultural(parcelle_id=parcelle_id, limit=limit))
        
        # Alertes liées
        events.extend(self._fetch_alerts(scope_type='parcelle', scope_id=parcelle_id, limit=limit))
        
        return events
    
    def _get_lot_events(self, lot_id: int, limit: int) -> List[TimelapseItem]:
        """Événements liés à un lot technique."""
        events = []
        
        # Opérations sur ce lot
        events.extend(self._fetch_operations(lot_id=lot_id, limit=limit))
        
        # Analyses sur ce lot
        events.extend(self._fetch_analyses(lot_id=lot_id, limit=limit))
        
        # Mouvements (soutirages, transferts)
        events.extend(self._fetch_soutirages(lot_id=lot_id, limit=limit))
        
        # Alertes liées
        events.extend(self._fetch_alerts(scope_type='lot', scope_id=lot_id, limit=limit))
        
        return events
    
    def _get_cuve_events(self, cuve_id: int, limit: int) -> List[TimelapseItem]:
        """Événements liés à un contenant (cuve/barrique)."""
        events = []
        
        # Opérations sur cette cuve
        events.extend(self._fetch_operations(contenant_id=cuve_id, limit=limit))
        
        # Mouvements impliquant cette cuve
        events.extend(self._fetch_soutirages(contenant_id=cuve_id, limit=limit))
        
        # Alertes liées
        events.extend(self._fetch_alerts(scope_type='cuve', scope_id=cuve_id, limit=limit))
        
        return events
    
    def _get_vendange_events(self, vendange_id: int, limit: int) -> List[TimelapseItem]:
        """Événements liés à une vendange."""
        events = []
        
        # La vendange elle-même + encuvages liés
        events.extend(self._fetch_vendanges(vendange_id=vendange_id, limit=limit))
        
        return events
    
    # ===== FETCH METHODS =====
    
    def _fetch_operations(self, lot_id=None, contenant_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les opérations de cave."""
        try:
            from apps.production.models import OperationCave
            
            qs = OperationCave.objects.filter(organization=self.organization)
            
            if lot_id:
                qs = qs.filter(lot_technique_id=lot_id)
            if contenant_id:
                qs = qs.filter(contenant_id=contenant_id)
            
            qs = qs.select_related('lot_technique', 'contenant').order_by('-date_operation')[:limit]
            
            items = []
            for op in qs:
                style = TYPE_STYLES.get('operation', ('gear-fill', 'bg-primary'))
                items.append(TimelapseItem(
                    date=op.date_operation if hasattr(op, 'date_operation') else op.created_at,
                    type='operation',
                    title=f"{op.get_type_operation_display() if hasattr(op, 'get_type_operation_display') else op.type_operation}",
                    url=f"/production/operations/{op.pk}/",
                    meta=f"Lot: {op.lot_technique.nom if op.lot_technique else 'N/A'}",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []
    
    def _fetch_analyses(self, lot_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les analyses œnologiques."""
        try:
            from apps.production.models_analyses import AnalyseOenologique
            
            qs = AnalyseOenologique.objects.filter(organization=self.organization)
            
            if lot_id:
                qs = qs.filter(lot_technique_id=lot_id)
            
            qs = qs.select_related('lot_technique').order_by('-date_prelevement')[:limit]
            
            items = []
            for an in qs:
                style = TYPE_STYLES.get('analyse', ('droplet-fill', 'bg-info'))
                items.append(TimelapseItem(
                    date=an.date_prelevement,
                    type='analyse',
                    title=f"Analyse {an.get_type_analyse_display() if hasattr(an, 'get_type_analyse_display') else 'œno'}",
                    url=f"/production/lots-elevage/analyses/{an.pk}/",
                    meta=f"Lot: {an.lot_technique.nom if an.lot_technique else 'N/A'}",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []
    
    def _fetch_alerts(self, scope_type=None, scope_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les alertes production."""
        try:
            from apps.production.models_alerts import ProductionAlert
            
            qs = ProductionAlert.objects.filter(organization=self.organization)
            
            if scope_type and scope_id:
                qs = qs.filter(scope_type=scope_type, scope_id=scope_id)
            
            qs = qs.order_by('-due_date')[:limit]
            
            items = []
            for alert in qs:
                style = TYPE_STYLES.get('alerte', ('bell-fill', 'bg-warning'))
                items.append(TimelapseItem(
                    date=alert.due_date or alert.created_at,
                    type='alerte',
                    title=alert.title,
                    url=f"/production/alertes/{alert.pk}/modifier/",
                    meta=f"Priorité: {alert.get_priority_display() if hasattr(alert, 'get_priority_display') else alert.priority}",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []
    
    def _fetch_vendanges(self, parcelle_id=None, vendange_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les vendanges."""
        try:
            from apps.production.models import Vendange
            
            qs = Vendange.objects.filter(organization=self.organization)
            
            if parcelle_id:
                qs = qs.filter(parcelle_id=parcelle_id)
            if vendange_id:
                qs = qs.filter(pk=vendange_id)
            
            qs = qs.select_related('parcelle').order_by('-date_vendange')[:limit]
            
            items = []
            for v in qs:
                style = TYPE_STYLES.get('vendange', ('basket-fill', 'bg-warning'))
                items.append(TimelapseItem(
                    date=timezone.make_aware(datetime.combine(v.date_vendange, datetime.min.time())) if v.date_vendange else v.created_at,
                    type='vendange',
                    title=f"Vendange {v.parcelle.nom if v.parcelle else ''}",
                    url=f"/production/vendanges/{v.pk}/",
                    meta=f"{v.volume_recolte or 0} L",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []
    
    def _fetch_soutirages(self, lot_id=None, contenant_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les soutirages/transferts."""
        try:
            from apps.production.models import Soutirage
            
            qs = Soutirage.objects.filter(organization=self.organization)
            
            if lot_id:
                qs = qs.filter(Q(lot_source_id=lot_id) | Q(lot_destination_id=lot_id))
            if contenant_id:
                qs = qs.filter(Q(contenant_source_id=contenant_id) | Q(contenant_destination_id=contenant_id))
            
            qs = qs.order_by('-date_soutirage')[:limit]
            
            items = []
            for s in qs:
                style = TYPE_STYLES.get('soutirage', ('arrow-down-up', 'bg-secondary'))
                items.append(TimelapseItem(
                    date=s.date_soutirage if hasattr(s, 'date_soutirage') else s.created_at,
                    type='soutirage',
                    title=f"Soutirage {s.volume or 0}L",
                    url=f"/production/soutirages/",
                    meta=f"De → Vers",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []
    
    def _fetch_journal_cultural(self, parcelle_id=None, limit=20) -> List[TimelapseItem]:
        """Récupère les entrées du journal cultural."""
        try:
            from apps.production.models import JournalEntry
            
            qs = JournalEntry.objects.filter(organization=self.organization)
            
            if parcelle_id:
                qs = qs.filter(parcelle_id=parcelle_id)
            
            qs = qs.order_by('-date_intervention')[:limit]
            
            items = []
            for entry in qs:
                style = TYPE_STYLES.get('sanitaire', ('shield-check', 'bg-success'))
                items.append(TimelapseItem(
                    date=entry.date_intervention if hasattr(entry, 'date_intervention') else entry.created_at,
                    type='sanitaire',
                    title=entry.type_intervention if hasattr(entry, 'type_intervention') else 'Intervention',
                    url=f"/production/journal-cultural/",
                    meta=f"Parcelle: {entry.parcelle.nom if entry.parcelle else 'N/A'}",
                    icon=style[0],
                    badge_class=style[1],
                ))
            return items
        except Exception:
            return []


def get_timelapse_for_context(
    organization,
    context_type: str,
    context_id: Optional[int] = None,
    limit: int = 30
) -> List[dict]:
    """
    Fonction utilitaire pour récupérer la timelapse.
    
    Usage:
        events = get_timelapse_for_context(request.current_org, 'production_home')
        events = get_timelapse_for_context(request.current_org, 'lot', lot.pk)
    """
    service = TimelapseService(organization)
    items = service.get_events_for_context(context_type, context_id, limit)
    return [item.to_dict() for item in items]
