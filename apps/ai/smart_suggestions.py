"""
=============================================================================
SMART SUGGESTIONS - Intelligence Proactive MonChai
=============================================================================
5 fonctionnalités intelligentes pour transformer l'ERP en assistant proactif :

1. Météo-Sensible (Vigne) - Alertes météo sur les actions parcelles
2. Calculateur de Destination (Chai) - Suggestions intelligentes de cuves
3. Détective d'Analyse (Labo) - Alertes déviations + actions suggérées
4. Timer Légal (DRM) - Rappels avec pré-brouillon auto-rempli
5. Mémoire des Intrants - Pré-remplissage basé sur l'historique
=============================================================================
"""

from __future__ import annotations
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import httpx

from django.db.models import Sum, Avg, Q
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES & DATACLASSES
# =============================================================================

class NudgeType(Enum):
    """Types de nudges (coups de coude visuels)"""
    INFO = "info"           # Bleu - Information
    SUGGESTION = "suggest"  # Vert - Suggestion logique
    WARNING = "warning"     # Orange - Attention
    ALERT = "alert"         # Rouge - Action urgente
    SPARKLE = "sparkle"     # Doré - Suggestion IA


@dataclass
class Nudge:
    """Un nudge = suggestion non intrusive affichée dans l'UI"""
    type: NudgeType
    icon: str
    title: str
    message: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Plus élevé = plus important
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'icon': self.icon,
            'title': self.title,
            'message': self.message,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'data': self.data,
            'priority': self.priority,
        }


@dataclass
class WeatherForecast:
    """Prévision météo simplifiée"""
    date: date
    temp_min: float
    temp_max: float
    precipitation_mm: float
    precipitation_prob: int  # %
    wind_speed_kmh: float
    description: str
    icon: str


@dataclass 
class CuveSuggestion:
    """Suggestion de cuve pour soutirage/assemblage"""
    contenant: Any  # Contenant model instance
    fit_score: int  # 0-100, 100 = perfect fit
    reason: str
    highlight: str  # "perfect", "good", "possible", "disabled"


# =============================================================================
# 1. MÉTÉO-SENSIBLE (Vigne)
# =============================================================================

