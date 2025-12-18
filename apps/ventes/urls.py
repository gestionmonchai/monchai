from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, RedirectView
from apps.clients import views as client_views
from apps.sales import views_quotes as quote_views
from . import views_orders, views_invoices, views_primeur, views_vrac

app_name = 'ventes'

def page(title, crumbs=None):
    extra = {'page_title': title}
    if crumbs is None:
        crumbs = [
            {'name': 'Ventes', 'url': '/ventes/'},
            {'name': title, 'url': None},
        ]
    extra['breadcrumb_items'] = crumbs
    return login_required(TemplateView.as_view(template_name='navigation/placeholder.html', extra_context=extra))

urlpatterns = [
    path('', page('Ventes'), name='dashboard'),
    path('devis/', login_required(quote_views.quotes_list), name='devis_list'),
    path('devis/search-ajax/', login_required(quote_views.quotes_search_ajax), name='devis_search_ajax'),
    path('devis/nouveau/', login_required(quote_views.quote_create), name='devis_new'),
    path('devis/<uuid:quote_id>/', login_required(quote_views.quote_detail), name='devis_detail'),
    path('devis/<uuid:quote_id>/modifier/', login_required(quote_views.quote_edit), name='devis_edit'),
    # Devis UX helper APIs
    path('devis/api/sales-customers/suggestions/', login_required(quote_views.sales_customers_suggestions_api), name='devis_sales_customers_suggestions'),
    path('devis/api/sales-customers/quick-create/', login_required(quote_views.sales_customers_quick_create_api), name='devis_sales_customers_quick_create'),
    path('commandes/', login_required(views_orders.orders_list), name='cmd_list'),
    path('commandes/nouveau/', login_required(views_orders.order_create), name='cmd_new'),
    path('commandes/<uuid:pk>/', login_required(views_orders.order_detail), name='cmd_detail'),

    # Clients handled by apps.clients (Redirect legacy /ventes/clients/ to /clients/)
    path('clients/', RedirectView.as_view(url='/clients/', permanent=False)),
    path('clients/<path:subpath>', RedirectView.as_view(url='/clients/%(subpath)s', permanent=False)),

    # Route tarifs supprimée - voir apps.sales monté sous /clients/
    path('factures/', login_required(views_invoices.invoices_list), name='factures_list'),
    path('factures/nouveau/', login_required(views_invoices.invoice_create), name='facture_new'),
    path('factures/<uuid:pk>/', login_required(views_invoices.invoice_detail), name='facture_detail'),
    
    # Vente en primeur
    path('primeur/', login_required(views_primeur.primeur_list), name='primeur_list'),
    path('primeur/nouveau/', login_required(views_primeur.primeur_create), name='primeur_new'),
    path('primeur/<uuid:pk>/', login_required(views_primeur.primeur_detail), name='primeur_detail'),
    
    # Vente en vrac
    path('vrac/', login_required(views_vrac.vrac_list), name='vrac_list'),
    path('vrac/nouveau/', login_required(views_vrac.vrac_create), name='vrac_new'),
    path('vrac/<uuid:pk>/', login_required(views_vrac.vrac_detail), name='vrac_detail'),
    
    path('conditions/', page('Conditions'), name='conditions_list'),
    path('expeditions/', page('Expéditions'), name='expeditions_list'),
]
