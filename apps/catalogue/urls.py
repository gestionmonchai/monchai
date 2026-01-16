"""
URLs pour le catalogue et la gestion des lots
Roadmap Cut #4 : Catalogue & lots
"""

from django.urls import path

from . import views, views_unified, api_views, views_grid
from django.contrib.auth.decorators import login_required
from apps.produits.views_catalog import ProductCreateView

app_name = 'catalogue'

urlpatterns = [
    # Catalogue Grid - Roadmap 25
    path('', views_grid.catalogue_grid, name='home'),
    path('recherche/', views_grid.catalogue_search_ajax, name='search_ajax'),
    
    # Catalogue détail - Roadmap 26 (canonique)
    path('<int:pk>/', views_unified.cuvee_detail, name='cuvee_detail'),
    
    # Interface unifiée produits - Même ergonomie que clients
    path('produits/', views_unified.products_dashboard, name='products_dashboard'),
    path('produits/cuvees/', views_unified.products_cuvees, name='products_cuvees'),
    path('produits/cuvees/recherche-ajax/', views_unified.cuvees_search_ajax, name='products_cuvees_search_ajax'),
    path('produits/cuvees/nouveau/', views_unified.cuvee_create, name='cuvee_create'),
    # Détail cuvée unifiée couvert par la route canonique ci-dessus
    path('produits/lots/', views_unified.products_lots, name='products_lots'),
    path('produits/lots/recherche-ajax/', views_unified.lots_search_ajax, name='products_lots_search_ajax'),
    # Alias rétrocompatible pour dashboard et anciens liens
    path('produits/lots/', views_unified.products_lots, name='lot_list'),
    path('produits/lots/nouveau/', views_unified.lot_create, name='lot_create'),
    path('produits/lots/<int:pk>/', views_unified.lot_detail, name='lot_detail'),
    path('produits/references/', views_unified.products_skus, name='products_skus'),
    path('produits/references/recherche-ajax/', views_unified.skus_search_ajax, name='products_skus_search_ajax'),
    # Remap to universal product create view (keeps URL/name stable)
    path('produits/references/nouveau/', login_required(ProductCreateView.as_view()), name='sku_create'),
    path('produits/references/<int:pk>/', views_unified.sku_detail, name='sku_detail'),
    path('produits/referentiels/', views_unified.products_referentiels, name='products_referentiels'),
    path('produits/recherche/', views_unified.products_search_ajax, name='products_search_ajax'),
    
    # API Catalogue - Roadmap 25 & 26
    path('api/catalogue/', api_views.catalogue_api, name='catalogue_api'),
    path('api/catalogue/facets/', api_views.catalogue_facets_api, name='catalogue_facets_api'),
    path('api/catalogue/<int:cuvee_id>/', api_views.catalogue_detail_api, name='catalogue_detail_api'),
    # API Parcelles (création via modal)
    path('api/plots/create/', api_views.create_vineyard_plot_api, name='create_vineyard_plot_api'),

    # --- NOUVEAU CATALOGUE (ARTICLES) ---
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/achats/', views.PurchaseArticleListView.as_view(), name='article_list_purchase'),
    path('articles/ventes/', views.SalesArticleListView.as_view(), name='article_list_sales'),
    path('articles/nouveau/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/', views.ArticleUpdateView.as_view(), name='article_detail'),
    
    path('stock/', views.InventoryListView.as_view(), name='inventory_list'),
]
