"""
URLs pour la gestion des clients - Roadmap 36
"""

from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Pages principales
    path('', views.customers_list, name='customers_list'),
    path('v2/', views.customers_list_v2, name='customers_list_v2'),
    path('nouveau/', views.customer_create, name='customer_create'),
    path('<uuid:customer_id>/', views.customer_detail, name='customer_detail'),
    path('<uuid:customer_id>/modifier/', views.customer_edit, name='customer_edit'),
    
    # Export
    path('export/', views.customers_export, name='customers_export'),
    
    # Recherche AJAX (comme les cépages)
    path('search-ajax/', views.customers_search_ajax, name='customers_search_ajax'),
    
    # API
    path('api/', views.customers_api, name='customers_api'),
    path('api/suggestions/', views.customers_suggestions_api, name='customers_suggestions_api'),
    path('api/quick-create/', views.customers_quick_create_api, name='customers_quick_create_api'),
    path('api/duplicates/', views.duplicate_detection_api, name='duplicate_detection_api'),
]
