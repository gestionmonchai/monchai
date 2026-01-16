from django.urls import path, include
from django.views.generic import TemplateView
from . import views, api
from apps.sales import views_pricelists, views_documents
from apps.referentiels import views_produits
from apps.ventes import views_clients as ventes_clients_views
from apps.ventes import views_clients_detail

app_name = 'ventes'

urlpatterns = [
    # --- HTMX PARTIALS ---
    path('htmx/clients-search/', views.client_search_htmx, name='client_search_htmx'),
    
    # --- TABLEAU DE BORD ---
    path('tableau-de-bord/', views.dashboard, {'side': 'sale'}, name='dashboard'),
    
    # --- PRODUITS (CATALOGUE VENTE) - Pointe vers base commune /referentiels/produits/ ---
    path('produits/', views_produits.produit_list, {'usage_filter': 'vente'}, name='produit_list'),
    path('produits/nouveau/', views_produits.produit_create, {'usage_preset': 'vente'}, name='produit_create'),
    path('produits/<int:pk>/', views_produits.produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/', views_produits.produit_update, name='produit_update'),

    # --- DÉVELOPPEMENT COMMERCIAL ---
    
    # Clients (redirige vers nouvelle app partners)
    path('clients/', include('apps.partners.urls_ventes')),
    path('clients/<int:display_id>/', views_clients_detail.client_detail_ventes, name='client_detail'),
    path('clients/<int:display_id>/devis/', views_clients_detail.client_quotes_ventes, name='client_quotes'),
    path('clients/<int:display_id>/commandes/', views_clients_detail.client_orders_ventes, name='client_orders'),
    path('clients/<int:display_id>/factures/', views_clients_detail.client_invoices_ventes, name='client_invoices'),

    # Pipeline (Vue globale opportunités/devis) - À faire, placeholder sur dashboard ou devis pour l'instant
    path('pipeline/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'quote'}, name='pipeline'),

    # Devis / Proformas
    path('devis/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'quote'}, name='quotes_list'),
    path('devis/nouveau/', views.DocumentCreateView.as_view(), {'side': 'sale', 'type': 'quote'}, name='quote_create'),
    path('devis/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'sale'}, name='quote_detail'),
    
    # --- COMMANDES & EXÉCUTION ---
    
    # Commandes
    path('commandes/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'order'}, name='orders_list'),
    path('commandes/nouvelle/', views.DocumentCreateView.as_view(), {'side': 'sale', 'type': 'order'}, name='order_create'),
    path('commandes/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'sale'}, name='order_detail'),

    # Livraisons (BL)
    path('livraisons/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'delivery'}, name='deliveries_list'),
    path('livraisons/nouvelle/', views.DocumentCreateView.as_view(), {'side': 'sale', 'type': 'delivery'}, name='delivery_create'),
    path('livraisons/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'sale'}, name='delivery_detail'),

    # --- FACTURATION ---
    
    # Factures
    path('factures/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'invoice'}, name='invoices_list'),
    path('factures/nouvelle/', views.InvoiceCreateView.as_view(), {'side': 'sale', 'type': 'invoice'}, name='invoice_create'),
    path('factures/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'sale'}, name='invoice_detail'),
    
    # Avoirs
    path('avoirs/', views.DocumentListView.as_view(), {'side': 'sale', 'doc_type': 'credit_note'}, name='credit_notes_list'),
    path('avoirs/nouvel/', views.DocumentCreateView.as_view(), {'side': 'sale', 'type': 'credit_note'}, name='credit_note_create'),
    path('avoirs/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'sale'}, name='credit_note_detail'),

    # --- ENCAISSEMENTS ---
    path('paiements/echeancier/', views.PaymentScheduleView.as_view(), {'side': 'sale'}, name='payment_schedule'),
    path('paiements/encaissements/', views.PaymentListView.as_view(), {'side': 'sale'}, name='payment_list'),
    
    # --- GESTION TARIFAIRE (Migré depuis apps.sales) ---
    # Grilles tarifaires
    path('grilletarifs/', views_pricelists.pricelist_list, name='pricelist_list'),
    path('grilletarifs/creer/', views_pricelists.pricelist_create, name='pricelist_create'),
    path('grilletarifs/<int:pk>/', views_pricelists.pricelist_detail, name='pricelist_detail'),
    path('grilletarifs/<int:pk>/modifier/', views_pricelists.pricelist_edit, name='pricelist_edit'),
    path('grilletarifs/<int:pk>/supprimer/', views_pricelists.pricelist_delete, name='pricelist_delete'),
    
    # Édition en grille
    path('grilletarifs/<int:pk>/grille/', views_pricelists.pricelist_grid_edit, name='pricelist_grid_edit'),
    
    # Import tarifaire
    path('grilletarifs/<int:pk>/import/', views_pricelists.pricelist_import, name='pricelist_import'),
    path('grilletarifs/<int:pk>/import/apercu/', views_pricelists.pricelist_import_preview, name='pricelist_import_preview'),
    path('grilletarifs/<int:pk>/import/confirmer/', views_pricelists.pricelist_import_confirm, name='pricelist_import_confirm'),
    
    # API recherche temps réel
    path('api/grilletarifs/search/', views_pricelists.pricelist_search_api, name='pricelist_search_api'),
    
    # API items (pour édition grille AJAX)
    path('api/grilletarifs/<int:pk>/items/', views_pricelists.pricelist_items_api, name='pricelist_items_api'),
    path('api/grilletarifs/items/<uuid:item_id>/', views_pricelists.priceitem_update_api, name='priceitem_update_api'),
    
    # Templates de documents
    path('modeles/', views_documents.template_list, name='template_list'),
    path('modeles/creer/', views_documents.template_builder, name='template_create'),  # Builder visuel par défaut
    path('modeles/creer-html/', views_documents.template_create, name='template_create_html'),  # Ancien mode HTML
    path('modeles/creer-blocks/', views_documents.template_save_blocks, name='template_create_blocks'),  # API création
    path('modeles/<uuid:pk>/', views_documents.template_detail, name='template_detail'),
    path('modeles/<uuid:pk>/modifier/', views_documents.template_builder, name='template_edit'),  # Builder visuel
    path('modeles/<uuid:pk>/modifier-html/', views_documents.template_edit, name='template_edit_html'),  # Ancien mode
    path('modeles/<uuid:pk>/save-blocks/', views_documents.template_save_blocks, name='template_save_blocks'),  # API save
    path('modeles/<uuid:pk>/supprimer/', views_documents.template_delete, name='template_delete'),
    path('modeles/<uuid:pk>/dupliquer/', views_documents.template_duplicate, name='template_duplicate'),
    path('modeles/<uuid:pk>/generaliser/', views_documents.template_generalize, name='template_generalize'),
    path('modeles/<uuid:pk>/apercu/', views_documents.template_preview, name='template_preview'),
    path('modeles/<uuid:pk>/pdf/<str:doc_type>/<uuid:doc_id>/', views_documents.template_generate_pdf, name='template_generate_pdf'),
    path('modeles/<uuid:pk>/variables/', views_documents.template_variables_help, name='template_variables_help'),

    # --- ACTIONS COMMUNES ---
    path('document/<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'), # Fallback générique
    path('document/<uuid:pk>/modifier/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('document/<uuid:pk>/supprimer/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Actions
    path('document/<uuid:pk>/transformer/<str:target_type>/', views.transform_document, name='document_transform'),
    path('document/<uuid:pk>/valider/', views.validate_document, name='document_validate'),
    path('document/<uuid:pk>/executer/', views.execute_document, name='document_execute'),
    path('document/<uuid:pk>/paiement/ajouter/', views.add_payment, name='payment_add'),
    path('document/<uuid:pk>/ligne/ajouter/', views.add_line, name='line_add'),
    path('ligne/<uuid:pk>/supprimer/', views.delete_line, name='line_delete'),
    
    # API
    path('api/sku/<int:pk>/', api.get_sku_details, name='api_sku_details'),
    path('api/sku/search/', api.search_skus, name='api_sku_search'),
    path('api/clients/search/', api.search_clients, name='api_clients_search'),
    path('api/clients/<uuid:pk>/', api.get_client_details, name='api_client_details'),

    # --- PAGES STATIQUES / DIVERS ---
    path('conditions/', TemplateView.as_view(template_name='commerce/conditions_list.html', extra_context={'page_title': 'Conditions'}), name='conditions_list'),
    path('expeditions/', TemplateView.as_view(template_name='commerce/expeditions_list.html', extra_context={'page_title': 'Expéditions'}), name='expeditions_list'),
]
