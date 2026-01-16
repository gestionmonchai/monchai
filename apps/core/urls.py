from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Domain mounts
    path('', include(('apps.produits.urls', 'produits'), namespace='produits')),
    path('stocks/', include(('apps.stock.urls', 'stock'), namespace='stock')),
    path('drm/', include(('apps.drm.urls', 'drm'), namespace='drm')),
    path('referentiels/', include(('apps.referentiels.urls', 'referentiels'), namespace='referentiels')),
    path('referentiels/contenants/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Contenants', 'breadcrumb_items': [
            {'name': 'Référentiels', 'url': '/referentiels/'},
            {'name': 'Contenants', 'url': None},
        ]}
    )), name='referentiels_contenants'),
    path('', include(('apps.site.urls', 'site'), namespace='site')),
]
