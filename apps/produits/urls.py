"""
URLs pour l'app produits (front-office)
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from apps.catalogue import views_unified as cat_views
from .views import (
    LotCommercialListView,
    LotCommercialDetailView,
    htmx_calc_units,
)
from .views_catalog import (
    ProductListView,
    ProductCreateView,
    ProductDetailView,
    ProductUpdateView,
    SKUUpdateView,
    PurchaseArticleCreateView,
    PurchaseArticleSuccessView,
    BridgePurchaseToSalesView,
    SalesArticleCreateView,
    SalesArticleSuccessView,
    BridgeSalesToPurchaseView,
)
from . import views_catalog
from .views import products_suggestions_api

app_name = 'produits'

def page(title, crumbs=None):
    extra = {'page_title': title, 'breadcrumb_items': crumbs or [
        {'name': 'Produits', 'url': '/produits/'},
        {'name': title, 'url': None},
    ]}
    return login_required(TemplateView.as_view(template_name='navigation/placeholder.html', extra_context=extra))

urlpatterns = [
    # Page principale des produits (legacy)
    path('', views.products_list, name='products_list'),

    # Cuvées
    path('produits/cuvees/', login_required(cat_views.products_cuvees), name='cuvees_list'),
    path('produits/cuvees/nouveau/', login_required(cat_views.cuvee_create), name='cuvee_new'),
    path('produits/cuvees/<int:pk>/', login_required(cat_views.cuvee_detail), name='cuvee_detail'),

    # SKUs (Références)
    path('produits/references/', login_required(cat_views.products_skus), name='skus_list'),
    # Remap nouveau to universal ProductCreateView (fiche à volets)
    path('produits/references/nouveau/', login_required(ProductCreateView.as_view()), name='sku_new'),
    path('produits/references/<int:pk>/', login_required(cat_views.sku_detail), name='sku_detail'),

    # Nouveaux flux de création (Workflow Achat/Vente)
    path('produits/achats/nouveau/', login_required(PurchaseArticleCreateView.as_view()), name='purchase_new'),
    path('produits/achats/<slug:slug>/succes/', login_required(PurchaseArticleSuccessView.as_view()), name='purchase_success'),
    path('produits/achats/<slug:slug>/vendre/', login_required(BridgePurchaseToSalesView.as_view()), name='bridge_purchase_to_sales'),
    
    path('produits/ventes/nouveau/', login_required(SalesArticleCreateView.as_view()), name='sales_new'),
    path('produits/ventes/<slug:slug>/succes/', login_required(SalesArticleSuccessView.as_view()), name='sales_success'),
    path('produits/ventes/<slug:slug>/acheter/', login_required(BridgeSalesToPurchaseView.as_view()), name='bridge_sales_to_purchase'),

    # Partials HTMX (universal product form)
    path('produits/formulaire/panneaux/', views_catalog.product_panels_partial, name='panels'),
    path('produits/formulaire/source/', views_catalog.product_source_partial, name='source_partial'),
    path('produits/formulaire/source/cuvee/ajouter/', views_catalog.product_source_cuvee_add, name='source_cuvee_add'),
    path('produits/formulaire/source/cuvee/supprimer/<int:row_id>/', views_catalog.product_source_cuvee_del, name='source_cuvee_del'),

    # Lots commerciaux
    path('produits/lots-commerciaux/', LotCommercialListView.as_view(), name='lots_com_list'),
    path('produits/lots-commerciaux/<uuid:pk>/', LotCommercialDetailView.as_view(), name='lot_com_detail'),

    # HTMX endpoint (Mise step 2 calc)
    path('produits/api/htmx/calcul/', htmx_calc_units, name='htmx_calc_units'),

    # API AJAX pour recherche temps réel (legacy)
    path('recherche-ajax/', views.products_search_ajax, name='products_search_ajax'),
    # Suggestions API for autocomplete
    path('produits/api/suggestions/', login_required(products_suggestions_api), name='products_suggestions_api'),

    # Catalogue produits (nouveau)
    path('produits/catalogue/', login_required(ProductListView.as_view()), name='catalog_list'),
    path('produits/catalogue/nouveau/', login_required(ProductCreateView.as_view()), name='product_new'),
    path('produits/catalogue/<slug:slug>/', login_required(ProductDetailView.as_view()), name='product_detail'),
    path('produits/catalogue/<slug:slug>/modifier/', login_required(ProductUpdateView.as_view()), name='product_edit'),
    path('produits/references/<int:pk>/modifier/', login_required(SKUUpdateView.as_view()), name='sku_edit'),
]
