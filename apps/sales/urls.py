"""
URLs pour le module Ventes
"""
from django.urls import path
from . import views_pricelists, views_documents

app_name = 'sales'

urlpatterns = [
    # Grilles tarifaires
    path('tarifs/', views_pricelists.pricelist_list, name='pricelist_list'),
    path('tarifs/creer/', views_pricelists.pricelist_create, name='pricelist_create'),
    path('tarifs/<uuid:pk>/', views_pricelists.pricelist_detail, name='pricelist_detail'),
    path('tarifs/<uuid:pk>/modifier/', views_pricelists.pricelist_edit, name='pricelist_edit'),
    path('tarifs/<uuid:pk>/supprimer/', views_pricelists.pricelist_delete, name='pricelist_delete'),
    
    # Édition en grille
    path('tarifs/<uuid:pk>/grille/', views_pricelists.pricelist_grid_edit, name='pricelist_grid_edit'),
    
    # Import tarifaire
    path('tarifs/<uuid:pk>/import/', views_pricelists.pricelist_import, name='pricelist_import'),
    path('tarifs/<uuid:pk>/import/preview/', views_pricelists.pricelist_import_preview, name='pricelist_import_preview'),
    path('tarifs/<uuid:pk>/import/confirm/', views_pricelists.pricelist_import_confirm, name='pricelist_import_confirm'),
    
    # API recherche temps réel
    path('api/tarifs/search/', views_pricelists.pricelist_search_api, name='pricelist_search_api'),
    
    # API items (pour édition grille AJAX)
    path('api/tarifs/<uuid:pk>/items/', views_pricelists.pricelist_items_api, name='pricelist_items_api'),
    path('api/tarifs/items/<uuid:item_id>/', views_pricelists.priceitem_update_api, name='priceitem_update_api'),
    
    # Templates de documents
    path('templates/', views_documents.template_list, name='template_list'),
    path('templates/creer/', views_documents.template_create, name='template_create'),
    path('templates/<uuid:pk>/', views_documents.template_detail, name='template_detail'),
    path('templates/<uuid:pk>/modifier/', views_documents.template_edit, name='template_edit'),
    path('templates/<uuid:pk>/supprimer/', views_documents.template_delete, name='template_delete'),
    path('templates/<uuid:pk>/dupliquer/', views_documents.template_duplicate, name='template_duplicate'),
    path('templates/<uuid:pk>/generaliser/', views_documents.template_generalize, name='template_generalize'),
    path('templates/<uuid:pk>/apercu/', views_documents.template_preview, name='template_preview'),
    path('templates/<uuid:pk>/pdf/<str:doc_type>/<uuid:doc_id>/', views_documents.template_generate_pdf, name='template_generate_pdf'),
    path('templates/<uuid:pk>/variables/', views_documents.template_variables_help, name='template_variables_help'),
]
