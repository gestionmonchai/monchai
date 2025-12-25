"""
URLs pour les référentiels viticoles
Roadmap Cut #3 : Référentiels (starter pack)
"""

from django.urls import path
from django.views.generic import RedirectView

from apps.referentiels.views import (
    # Home
    referentiels_home,
    # Cépages
    cepage_list, export_cepages, cepage_search_ajax, cepage_detail, cepage_create, cepage_update, cepage_delete,
    cepage_import_from_reference,
    # Parcelles
    parcelle_list, parcelles_map, export_parcelles, parcelle_search_ajax, parcelle_detail, parcelle_create, parcelle_update, parcelle_delete, parcelles_update_geo,
    parcelle_cepages_api,
    # Encépagement
    encepagement_add, encepagement_edit, encepagement_delete,
    # Unités
    unite_list, export_unites, unite_search_ajax, unite_detail, unite_create, unite_update, unite_delete,
    # Cuvées
    cuvee_list, export_cuvees, cuvee_search_ajax, cuvee_detail, cuvee_create, cuvee_update, cuvee_delete,
    # Entrepôts
    entrepot_list, export_entrepots, entrepot_search_ajax, entrepot_detail, entrepot_create, entrepot_update, entrepot_delete,
    # Import CSV
    import_csv, import_csv_preview, import_csv_execute, import_csv_download_errors,
    # Secure Import API
    import_intake_api, import_preview_api, import_execute_api,
)
from . import api_v2
from .views_produits import (
    produit_list, produit_search_ajax, produit_create, produit_detail, 
    produit_update, produit_archive, categorie_create_ajax
)

app_name = 'referentiels'

urlpatterns = [
    # Page d'accueil référentiels
    path('', referentiels_home, name='home'),
    
    # Cépages - Roadmap item 14
    path('cepages/', cepage_list, name='cepage_list'),
    path('cepages/export/', export_cepages, name='export_cepages'),
    path('cepages/search-ajax/', cepage_search_ajax, name='cepage_search_ajax'),
    path('cepages/import-reference/', cepage_import_from_reference, name='cepage_import_reference'),
    path('cepages/<int:pk>/', cepage_detail, name='cepage_detail'),
    path('cepages/nouveau/', cepage_create, name='cepage_create'),
    path('cepages/<int:pk>/modifier/', cepage_update, name='cepage_update'),
    path('cepages/<int:pk>/supprimer/', cepage_delete, name='cepage_delete'),
    
    # Parcelles
    path('parcelles/', parcelle_list, name='parcelle_list'),
    path('parcelles/carte/', parcelles_map, name='parcelles_map'),
    path('parcelles/export/', export_parcelles, name='export_parcelles'),
    path('parcelles/search-ajax/', parcelle_search_ajax, name='parcelle_search_ajax'),
    path('parcelles/<int:pk>/', parcelle_detail, name='parcelle_detail'),
    path('parcelles/nouvelle/', parcelle_create, name='parcelle_create'),
    path('parcelles/<int:pk>/modifier/', parcelle_update, name='parcelle_update'),
    path('parcelles/<int:pk>/supprimer/', parcelle_delete, name='parcelle_delete'),
    path('parcelles/api/update-geo/', parcelles_update_geo, name='parcelles_update_geo'),
    
    # Encépagement
    path('parcelles/<int:parcelle_pk>/encepagement/ajouter/', encepagement_add, name='encepagement_add'),
    path('parcelles/<int:parcelle_pk>/encepagement/<int:pk>/modifier/', encepagement_edit, name='encepagement_edit'),
    path('parcelles/<int:parcelle_pk>/encepagement/<int:pk>/supprimer/', encepagement_delete, name='encepagement_delete'),
    
    # API Cépages parcelle
    path('parcelles/<int:pk>/cepages-api/', parcelle_cepages_api, name='parcelle_cepages_api'),
    
    # Unités - Roadmap item 16
    path('unites/', unite_list, name='unite_list'),
    path('unites/export/', export_unites, name='export_unites'),
    path('unites/search-ajax/', unite_search_ajax, name='unite_search_ajax'),
    path('unites/<int:pk>/', unite_detail, name='unite_detail'),
    path('unites/nouvelle/', unite_create, name='unite_create'),
    path('unites/<int:pk>/modifier/', unite_update, name='unite_update'),
    path('unites/<int:pk>/supprimer/', unite_delete, name='unite_delete'),
    
    # Cuvées - Roadmap item 17
    path('cuvees/', cuvee_list, name='cuvee_list'),
    path('cuvees/export/', export_cuvees, name='export_cuvees'),
    path('cuvees/search-ajax/', cuvee_search_ajax, name='cuvee_search_ajax'),
    path('cuvees/<int:pk>/', cuvee_detail, name='cuvee_detail'),
    path('cuvees/nouvelle/', cuvee_create, name='cuvee_create'),
    path('cuvees/<int:pk>/modifier/', cuvee_update, name='cuvee_update'),
    path('cuvees/<int:pk>/supprimer/', cuvee_delete, name='cuvee_delete'),
    
    # Entrepôts - Roadmap item 18
    path('entrepots/', entrepot_list, name='entrepot_list'),
    path('entrepots/export/', export_entrepots, name='export_entrepots'),
    path('entrepots/search-ajax/', entrepot_search_ajax, name='entrepot_search_ajax'),
    path('entrepots/<int:pk>/', entrepot_detail, name='entrepot_detail'),
    path('entrepots/nouveau/', entrepot_create, name='entrepot_create'),
    path('entrepots/<int:pk>/modifier/', entrepot_update, name='entrepot_update'),
    path('entrepots/<int:pk>/supprimer/', entrepot_delete, name='entrepot_delete'),
    
    # Produits (base commune) - Nouvelle architecture
    path('produits/', produit_list, name='produit_list'),
    path('produits/search-ajax/', produit_search_ajax, name='produit_search_ajax'),
    path('produits/nouveau/', produit_create, name='produit_create'),
    path('produits/<int:pk>/', produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/', produit_update, name='produit_update'),
    path('produits/<int:pk>/archiver/', produit_archive, name='produit_archive'),
    path('produits/categories/nouveau/', categorie_create_ajax, name='categorie_create_ajax'),
    
    # Import CSV - Roadmap item 18
    path('import/', import_csv, name='import_csv'),
    path('import/preview/', import_csv_preview, name='import_csv_preview'),
    path('import/execute/', import_csv_execute, name='import_csv_execute'),
    path('import/download-errors/', import_csv_download_errors, name='import_csv_download_errors'),
    # New secure Import API
    path('import/api/intake/', import_intake_api, name='import_intake_api'),
    path('import/api/preview/', import_preview_api, name='import_preview_api'),
    path('import/api/execute/', import_execute_api, name='import_execute_api'),
    
    # API V2 - GIGA ROADMAP S2
    path('api/v2/search/', api_v2.search_api_v2, name='search_api_v2'),
    path('api/v2/suggestions/', api_v2.search_suggestions_v2, name='search_suggestions_v2'),
    path('api/v2/facets/', api_v2.search_facets_v2, name='search_facets_v2'),
    
    # Inline Edit V2
    path('api/v2/<str:entity_type>/<int:entity_id>/cell/<str:field_name>/', 
         api_v2.inline_edit_cell_v2, name='inline_edit_cell_v2'),
    path('api/v2/<str:entity_type>/<int:entity_id>/cell/<str:field_name>/save/', 
         api_v2.inline_edit_save_v2, name='inline_edit_save_v2'),
    path('api/v2/undo/', api_v2.inline_edit_undo_v2, name='inline_edit_undo_v2'),
]
