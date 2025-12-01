from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from apps.referentiels import views as ref_views

app_name = 'ref'

# Placeholder for formats until implemented
formats_view = login_required(TemplateView.as_view(
    template_name='navigation/placeholder.html',
    extra_context={'page_title': 'Formats', 'breadcrumb_items': [
        {'name': 'Référentiels', 'url': '/ref/'},
        {'name': 'Formats', 'url': None},
    ]}
))

urlpatterns = [
    path('ref/unites/', login_required(ref_views.unite_list), name='unites_list'),
    path('ref/formats/', formats_view, name='formats_list'),
    path('ref/cepages/', login_required(ref_views.cepage_list), name='cepages_list'),
    path('ref/appellations/', login_required(ref_views.appellation_list if hasattr(ref_views, 'appellation_list') else TemplateView.as_view(template_name='navigation/placeholder.html')), name='appellations_list'),
]
