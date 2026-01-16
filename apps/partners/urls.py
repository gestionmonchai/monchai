"""
URLs pour la gestion des partenaires (Tiers unifiés)
Remplace l'ancienne app clients
"""

from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    # ===== LISTES =====
    path('', views.partners_list, name='partners_list'),
    path('clients/', views.clients_list, name='clients_list'),
    path('fournisseurs/', views.suppliers_list, name='suppliers_list'),
    
    # ===== CRÉATION =====
    path('nouveau/', views.partner_create, name='partner_create'),
    path('nouveau/client/', views.partner_create_as_client, name='partner_create_as_client'),
    path('nouveau/fournisseur/', views.partner_create_as_supplier, name='partner_create_as_supplier'),
    
    # ===== FICHE PARTENAIRE =====
    path('<int:display_id>/', views.partner_detail, name='partner_detail'),
    path('<int:display_id>/modifier/', views.partner_edit, name='partner_edit'),
    path('<int:display_id>/archiver/', views.partner_archive, name='partner_archive'),
    path('<int:display_id>/restaurer/', views.partner_restore, name='partner_restore'),
    path('<int:display_id>/ajouter-role/', views.partner_add_role, name='partner_add_role'),
    
    # ===== ADRESSES =====
    path('<int:partner_display_id>/adresses/nouvelle/', views.address_create, name='address_create'),
    path('adresses/<uuid:address_id>/supprimer/', views.address_delete, name='address_delete'),
    
    # ===== INTERLOCUTEURS =====
    path('<int:partner_display_id>/contacts/nouveau/', views.contact_create, name='contact_create'),
    path('contacts/<uuid:contact_id>/supprimer/', views.contact_delete, name='contact_delete'),
    
    # ===== PROFILS SPÉCIFIQUES =====
    path('<int:partner_display_id>/profil-client/', views.client_profile_edit, name='client_profile_edit'),
    path('<int:partner_display_id>/profil-fournisseur/', views.supplier_profile_edit, name='supplier_profile_edit'),
    
    # ===== TABLEAUX AJAX (HTMX) =====
    path('tableau/', views.partners_table_ajax, name='partners_table'),
    path('clients/tableau/', views.partners_table_ajax, {'role': 'client'}, name='clients_table'),
    path('fournisseurs/tableau/', views.partners_table_ajax, {'role': 'supplier'}, name='suppliers_table'),
    
    # ===== API / AJAX =====
    path('api/recherche/', views.partners_search_ajax, name='partners_search_ajax'),
    path('api/suggestions/', views.partners_suggestions_api, name='partners_suggestions_api'),
    path('api/creation-rapide/', views.partner_quick_create_api, name='partner_quick_create_api'),
    path('api/doublons/', views.partner_quick_create_api, name='duplicate_detection_api'),
    path('export/', views.partners_list, name='partners_export'),
]
