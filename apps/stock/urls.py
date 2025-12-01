"""
URLs pour la gestion des stocks et transferts
Roadmap 32 - Stocks/Transferts
"""

from django.urls import path
from . import views, api_views

app_name = 'stock'

urlpatterns = [
    # Dashboard stocks
    path('', views.stock_dashboard, name='dashboard'),

    # Journal des mouvements (nouveau)
    path('mouvements/', views.mouvements_view, name='mouvements'),

    # Inventaires (nouvelle arborescence)
    path('inventaires/', views.inventaire_list, name='inventaire_list'),
    path('inventaires/nouveau/', views.inventaire_new, name='inventaire_new'),
    path('inventaires/<uuid:pk>/', views.inventaire_detail, name='inventaire_detail'),

    # Entrepôts & Emplacements
    path('entrepots/', views.entrepots_list, name='entrepots'),
    path('emplacements/', views.emplacements_list, name='emplacements'),

    # Transferts - Roadmap 32 (existants)
    path('transferts/', views.transferts_list, name='transferts_list'),
    path('transferts/nouveau/', views.transfert_create, name='transfert_create'),
    
    # Inventaire - Roadmap 33 (existants)
    path('inventaire/', views.inventaire_view, name='inventaire_view'),
    path('inventaire/counting/<uuid:warehouse_id>/', views.inventaire_counting_view, name='inventaire_counting_view'),
    
    # Alertes - Roadmap 34
    path('alertes/', views.alertes_view, name='alertes_view'),
    path('seuils/', views.seuils_view, name='seuils_view'),
    
    # API Transferts
    path('api/transferts/', api_views.transferts_api, name='transferts_api'),
    path('api/transferts/create/', api_views.transfert_create_api, name='transfert_create_api'),
    
    # API Inventaire - Roadmap 33
    path('api/inventaire/', api_views.inventaire_api, name='inventaire_api'),
    path('api/inventaire/counting/<uuid:warehouse_id>/', api_views.inventaire_counting_api, name='inventaire_counting_api'),
    path('api/inventaire/calculate-adjustments/', api_views.inventaire_calculate_adjustments_api, name='inventaire_calculate_adjustments_api'),
    path('api/inventaire/apply-adjustments/', api_views.inventaire_apply_adjustments_api, name='inventaire_apply_adjustments_api'),
    
    # API Alertes - Roadmap 34
    path('api/alertes/', api_views.alertes_api, name='alertes_api'),
    path('api/alertes/acknowledge/', api_views.acknowledge_alert_api, name='acknowledge_alert_api'),
    path('api/alertes/badge-count/', api_views.alerts_badge_count_api, name='alerts_badge_count_api'),
    path('api/seuils/create/', api_views.create_threshold_api, name='create_threshold_api'),
    path('api/seuils/<uuid:threshold_id>/', api_views.delete_threshold_api, name='delete_threshold_api'),
]