class WeatherService:
    """
    Service météo pour suggestions intelligentes sur les parcelles.
    Utilise Open-Meteo (gratuit, pas de clé API requise).
    """
    
    CACHE_TTL = 3600  # 1 heure
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Seuils météo pour les alertes
    RAIN_THRESHOLD_MM = 5  # mm de pluie = risque lessivage
    WIND_THRESHOLD_KMH = 30  # km/h = risque traitement
    FROST_THRESHOLD_C = 2  # °C = risque gel
    
    @classmethod
    def get_forecast(cls, lat: float, lon: float, days: int = 3) -> List[WeatherForecast]:
        """Récupère les prévisions météo pour une localisation"""
        cache_key = f"weather_{lat:.3f}_{lon:.3f}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code",
                "timezone": "Europe/Paris",
                "forecast_days": days,
            }
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(cls.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            forecasts = []
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            
            for i, date_str in enumerate(dates):
                forecast = WeatherForecast(
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    temp_min=daily.get("temperature_2m_min", [0])[i] or 0,
                    temp_max=daily.get("temperature_2m_max", [0])[i] or 0,
                    precipitation_mm=daily.get("precipitation_sum", [0])[i] or 0,
                    precipitation_prob=daily.get("precipitation_probability_max", [0])[i] or 0,
                    wind_speed_kmh=daily.get("wind_speed_10m_max", [0])[i] or 0,
                    description=cls._weather_code_to_description(daily.get("weather_code", [0])[i]),
                    icon=cls._weather_code_to_icon(daily.get("weather_code", [0])[i]),
                )
                forecasts.append(forecast)
            
            cache.set(cache_key, forecasts, cls.CACHE_TTL)
            return forecasts
            
        except Exception as e:
            logger.warning(f"Erreur météo: {e}")
            return []
    
    @classmethod
    def get_parcelle_alerts(cls, parcelle) -> List[Nudge]:
        """
        Génère les alertes météo pour une parcelle.
        Retourne des nudges pour les actions à éviter ou suggérées.
        """
        nudges = []
        
        # Récupérer coordonnées de la parcelle
        lat = getattr(parcelle, 'latitude', None) or getattr(parcelle, 'centroid_y', None)
        lon = getattr(parcelle, 'longitude', None) or getattr(parcelle, 'centroid_x', None)
        
        if not lat or not lon:
            return nudges
        
        forecasts = cls.get_forecast(float(lat), float(lon), days=3)
        if not forecasts:
            return nudges
        
        # Analyser les 48h à venir
        today = date.today()
        rain_48h = sum(f.precipitation_mm for f in forecasts[:2])
        max_wind_48h = max((f.wind_speed_kmh for f in forecasts[:2]), default=0)
        min_temp_48h = min((f.temp_min for f in forecasts[:2]), default=10)
        
        # Alerte pluie = risque lessivage traitement
        if rain_48h >= cls.RAIN_THRESHOLD_MM:
            rain_day = next((f for f in forecasts if f.precipitation_mm >= cls.RAIN_THRESHOLD_MM), forecasts[0])
            nudges.append(Nudge(
                type=NudgeType.WARNING,
                icon="bi-cloud-rain",
                title="Risque de lessivage",
                message=f"Pluie prévue: {rain_48h:.0f}mm dans les 48h ({rain_day.description})",
                data={
                    "affected_action": "traitement_phyto",
                    "rain_mm": rain_48h,
                    "rain_date": rain_day.date.isoformat(),
                },
                priority=80,
            ))
            # Suggestion alternative
            nudges.append(Nudge(
                type=NudgeType.SUGGESTION,
                icon="bi-lightbulb",
                title="Suggestion",
                message="Privilégiez le travail du sol ou l'entretien du palissage",
                action_label="Saisir travail du sol",
                data={"suggested_actions": ["travail_sol", "palissage"]},
                priority=60,
            ))
        
        # Alerte vent = risque dérive traitement
        if max_wind_48h >= cls.WIND_THRESHOLD_KMH:
            nudges.append(Nudge(
                type=NudgeType.WARNING,
                icon="bi-wind",
                title="Vent fort prévu",
                message=f"Rafales jusqu'à {max_wind_48h:.0f} km/h - risque de dérive",
                data={
                    "affected_action": "traitement_phyto",
                    "wind_kmh": max_wind_48h,
                },
                priority=70,
            ))
        
        # Alerte gel
        if min_temp_48h <= cls.FROST_THRESHOLD_C:
            nudges.append(Nudge(
                type=NudgeType.ALERT,
                icon="bi-snow",
                title="Risque de gel",
                message=f"Température minimale prévue: {min_temp_48h:.1f}°C",
                data={
                    "min_temp": min_temp_48h,
                    "frost_risk": True,
                },
                priority=95,
            ))
        
        return nudges
    
    @staticmethod
    def _weather_code_to_description(code: int) -> str:
        """Convertit le code météo WMO en description"""
        codes = {
            0: "Ciel dégagé",
            1: "Principalement dégagé", 2: "Partiellement nuageux", 3: "Couvert",
            45: "Brouillard", 48: "Brouillard givrant",
            51: "Bruine légère", 53: "Bruine modérée", 55: "Bruine dense",
            61: "Pluie légère", 63: "Pluie modérée", 65: "Pluie forte",
            71: "Neige légère", 73: "Neige modérée", 75: "Neige forte",
            80: "Averses légères", 81: "Averses modérées", 82: "Averses violentes",
            95: "Orage", 96: "Orage avec grêle légère", 99: "Orage avec grêle forte",
        }
        return codes.get(code, "Variable")
    
    @staticmethod
    def _weather_code_to_icon(code: int) -> str:
        """Convertit le code météo WMO en icône Bootstrap"""
        if code == 0:
            return "bi-sun"
        elif code in (1, 2):
            return "bi-cloud-sun"
        elif code == 3:
            return "bi-clouds"
        elif code in (45, 48):
            return "bi-cloud-fog"
        elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
            return "bi-cloud-rain"
        elif code in (71, 73, 75):
            return "bi-snow"
        elif code in (95, 96, 99):
            return "bi-cloud-lightning-rain"
        return "bi-cloud"


# =============================================================================
# 2. CALCULATEUR DE DESTINATION (Chai)
# =============================================================================

class CuveCalculator:
    """
    Suggestions intelligentes de cuves pour soutirages et assemblages.
    Grise les cuves inadaptées, met en surbrillance les "perfect fit".
    """
    
    # Marge de tolérance pour "perfect fit" (±10%)
    PERFECT_FIT_MARGIN = 0.10
    
    @classmethod
    def get_destination_suggestions(
        cls,
        organization,
        volume_source_l: Decimal,
        exclude_ids: List[int] = None,
        operation_type: str = "soutirage"
    ) -> List[CuveSuggestion]:
        """
        Retourne les cuves triées par pertinence pour recevoir un volume donné.
        
        Args:
            organization: Organisation courante
            volume_source_l: Volume à transférer en litres
            exclude_ids: IDs de cuves sources à exclure
            operation_type: "soutirage" ou "assemblage"
        """
        from apps.production.models_containers import Contenant
        
        exclude_ids = exclude_ids or []
        volume = Decimal(str(volume_source_l))
        
        # Récupérer toutes les cuves de l'organisation
        cuves = Contenant.objects.filter(
            organization=organization,
            is_active=True,
        ).exclude(id__in=exclude_ids)
        
        suggestions = []
        
        for cuve in cuves:
            suggestion = cls._evaluate_cuve(cuve, volume, operation_type)
            suggestions.append(suggestion)
        
        # Trier par score décroissant (meilleur en premier)
        suggestions.sort(key=lambda x: (-x.fit_score, x.contenant.code))
        
        return suggestions
    
    @classmethod
    def _evaluate_cuve(cls, cuve, volume_l: Decimal, operation_type: str) -> CuveSuggestion:
        """Évalue une cuve et retourne une suggestion avec score"""
        
        free_capacity = cuve.free_capacity_l()
        total_capacity = cuve.capacite_utile_effective_l
        
        # Cas 1: Cuve hors service ou en maintenance
        if cuve.statut in ('hors_service', 'maintenance', 'nettoyage'):
            return CuveSuggestion(
                contenant=cuve,
                fit_score=0,
                reason=f"Cuve {cuve.get_statut_display().lower()}",
                highlight="disabled",
            )
        
        # Cas 2: Capacité insuffisante
        if free_capacity < volume_l:
            deficit = volume_l - free_capacity
            return CuveSuggestion(
                contenant=cuve,
                fit_score=5,
                reason=f"Capacité insuffisante (-{deficit:.0f}L)",
                highlight="disabled",
            )
        
        # Cas 3: Perfect fit (cuve vide, capacité proche du volume)
        if cuve.statut == 'disponible' and cuve.volume_occupe_l == 0:
            ratio = float(volume_l / total_capacity) if total_capacity else 0
            
            # Perfect fit: volume entre 90% et 100% de la capacité
            if 0.90 <= ratio <= 1.0:
                return CuveSuggestion(
                    contenant=cuve,
                    fit_score=100,
                    reason=f"✨ Perfect fit ({ratio*100:.0f}% de remplissage)",
                    highlight="perfect",
                )
            
            # Bon fit: volume entre 70% et 90%
            elif 0.70 <= ratio < 0.90:
                return CuveSuggestion(
                    contenant=cuve,
                    fit_score=80,
                    reason=f"Bon remplissage ({ratio*100:.0f}%)",
                    highlight="good",
                )
            
            # Cuve vide mais surdimensionnée
            elif ratio < 0.70:
                return CuveSuggestion(
                    contenant=cuve,
                    fit_score=50,
                    reason=f"Cuve surdimensionnée ({ratio*100:.0f}% utilisé)",
                    highlight="possible",
                )
        
        # Cas 4: Cuve partiellement occupée mais peut recevoir
        if cuve.statut == 'occupe':
            fill_after = float((cuve.volume_occupe_l + volume_l) / total_capacity) if total_capacity else 0
            
            if fill_after <= 0.95:
                return CuveSuggestion(
                    contenant=cuve,
                    fit_score=60,
                    reason=f"Ajout possible ({fill_after*100:.0f}% après)",
                    highlight="possible",
                )
            else:
                return CuveSuggestion(
                    contenant=cuve,
                    fit_score=40,
                    reason=f"Limite haute ({fill_after*100:.0f}% après)",
                    highlight="possible",
                )
        
        # Cas par défaut
        return CuveSuggestion(
            contenant=cuve,
            fit_score=30,
            reason="Disponible",
            highlight="possible",
        )
    
    @classmethod
    def get_multi_source_suggestions(
        cls,
        organization,
        source_volumes: List[Tuple[int, Decimal]],  # [(cuve_id, volume), ...]
    ) -> List[CuveSuggestion]:
        """
        Suggestions pour assemblage multi-sources.
        Calcule le volume total et suggère les cuves adaptées.
        """
        total_volume = sum(v for _, v in source_volumes)
        exclude_ids = [cuve_id for cuve_id, _ in source_volumes]
        
        return cls.get_destination_suggestions(
            organization,
            total_volume,
            exclude_ids=exclude_ids,
            operation_type="assemblage"
        )


# =============================================================================
# 3. DÉTECTIVE D'ANALYSE (Labo)
# =============================================================================

class AnalyseDetective:
    """
    Surveille les déviations dangereuses dans les analyses et suggère des actions.
    """
    
    # Seuils d'alerte par paramètre
    THRESHOLDS = {
        'acidite_volatile': {
            'warning': Decimal('0.50'),  # g/L H2SO4
            'alert': Decimal('0.65'),
            'action': "Filtration ou sulfitage",
            'action_url': "/production/operations/add/?type=filtration",
        },
        'so2_libre': {
            'warning_low': Decimal('15'),  # mg/L
            'alert_low': Decimal('10'),
            'action': "Sulfitage d'urgence",
            'action_url': "/production/operations/add/?type=sulfitage",
        },
        'ph': {
            'warning_high': Decimal('3.70'),
            'alert_high': Decimal('3.85'),
            'warning_low': Decimal('3.10'),
            'alert_low': Decimal('3.00'),
            'action_high': "Acidification recommandée",
            'action_low': "Désacidification recommandée",
        },
    }
    
    # Seuils de variation (déclenchent une alerte si dépassés)
    VARIATION_THRESHOLDS = {
        'acidite_volatile': Decimal('0.10'),  # +0.10 g/L en 1 semaine = alerte
        'so2_libre': Decimal('-10'),  # -10 mg/L en 1 semaine = alerte
    }
    
    @classmethod
    def analyze_lot(cls, lot) -> List[Nudge]:
        """
        Analyse les dernières analyses d'un lot et génère des nudges d'alerte.
        """
        nudges = []
        
        # Récupérer les 2 dernières analyses pour comparaison
        analyses = list(lot.analyses.order_by('-date')[:2])
        
        if not analyses:
            return nudges
        
        last_analyse = analyses[0]
        previous_analyse = analyses[1] if len(analyses) > 1 else None
        
        # Vérifier les seuils absolus
        nudges.extend(cls._check_absolute_thresholds(last_analyse))
        
        # Vérifier les variations
        if previous_analyse:
            nudges.extend(cls._check_variations(last_analyse, previous_analyse))
        
        return nudges
    
    @classmethod
    def _check_absolute_thresholds(cls, analyse) -> List[Nudge]:
        """Vérifie les seuils absolus"""
        nudges = []
        
        # Acidité volatile
        av = analyse.acidite_volatile
        if av:
            thresholds = cls.THRESHOLDS['acidite_volatile']
            if av >= thresholds['alert']:
                nudges.append(Nudge(
                    type=NudgeType.ALERT,
                    icon="bi-exclamation-triangle",
                    title="AV critique",
                    message=f"Acidité volatile: {av} g/L (seuil: {thresholds['alert']})",
                    action_url=thresholds['action_url'],
                    action_label=thresholds['action'],
                    data={'parameter': 'acidite_volatile', 'value': float(av)},
                    priority=95,
                ))
            elif av >= thresholds['warning']:
                nudges.append(Nudge(
                    type=NudgeType.WARNING,
                    icon="bi-exclamation-circle",
                    title="AV à surveiller",
                    message=f"Acidité volatile: {av} g/L (attention > {thresholds['warning']})",
                    action_url=thresholds['action_url'],
                    action_label="Planifier filtration",
                    data={'parameter': 'acidite_volatile', 'value': float(av)},
                    priority=70,
                ))
        
        # SO2 libre
        so2 = analyse.so2_libre
        if so2:
            thresholds = cls.THRESHOLDS['so2_libre']
            if so2 <= thresholds['alert_low']:
                nudges.append(Nudge(
                    type=NudgeType.ALERT,
                    icon="bi-shield-exclamation",
                    title="SO₂ critique",
                    message=f"SO₂ libre: {so2} mg/L (minimum: {thresholds['alert_low']})",
                    action_url=thresholds['action_url'],
                    action_label=thresholds['action'],
                    data={'parameter': 'so2_libre', 'value': float(so2)},
                    priority=90,
                ))
            elif so2 <= thresholds['warning_low']:
                nudges.append(Nudge(
                    type=NudgeType.WARNING,
                    icon="bi-shield",
                    title="SO₂ bas",
                    message=f"SO₂ libre: {so2} mg/L (surveiller < {thresholds['warning_low']})",
                    action_url=thresholds['action_url'],
                    action_label="Planifier sulfitage",
                    data={'parameter': 'so2_libre', 'value': float(so2)},
                    priority=65,
                ))
        
        # pH
        ph = analyse.ph
        if ph:
            thresholds = cls.THRESHOLDS['ph']
            if ph >= thresholds.get('alert_high', 99):
                nudges.append(Nudge(
                    type=NudgeType.ALERT,
                    icon="bi-droplet",
                    title="pH élevé",
                    message=f"pH: {ph} (seuil: {thresholds['alert_high']})",
                    action_label=thresholds.get('action_high', 'Corriger pH'),
                    data={'parameter': 'ph', 'value': float(ph)},
                    priority=80,
                ))
            elif ph <= thresholds.get('alert_low', 0):
                nudges.append(Nudge(
                    type=NudgeType.ALERT,
                    icon="bi-droplet",
                    title="pH bas",
                    message=f"pH: {ph} (seuil: {thresholds['alert_low']})",
                    action_label=thresholds.get('action_low', 'Corriger pH'),
                    data={'parameter': 'ph', 'value': float(ph)},
                    priority=80,
                ))
        
        return nudges
    
    @classmethod
    def _check_variations(cls, current, previous) -> List[Nudge]:
        """Vérifie les variations entre deux analyses"""
        nudges = []
        days_diff = (current.date - previous.date).days
        
        if days_diff <= 0:
            return nudges
        
        # Normaliser sur 7 jours
        factor = 7 / days_diff
        
        # Variation AV
        if current.acidite_volatile and previous.acidite_volatile:
            variation = (current.acidite_volatile - previous.acidite_volatile) * Decimal(str(factor))
            threshold = cls.VARIATION_THRESHOLDS['acidite_volatile']
            
            if variation >= threshold:
                nudges.append(Nudge(
                    type=NudgeType.WARNING,
                    icon="bi-graph-up-arrow",
                    title="AV en hausse rapide",
                    message=f"+{current.acidite_volatile - previous.acidite_volatile:.2f} g/L en {days_diff}j",
                    action_label="Planifier filtration",
                    data={
                        'parameter': 'acidite_volatile',
                        'variation': float(variation),
                        'days': days_diff,
                    },
                    priority=75,
                ))
        
        # Variation SO2
        if current.so2_libre and previous.so2_libre:
            variation = (current.so2_libre - previous.so2_libre) * Decimal(str(factor))
            threshold = cls.VARIATION_THRESHOLDS['so2_libre']
            
            if variation <= threshold:  # Threshold is negative
                nudges.append(Nudge(
                    type=NudgeType.WARNING,
                    icon="bi-graph-down-arrow",
                    title="SO₂ en baisse rapide",
                    message=f"{current.so2_libre - previous.so2_libre:.0f} mg/L en {days_diff}j",
                    action_label="Planifier sulfitage",
                    data={
                        'parameter': 'so2_libre',
                        'variation': float(variation),
                        'days': days_diff,
                    },
                    priority=70,
                ))
        
        return nudges


# =============================================================================
# 4. TIMER LÉGAL (DRM)
# =============================================================================

class DRMTimer:
    """
    Gestion des rappels légaux DRM avec pré-brouillon auto-rempli.
    """
    
    # Date limite DRM = 10 du mois suivant
    DRM_DAY_LIMIT = 10
    
    @classmethod
    def get_drm_status(cls, organization) -> Dict[str, Any]:
        """
        Retourne le statut DRM pour une organisation.
        Inclut le nombre de jours restants et le statut du brouillon.
        """
        today = date.today()
        
        # Période DRM = mois précédent
        if today.day <= cls.DRM_DAY_LIMIT:
            # On est encore dans la période de déclaration du mois précédent
            if today.month == 1:
                drm_month = 12
                drm_year = today.year - 1
            else:
                drm_month = today.month - 1
                drm_year = today.year
            deadline = date(today.year, today.month, cls.DRM_DAY_LIMIT)
            days_remaining = (deadline - today).days
        else:
            # Nouvelle période, DRM précédente échue
            drm_month = today.month
            drm_year = today.year
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year if today.month < 12 else today.year + 1
            deadline = date(next_year, next_month, cls.DRM_DAY_LIMIT)
            days_remaining = (deadline - today).days
        
        period = f"{drm_year}-{drm_month:02d}"
        
        return {
            'period': period,
            'period_display': f"{cls._month_name(drm_month)} {drm_year}",
            'deadline': deadline,
            'days_remaining': days_remaining,
            'is_urgent': days_remaining <= 3,
            'is_overdue': days_remaining < 0,
        }
    
    @classmethod
    def get_header_nudge(cls, organization) -> Optional[Nudge]:
        """
        Retourne un nudge pour le header si DRM proche.
        """
        status = cls.get_drm_status(organization)
        days = status['days_remaining']
        
        if status['is_overdue']:
            return Nudge(
                type=NudgeType.ALERT,
                icon="bi-exclamation-triangle-fill",
                title="DRM en retard",
                message=f"DRM {status['period_display']} à régulariser",
                action_url=f"/drm/brouillon/?period={status['period']}",
                action_label="Compléter maintenant",
                priority=100,
            )
        elif status['is_urgent']:
            return Nudge(
                type=NudgeType.WARNING,
                icon="bi-clock-history",
                title=f"J-{days} pour la DRM",
                message=f"DRM {status['period_display']} à envoyer avant le {status['deadline'].strftime('%d/%m')}",
                action_url=f"/drm/brouillon/?period={status['period']}",
                action_label="Voir le pré-brouillon",
                priority=85,
            )
        elif days <= 7:
            return Nudge(
                type=NudgeType.INFO,
                icon="bi-calendar-check",
                title=f"DRM dans {days}j",
                message=f"Pensez à vérifier votre pré-brouillon",
                action_url=f"/drm/brouillon/?period={status['period']}",
                action_label="Voir",
                priority=40,
            )
        
        return None
    
    @classmethod
    def generate_pre_brouillon(cls, organization, period: str) -> Dict[str, Any]:
        """
        Génère un pré-brouillon DRM basé sur les mouvements du mois.
        """
        from apps.stock.models import MouvementStock
        from apps.production.models import VendangeReception
        
        year, month = map(int, period.split('-'))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Collecter les données
        data = {
            'period': period,
            'period_display': f"{cls._month_name(month)} {year}",
            'generated_at': timezone.now().isoformat(),
            'entries': [],  # Entrées
            'exits': [],    # Sorties
            'totals': {
                'entrees_hl': Decimal('0'),
                'sorties_hl': Decimal('0'),
            },
            'completeness': 0,  # % de complétion estimé
        }
        
        try:
            # Entrées: vendanges du mois
            vendanges = VendangeReception.objects.filter(
                organization=organization,
                date__gte=start_date,
                date__lt=end_date,
            )
            
            for v in vendanges:
                vol_hl = (v.volume_mesure_l or Decimal('0')) / Decimal('100')
                data['entries'].append({
                    'type': 'vendange',
                    'date': v.date.isoformat(),
                    'description': f"Vendange {v.parcelle.nom}" if v.parcelle else "Vendange",
                    'volume_hl': float(vol_hl),
                    'code': v.code,
                })
                data['totals']['entrees_hl'] += vol_hl
            
            # Mouvements de stock
            mouvements = MouvementStock.objects.filter(
                organization=organization,
                date__gte=start_date,
                date__lt=end_date,
            )
            
            for m in mouvements:
                vol_hl = abs(m.quantite_l or Decimal('0')) / Decimal('100')
                entry = {
                    'type': m.type_mouvement,
                    'date': m.date.isoformat(),
                    'description': str(m),
                    'volume_hl': float(vol_hl),
                }
                
                if m.type_mouvement in ('entree', 'achat', 'production'):
                    data['entries'].append(entry)
                    data['totals']['entrees_hl'] += vol_hl
                elif m.type_mouvement in ('sortie', 'vente', 'expedition'):
                    data['exits'].append(entry)
                    data['totals']['sorties_hl'] += vol_hl
            
            # Estimer la complétion
            if data['entries'] or data['exits']:
                data['completeness'] = 80  # Données présentes
            else:
                data['completeness'] = 10  # Pas de données
                
        except Exception as e:
            logger.warning(f"Erreur génération pré-brouillon DRM: {e}")
            data['error'] = str(e)
        
        return data
    
    @staticmethod
    def _month_name(month: int) -> str:
        """Retourne le nom du mois en français"""
        names = [
            "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return names[month] if 1 <= month <= 12 else ""


# =============================================================================
# 5. MÉMOIRE DES INTRANTS (Traçabilité)
# =============================================================================

class IntrantMemory:
    """
    Mémorise les intrants utilisés et pré-remplit les formulaires.
    """
    
    @classmethod
    def get_suggested_intrants(
        cls,
        organization,
        operation_type: str,
        lot_type: str = None,
        cepage: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Retourne les intrants suggérés basés sur l'historique.
        
        Args:
            organization: Organisation courante
            operation_type: Type d'opération (collage, sulfitage, etc.)
            lot_type: Type de vin (rouge, blanc, rosé)
            cepage: Cépage principal (optionnel)
        """
        from apps.production.models import OperationChai
        
        suggestions = []
        
        try:
            # Chercher les opérations similaires de l'année dernière
            one_year_ago = timezone.now() - timedelta(days=365)
            
            operations = OperationChai.objects.filter(
                organization=organization,
                type_operation=operation_type,
                date__gte=one_year_ago,
            ).select_related('lot')
            
            if lot_type:
                operations = operations.filter(lot__type_vin=lot_type)
            
            # Compter les intrants utilisés
            intrant_counts = {}
            for op in operations[:50]:  # Limiter pour performance
                intrants = op.intrants or []
                for intrant in intrants:
                    key = (intrant.get('produit'), intrant.get('dose_unite'))
                    if key[0]:
                        if key not in intrant_counts:
                            intrant_counts[key] = {
                                'produit': intrant.get('produit'),
                                'dose': intrant.get('dose'),
                                'dose_unite': intrant.get('dose_unite'),
                                'count': 0,
                                'last_used': None,
                            }
                        intrant_counts[key]['count'] += 1
                        if not intrant_counts[key]['last_used'] or op.date > intrant_counts[key]['last_used']:
                            intrant_counts[key]['last_used'] = op.date
            
            # Trier par fréquence d'utilisation
            sorted_intrants = sorted(
                intrant_counts.values(),
                key=lambda x: x['count'],
                reverse=True
            )
            
            for intrant in sorted_intrants[:5]:  # Top 5
                suggestions.append({
                    'produit': intrant['produit'],
                    'dose': intrant['dose'],
                    'dose_unite': intrant['dose_unite'],
                    'frequency': intrant['count'],
                    'last_used': intrant['last_used'].isoformat() if intrant['last_used'] else None,
                    'source': 'historique',
                })
                
        except Exception as e:
            logger.warning(f"Erreur mémoire intrants: {e}")
        
        return suggestions
    
    @classmethod
    def get_nudge_for_operation(cls, organization, operation_type: str, lot=None) -> Optional[Nudge]:
        """
        Retourne un nudge de suggestion d'intrant pour une opération.
        """
        lot_type = lot.type_vin if lot and hasattr(lot, 'type_vin') else None
        
        suggestions = cls.get_suggested_intrants(
            organization,
            operation_type,
            lot_type=lot_type,
        )
        
        if suggestions:
            top = suggestions[0]
            return Nudge(
                type=NudgeType.SPARKLE,
                icon="bi-stars",
                title="Basé sur votre historique",
                message=f"{top['produit']} - {top['dose']} {top['dose_unite']} (utilisé {top['frequency']}x)",
                data={
                    'prefill': {
                        'produit': top['produit'],
                        'dose': top['dose'],
                        'dose_unite': top['dose_unite'],
                    },
                    'all_suggestions': suggestions,
                },
                priority=50,
            )
        
        return None


# =============================================================================
# SERVICE CENTRALISÉ
# =============================================================================

class SmartSuggestions:
    """
    Point d'entrée centralisé pour toutes les suggestions intelligentes.
    """
    
    @classmethod
    def get_header_notifications(cls, organization) -> List[Nudge]:
        """
        Récupère toutes les notifications à afficher dans le header.
        """
        nudges = []
        
        # Timer DRM
        drm_nudge = DRMTimer.get_header_nudge(organization)
        if drm_nudge:
            nudges.append(drm_nudge)
        
        # Autres notifications globales à ajouter ici...
        
        # Trier par priorité
        nudges.sort(key=lambda x: -x.priority)
        
        return nudges
    
    @classmethod
    def get_parcelle_context(cls, parcelle) -> Dict[str, Any]:
        """
        Contexte intelligent pour une page parcelle.
        """
        return {
            'weather_nudges': WeatherService.get_parcelle_alerts(parcelle),
            'weather_forecast': WeatherService.get_forecast(
                float(parcelle.latitude or parcelle.centroid_y or 46.5),
                float(parcelle.longitude or parcelle.centroid_x or 2.5),
                days=3
            ) if (parcelle.latitude or parcelle.centroid_y) else [],
        }
    
    @classmethod
    def get_lot_context(cls, lot) -> Dict[str, Any]:
        """
        Contexte intelligent pour une page lot technique.
        """
        return {
            'analyse_nudges': AnalyseDetective.analyze_lot(lot),
        }
    
    @classmethod
    def get_soutirage_context(cls, organization, volume_l: Decimal, exclude_ids: List[int] = None) -> Dict[str, Any]:
        """
        Contexte intelligent pour un formulaire de soutirage.
        """
        suggestions = CuveCalculator.get_destination_suggestions(
            organization,
            volume_l,
            exclude_ids=exclude_ids,
        )
        
        return {
            'cuve_suggestions': suggestions,
            'perfect_fits': [s for s in suggestions if s.highlight == 'perfect'],
            'good_fits': [s for s in suggestions if s.highlight == 'good'],
            'possible_fits': [s for s in suggestions if s.highlight == 'possible'],
            'disabled': [s for s in suggestions if s.highlight == 'disabled'],
        }
    
    @classmethod
    def get_operation_context(cls, organization, operation_type: str, lot=None) -> Dict[str, Any]:
        """
        Contexte intelligent pour un formulaire d'opération chai.
        """
        intrant_nudge = IntrantMemory.get_nudge_for_operation(organization, operation_type, lot)
        
        return {
            'intrant_suggestions': IntrantMemory.get_suggested_intrants(
                organization,
                operation_type,
                lot_type=getattr(lot, 'type_vin', None) if lot else None,
            ),
            'intrant_nudge': intrant_nudge,
        }
