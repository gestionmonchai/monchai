from django.urls import path
from django.views.generic import TemplateView

app_name = 'site'

urlpatterns = [
    path('cave/cuvees/<slug:slug>/', TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={
            'page_title': 'Cuvée publique',
            'breadcrumb_items': [
                {'name': 'La Cave', 'url': '/cave/'},
                {'name': 'Cuvée', 'url': None},
            ]
        }
    ), name='cuvee_public'),
]
