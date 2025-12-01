from django.urls import path, include, re_path
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.decorators import login_required

# Optional legacy includes removed in favor of explicit apps; keep only redirects below

urlpatterns = [
    # New domain mounts
    path('', include(('apps.produits.urls', 'produits'), namespace='produits')),
    path('', include(('apps.ventes.urls', 'ventes'), namespace='ventes')),
    path('stocks/', include(('apps.stock.urls', 'stock'), namespace='stock')),
    path('drm/', include(('apps.drm.urls', 'drm'), namespace='drm')),
    path('referentiels/', include(('apps.referentiels.urls', 'referentiels'), namespace='referentiels')),
    # Optional placeholders aligning with header
    path('referentiels/contenants/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Contenants', 'breadcrumb_items': [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Contenants', 'url': None},
        ]}
    )), name='referentiels_contenants'),
    path('compta/stock/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': "Écritures stock", 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/compta/'},
            {'name': 'Écritures stock', 'url': None},
        ]}
    )), name='compta_stock'),
    path('compta/ventes/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Ventes (CA, TVA)', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/compta/'},
            {'name': 'Ventes (CA, TVA)', 'url': None},
        ]}
    )), name='compta_ventes'),
    path('compta/exports/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Exports (Sage/Quadratus/CSV)', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/compta/'},
            {'name': 'Exports (Sage/Quadratus/CSV)', 'url': None},
        ]}
    )), name='compta_exports'),
    path('', include(('apps.site.urls', 'site'), namespace='site')),

    # 301 redirects from major old URLs to new structure (must be before old includes in root urls)
    # Catalogue → Produits (Cuvées)
    re_path(r'^catalogue/produits/?$',
            RedirectView.as_view(url='/produits/cuvees/', permanent=True)),
    re_path(r'^catalogue/produits/cuvees/nouveau/?$',
            RedirectView.as_view(url='/produits/cuvees/nouveau/', permanent=True)),
    re_path(r'^catalogue/produits/cuvees/?$',
            RedirectView.as_view(url='/produits/cuvees/', permanent=True)),
    # SKUs
    re_path(r'^catalogue/produits/skus/nouveau/?$',
            RedirectView.as_view(url='/produits/skus/nouveau/', permanent=True)),
    re_path(r'^catalogue/produits/skus/?$',
            RedirectView.as_view(url='/produits/skus/', permanent=True)),
    # Lots techniques (production)
    re_path(r'^catalogue/produits/lots/nouveau/?$',
            RedirectView.as_view(url='/production/lots-techniques/nouveau/', permanent=True)),
    re_path(r'^catalogue/produits/lots/?$',
            RedirectView.as_view(url='/production/lots-techniques/', permanent=True)),

    # Clients (legacy) → Ventes/Clients
    re_path(r'^clients/?$', RedirectView.as_view(url='/ventes/clients/', permanent=True)),
    re_path(r'^clients/nouveau/?$', RedirectView.as_view(url='/ventes/clients/nouveau/', permanent=True)),
    re_path(r'^clients/(?P<cid>[0-9a-f\-]{36})/?$',
            RedirectView.as_view(url='/ventes/clients/%(cid)s/', permanent=True)),
    re_path(r'^clients/(?P<cid>[0-9a-f\-]{36})/modifier/?$',
            RedirectView.as_view(url='/ventes/clients/%(cid)s/', permanent=True)),
    re_path(r'^clients/tarifs/?$', RedirectView.as_view(url='/ventes/tarifs/', permanent=True)),
    re_path(r'^clients/conditions/?$', RedirectView.as_view(url='/ventes/conditions/', permanent=True)),

    # Legacy redirects: old /stock/* → new /stocks/* and DRM paths
    re_path(r'^stocks/?$', RedirectView.as_view(url='/stocks/', permanent=True)),
    re_path(r'^stock/mouvements/?$', RedirectView.as_view(url='/stocks/mouvements/', permanent=True)),
    re_path(r'^stock/inventaire/?$', RedirectView.as_view(url='/stocks/inventaires/', permanent=True)),
    re_path(r'^stock/transferts/?$', RedirectView.as_view(url='/stocks/transferts/', permanent=True)),
    re_path(r'^stock/drm/?$', RedirectView.as_view(url='/drm/', permanent=True)),
    re_path(r'^stock/drm/brouillon/?$', RedirectView.as_view(url='/drm/editer/', permanent=True)),
    re_path(r'^stock/drm/export/?$', RedirectView.as_view(url='/drm/export/', permanent=True)),

    
    
    re_path(r'^ref/unites/add/?$', RedirectView.as_view(url='/referentiels/unites/nouvelle/', permanent=True)),
    re_path(r'^ref/unites/(?P<pk>\d+)/edit/?$', RedirectView.as_view(url='/referentiels/unites/%(pk)s/modifier/', permanent=True)),
    re_path(r'^ref/unites/(?P<pk>\d+)/?$', RedirectView.as_view(url='/referentiels/unites/%(pk)s/', permanent=True)),
    re_path(r'^ref/unites/?$', RedirectView.as_view(url='/referentiels/unites/', permanent=True)),

    
    re_path(r'^ref/cepages/add/?$', RedirectView.as_view(url='/referentiels/cepages/nouveau/', permanent=True)),
    re_path(r'^ref/cepages/(?P<pk>\d+)/edit/?$', RedirectView.as_view(url='/referentiels/cepages/%(pk)s/modifier/', permanent=True)),
    re_path(r'^ref/cepages/(?P<pk>\d+)/?$', RedirectView.as_view(url='/referentiels/cepages/%(pk)s/', permanent=True)),
    re_path(r'^ref/cepages/?$', RedirectView.as_view(url='/referentiels/cepages/', permanent=True)),

    
    # Fix user reported 404s
    re_path(r'^parcelles/nouveau/?$', RedirectView.as_view(url='/referentiels/parcelles/nouvelle/', permanent=True)),
    re_path(r'^parcelles/(?P<pk>\d+)/?$', RedirectView.as_view(url='/referentiels/parcelles/%(pk)s/', permanent=True)),
    re_path(r'^parcelles/?$', RedirectView.as_view(url='/referentiels/parcelles/', permanent=True)),

    re_path(r'^ref/parcelles/add/?$', RedirectView.as_view(url='/referentiels/parcelles/nouvelle/', permanent=True)),
    re_path(r'^ref/parcelles/(?P<pk>\d+)/edit/?$', RedirectView.as_view(url='/referentiels/parcelles/%(pk)s/modifier/', permanent=True)),
    re_path(r'^ref/parcelles/(?P<pk>\d+)/?$', RedirectView.as_view(url='/referentiels/parcelles/%(pk)s/', permanent=True)),
    re_path(r'^ref/parcelles/?$', RedirectView.as_view(url='/referentiels/parcelles/', permanent=True)),

    
    re_path(r'^ref/entrepots/add/?$', RedirectView.as_view(url='/referentiels/entrepots/nouveau/', permanent=True)),
    re_path(r'^ref/entrepots/(?P<pk>\d+)/edit/?$', RedirectView.as_view(url='/referentiels/entrepots/%(pk)s/modifier/', permanent=True)),
    re_path(r'^ref/entrepots/(?P<pk>\d+)/?$', RedirectView.as_view(url='/referentiels/entrepots/%(pk)s/', permanent=True)),
    re_path(r'^ref/entrepots/?$', RedirectView.as_view(url='/referentiels/entrepots/', permanent=True)),

    
    re_path(r'^ref/import/?$', RedirectView.as_view(url='/referentiels/import/', permanent=True)),

    
    re_path(r'^ref/(?P<rest>.*)$', RedirectView.as_view(url='/referentiels/%(rest)s', permanent=True)),
]
