from django.urls import path, include
from django.views.generic import RedirectView
from . import views, api
from apps.partners import views as partners_views
from apps.referentiels import views_produits

app_name = 'achats'

urlpatterns = [
    # --- TABLEAU DE BORD ---
    path('tableau-de-bord/', views.dashboard, {'side': 'purchase'}, name='dashboard'),
    
    # --- PRODUITS (CATALOGUE ACHAT) - Pointe vers base commune /referentiels/produits/ ---
    path('produits/', views_produits.produit_list, {'usage_filter': 'achat'}, name='produit_list'),
    path('produits/nouveau/', views_produits.produit_create, {'usage_preset': 'achat'}, name='produit_create'),
    path('produits/<int:pk>/', views_produits.produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/', views_produits.produit_update, name='produit_update'),

    # --- FOURNISSEURS (nouvelle app partners) ---
    path('fournisseurs/', include('apps.partners.urls_achats')),


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
    path('document/<uuid:pk>/modifier/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('document/<uuid:pk>/supprimer/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Actions
    path('document/<uuid:pk>/transformer/<str:target_type>/', views.transform_document, name='document_transform'),
    path('document/<uuid:pk>/valider/', views.validate_document, name='document_validate'),
    path('document/<uuid:pk>/executer/', views.execute_document, name='document_execute'),
    path('document/<uuid:pk>/paiement/ajouter/', views.add_payment, name='payment_add'),
    path('document/<uuid:pk>/ligne/ajouter/', views.add_line, name='line_add'),
    path('ligne/<uuid:pk>/supprimer/', views.delete_line, name='line_delete'),
    
    # API (partagée ou dupliquée)
    path('api/sku/<int:pk>/', api.get_sku_details, name='api_sku_details'),
]
