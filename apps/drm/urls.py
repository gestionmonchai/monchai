from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .views import DashboardView, BrouillonView, ExportView, INAOCodeSearchApiView, INAOListView

app_name = 'drm'

urlpatterns = [
    # Dashboard / Landing
    path('', DashboardView.as_view(), name='dashboard'),

    # CRD / Code INAO
    path('crd/', login_required(TemplateView.as_view(template_name='drm/crd.html', extra_context={
        'page_title': 'CRD / Code INAO',
        'breadcrumb_items': [
            {'name': 'DRM', 'url': '/drm/'},
            {'name': 'CRD / Code INAO', 'url': None},
        ]
    })), name='crd'),

    # Codes INAO: DB-backed list with filters
    path('inao/', INAOListView.as_view(), name='inao'),

    # Editor (period optional via query or path)
    path('editer/', BrouillonView.as_view(), name='editor_current'),
    path('editer/<str:period>/', BrouillonView.as_view(), name='editor'),

    # API: INAO codes search (JSON)
    path('api/inao/', INAOCodeSearchApiView.as_view(), name='inao_api'),

    # Export (period optional)
    path('export/', ExportView.as_view(), name='export_current'),
    path('export/<str:period>/', ExportView.as_view(), name='export'),
]
