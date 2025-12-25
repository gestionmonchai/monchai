"""
Vues API pour les suggestions intelligentes MonChai.
"""

from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from decimal import Decimal
import json


@method_decorator([login_required], name='dispatch')
class WeatherAlertsView(View):
    """API: Alertes météo pour une parcelle"""
    
    def get(self, request, parcelle_id):
        from apps.referentiels.models import Parcelle
        from apps.ai.smart_suggestions import WeatherService
        
        try:
            parcelle = Parcelle.objects.get(pk=parcelle_id)
            nudges = WeatherService.get_parcelle_alerts(parcelle)
            
            return JsonResponse({
                'success': True,
                'nudges': [n.to_dict() for n in nudges],
                'parcelle': parcelle.nom,
            })
        except Parcelle.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Parcelle non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class WeatherForecastView(View):
    """API: Prévisions météo pour des coordonnées"""
    
    def get(self, request):
        from apps.ai.smart_suggestions import WeatherService
        
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        days = int(request.GET.get('days', 3))
        
        if not lat or not lon:
            return JsonResponse({'success': False, 'error': 'lat et lon requis'}, status=400)
        
        try:
            forecasts = WeatherService.get_forecast(float(lat), float(lon), days=days)
            return JsonResponse({
                'success': True,
                'forecasts': [
                    {
                        'date': f.date.isoformat(),
                        'temp_min': f.temp_min,
                        'temp_max': f.temp_max,
                        'precipitation_mm': f.precipitation_mm,
                        'precipitation_prob': f.precipitation_prob,
                        'wind_speed_kmh': f.wind_speed_kmh,
                        'description': f.description,
                        'icon': f.icon,
                    }
                    for f in forecasts
                ],
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class CuveSuggestionsView(View):
    """API: Suggestions de cuves pour soutirage/assemblage"""
    
    def get(self, request):
        from apps.ai.smart_suggestions import CuveCalculator
        
        volume_l = request.GET.get('volume_l')
        exclude_ids = request.GET.getlist('exclude')
        operation = request.GET.get('operation', 'soutirage')
        
        if not volume_l:
            return JsonResponse({'success': False, 'error': 'volume_l requis'}, status=400)
        
        try:
            organization = getattr(request, 'current_org', None)
            if not organization:
                return JsonResponse({'success': False, 'error': 'Organisation non définie'}, status=400)
            
            exclude_ids = [int(x) for x in exclude_ids if x.isdigit()]
            
            suggestions = CuveCalculator.get_destination_suggestions(
                organization,
                Decimal(str(volume_l)),
                exclude_ids=exclude_ids,
                operation_type=operation,
            )
            
            return JsonResponse({
                'success': True,
                'volume_source_l': float(volume_l),
                'suggestions': [
                    {
                        'id': s.contenant.id,
                        'code': s.contenant.code,
                        'type': s.contenant.get_type_display(),
                        'capacite_l': float(s.contenant.capacite_l),
                        'free_capacity_l': float(s.contenant.free_capacity_l()),
                        'occupancy_pct': float(s.contenant.occupancy_pct),
                        'fit_score': s.fit_score,
                        'reason': s.reason,
                        'highlight': s.highlight,
                    }
                    for s in suggestions
                ],
                'summary': {
                    'perfect': sum(1 for s in suggestions if s.highlight == 'perfect'),
                    'good': sum(1 for s in suggestions if s.highlight == 'good'),
                    'possible': sum(1 for s in suggestions if s.highlight == 'possible'),
                    'disabled': sum(1 for s in suggestions if s.highlight == 'disabled'),
                },
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class AnalyseAlertsView(View):
    """API: Alertes d'analyse pour un lot"""
    
    def get(self, request, lot_id):
        from apps.production.models import LotTechnique
        from apps.ai.smart_suggestions import AnalyseDetective
        
        try:
            lot = LotTechnique.objects.get(pk=lot_id)
            nudges = AnalyseDetective.analyze_lot(lot)
            
            return JsonResponse({
                'success': True,
                'nudges': [n.to_dict() for n in nudges],
                'lot': str(lot),
            })
        except LotTechnique.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Lot non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class DRMStatusView(View):
    """API: Statut DRM et pré-brouillon"""
    
    def get(self, request):
        from apps.ai.smart_suggestions import DRMTimer
        
        try:
            organization = getattr(request, 'current_org', None)
            if not organization:
                return JsonResponse({'success': False, 'error': 'Organisation non définie'}, status=400)
            
            status = DRMTimer.get_drm_status(organization)
            
            # Générer le pré-brouillon si demandé
            include_brouillon = request.GET.get('brouillon', 'false').lower() == 'true'
            brouillon = None
            
            if include_brouillon:
                brouillon = DRMTimer.generate_pre_brouillon(organization, status['period'])
            
            return JsonResponse({
                'success': True,
                'status': {
                    'period': status['period'],
                    'period_display': status['period_display'],
                    'deadline': status['deadline'].isoformat(),
                    'days_remaining': status['days_remaining'],
                    'is_urgent': status['is_urgent'],
                    'is_overdue': status['is_overdue'],
                },
                'brouillon': brouillon,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class IntrantSuggestionsView(View):
    """API: Suggestions d'intrants basées sur l'historique"""
    
    def get(self, request):
        from apps.ai.smart_suggestions import IntrantMemory
        
        operation_type = request.GET.get('operation')
        lot_type = request.GET.get('lot_type')
        
        if not operation_type:
            return JsonResponse({'success': False, 'error': 'operation requis'}, status=400)
        
        try:
            organization = getattr(request, 'current_org', None)
            if not organization:
                return JsonResponse({'success': False, 'error': 'Organisation non définie'}, status=400)
            
            suggestions = IntrantMemory.get_suggested_intrants(
                organization,
                operation_type,
                lot_type=lot_type,
            )
            
            return JsonResponse({
                'success': True,
                'operation_type': operation_type,
                'suggestions': suggestions,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator([login_required], name='dispatch')
class SmartContextView(View):
    """API: Contexte intelligent complet pour une page"""
    
    def get(self, request):
        from apps.ai.smart_suggestions import SmartSuggestions
        
        context_type = request.GET.get('type')
        
        try:
            organization = getattr(request, 'current_org', None)
            if not organization:
                return JsonResponse({'success': False, 'error': 'Organisation non définie'}, status=400)
            
            if context_type == 'header':
                nudges = SmartSuggestions.get_header_notifications(organization)
                return JsonResponse({
                    'success': True,
                    'nudges': [n.to_dict() for n in nudges],
                })
            
            return JsonResponse({'success': False, 'error': 'type inconnu'}, status=400)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
