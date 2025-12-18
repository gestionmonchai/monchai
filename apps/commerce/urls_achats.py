from django.urls import path, include
from django.views.generic import RedirectView
from . import views, api
from apps.clients import views as clients_views
from apps.referentiels import views_produits

app_name = 'achats'

urlpatterns = [
    # --- TABLEAU DE BORD ---
    path('dashboard/', views.dashboard, {'side': 'purchase'}, name='dashboard'),
    
    # --- ARTICLES (CATALOGUE ACHAT) - Pointe vers base commune /referentiels/produits/ ---
    path('articles/', views_produits.produit_list, {'usage_filter': 'achat'}, name='article_list'),
    path('articles/nouveau/', views_produits.produit_create, {'usage_preset': 'achat'}, name='article_create'),
    path('articles/<int:pk>/', views_produits.produit_detail, name='article_detail'),
    path('articles/<int:pk>/modifier/', views_produits.produit_update, name='article_update'),

    # --- FOURNISSEURS ---
    path('fournisseurs/', clients_views.customers_list, {'segment_override': 'supplier'}, name='suppliers_list'),
    path('fournisseurs/nouveau/', clients_views.customer_create, name='supplier_create'),
    path('fournisseurs/<uuid:customer_id>/', clients_views.customer_detail, name='supplier_detail'),
    path('fournisseurs/<uuid:customer_id>/modifier/', clients_views.customer_edit, name='supplier_edit'),


    # --- CYCLE D'ACHAT ---
    
    # Demandes de prix (Quote)
    path('demandes-prix/', views.DocumentListView.as_view(), {'side': 'purchase', 'doc_type': 'quote'}, name='quotes_list'),
    path('demandes-prix/nouveau/', views.DocumentCreateView.as_view(), {'side': 'purchase', 'type': 'quote'}, name='quote_create'),
    path('demandes-prix/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'purchase'}, name='quote_detail'),
    
    # Commandes fournisseurs (Order)
    path('commandes/', views.DocumentListView.as_view(), {'side': 'purchase', 'doc_type': 'order'}, name='orders_list'),
    path('commandes/nouvelle/', views.DocumentCreateView.as_view(), {'side': 'purchase', 'type': 'order'}, name='order_create'),
    path('commandes/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'purchase'}, name='order_detail'),
    
    # Réceptions (Delivery)
    path('receptions/', views.DocumentListView.as_view(), {'side': 'purchase', 'doc_type': 'delivery'}, name='deliveries_list'),
    path('receptions/nouvelle/', views.DocumentCreateView.as_view(), {'side': 'purchase', 'type': 'delivery'}, name='delivery_create'),
    path('receptions/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'purchase'}, name='delivery_detail'),

    # --- FACTURATION ---
    
    # Factures
    path('factures/', views.DocumentListView.as_view(), {'side': 'purchase', 'doc_type': 'invoice'}, name='invoices_list'),
    path('factures/nouvelle/', views.DocumentCreateView.as_view(), {'side': 'purchase', 'type': 'invoice'}, name='invoice_create'),
    path('factures/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'purchase'}, name='invoice_detail'),
    
    # Avoirs
    path('avoirs/', views.DocumentListView.as_view(), {'side': 'purchase', 'doc_type': 'credit_note'}, name='credit_notes_list'),
    path('avoirs/nouvel/', views.DocumentCreateView.as_view(), {'side': 'purchase', 'type': 'credit_note'}, name='credit_note_create'),
    path('avoirs/<uuid:pk>/', views.DocumentDetailView.as_view(), {'side': 'purchase'}, name='credit_note_detail'),

    # --- PAIEMENTS ---
    path('paiements/echeancier/', views.PaymentScheduleView.as_view(), {'side': 'purchase'}, name='payment_schedule'),
    path('paiements/effectues/', views.PaymentListView.as_view(), {'side': 'purchase'}, name='payment_list'),
    
    # --- ACTIONS COMMUNES (modif, suppression, transitions) ---
    path('document/<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'), # Fallback générique
    path('document/<uuid:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('document/<uuid:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Actions
    path('document/<uuid:pk>/transform/<str:target_type>/', views.transform_document, name='document_transform'),
    path('document/<uuid:pk>/validate/', views.validate_document, name='document_validate'),
    path('document/<uuid:pk>/execute/', views.execute_document, name='document_execute'),
    path('document/<uuid:pk>/payment/add/', views.add_payment, name='payment_add'),
    path('document/<uuid:pk>/line/add/', views.add_line, name='line_add'),
    path('line/<uuid:pk>/delete/', views.delete_line, name='line_delete'),
    
    # API (partagée ou dupliquée)
    path('api/sku/<int:pk>/', api.get_sku_details, name='api_sku_details'),
]
