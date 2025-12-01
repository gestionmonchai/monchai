from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from apps.drm.views import DashboardView, BrouillonView, ExportView

app_name = 'stock_drm'

# Expose two pattern lists for inclusion with separate namespaces


def page(title, crumbs=None):
    extra = {'page_title': title}
    if crumbs is None:
        crumbs = [
            {'name': 'Stock & DRM', 'url': '/stock/'},
            {'name': title, 'url': None},
        ]
    extra['breadcrumb_items'] = crumbs
    return login_required(TemplateView.as_view(template_name='navigation/placeholder.html', extra_context=extra))

stock_urlpatterns = [
    path('stock/mouvements/', page('Mouvements de stock'), name='mov_list'),
    path('stock/inventaire/', page('Inventaire'), name='inv_list'),
]

drm_urlpatterns = [
    path('stock/drm/', DashboardView.as_view(), name='dashboard'),
    path('stock/drm/brouillon/', BrouillonView.as_view(), name='brouillon'),
    path('stock/drm/export/', ExportView.as_view(), name='export'),
]
