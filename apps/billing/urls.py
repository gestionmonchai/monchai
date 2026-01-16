from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

app_name = 'compta'

urlpatterns = [
    path('', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Comptabilité', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': None},
        ]}
    )), name='dashboard'),
    path('stock/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': "Écritures stock", 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Écritures stock', 'url': None},
        ]}
    )), name='stock'),
    path('ventes/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Ventes (CA, TVA)', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Ventes (CA, TVA)', 'url': None},
        ]}
    )), name='ventes'),
    path('exports/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Exports (Sage/Quadratus/CSV)', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Exports (Sage/Quadratus/CSV)', 'url': None},
        ]}
    )), name='exports'),
    path('achats/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Achats Comptables', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Achats', 'url': None},
        ]}
    )), name='achats'),
    path('plan-comptable/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Plan Comptable', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Plan Comptable', 'url': None},
        ]}
    )), name='plan_comptable'),
    path('journaux/', login_required(TemplateView.as_view(
        template_name='navigation/placeholder.html',
        extra_context={'page_title': 'Journaux', 'breadcrumb_items': [
            {'name': 'Comptabilité', 'url': '/comptabilite/'},
            {'name': 'Journaux', 'url': None},
        ]}
    )), name='journaux'),
]
