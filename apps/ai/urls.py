from django.urls import path
from .views import help_assistant, help_query
from .views_smart import (
    WeatherAlertsView, WeatherForecastView, CuveSuggestionsView,
    AnalyseAlertsView, DRMStatusView, IntrantSuggestionsView, SmartContextView
)

app_name = 'ai'

urlpatterns = [
    path('aide/', help_assistant, name='help_assistant'),
    path('aide/requete', help_query, name='help_query'),
    
    # Smart Suggestions API
    path('smart/meteo/parcelle/<int:parcelle_id>/', WeatherAlertsView.as_view(), name='weather_parcelle'),
    path('smart/meteo/previsions/', WeatherForecastView.as_view(), name='weather_forecast'),
    path('smart/cuves/', CuveSuggestionsView.as_view(), name='cuve_suggestions'),
    path('smart/analyse/<int:lot_id>/', AnalyseAlertsView.as_view(), name='analyse_alerts'),
    path('smart/drm/', DRMStatusView.as_view(), name='drm_status'),
    path('smart/intrants/', IntrantSuggestionsView.as_view(), name='intrant_suggestions'),
    path('smart/contexte/', SmartContextView.as_view(), name='smart_context'),
]
