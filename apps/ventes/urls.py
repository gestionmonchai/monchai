from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
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
    path('ventes/', page('Ventes'), name='dashboard'),
    path('ventes/devis/', login_required(quote_views.quotes_list), name='devis_list'),
    path('ventes/devis/search-ajax/', login_required(quote_views.quotes_search_ajax), name='devis_search_ajax'),
    path('ventes/devis/nouveau/', login_required(quote_views.quote_create), name='devis_new'),
    path('ventes/devis/<uuid:quote_id>/', login_required(quote_views.quote_detail), name='devis_detail'),
    path('ventes/devis/<uuid:quote_id>/modifier/', login_required(quote_views.quote_edit), name='devis_edit'),
    # Devis UX helper APIs
    path('ventes/devis/api/sales-customers/suggestions/', login_required(quote_views.sales_customers_suggestions_api), name='devis_sales_customers_suggestions'),
    path('ventes/devis/api/sales-customers/quick-create/', login_required(quote_views.sales_customers_quick_create_api), name='devis_sales_customers_quick_create'),
    path('ventes/commandes/', login_required(views_orders.orders_list), name='cmd_list'),
    path('ventes/commandes/nouveau/', login_required(views_orders.order_create), name='cmd_new'),
    path('ventes/commandes/<uuid:pk>/', login_required(views_orders.order_detail), name='cmd_detail'),

    path('ventes/clients/', login_required(client_views.customers_list), name='clients_list'),
    path('ventes/clients/nouveau/', login_required(client_views.customer_create), name='client_new'),
    path('ventes/clients/<uuid:customer_id>/', login_required(client_views.customer_detail), name='client_detail'),
    path('ventes/clients/<uuid:customer_id>/modifier/', login_required(client_views.customer_edit), name='client_edit'),
    path('ventes/clients/export/', login_required(client_views.customers_export), name='clients_export'),

    # Route tarifs supprimée - voir apps.sales monté sous /clients/
    path('ventes/factures/', login_required(views_invoices.invoices_list), name='factures_list'),
    path('ventes/factures/nouveau/', login_required(views_invoices.invoice_create), name='facture_new'),
    path('ventes/factures/<uuid:pk>/', login_required(views_invoices.invoice_detail), name='facture_detail'),
    
    # Vente en primeur
    path('ventes/primeur/', login_required(views_primeur.primeur_list), name='primeur_list'),
    path('ventes/primeur/nouveau/', login_required(views_primeur.primeur_create), name='primeur_new'),
    path('ventes/primeur/<uuid:pk>/', login_required(views_primeur.primeur_detail), name='primeur_detail'),
    
    # Vente en vrac
    path('ventes/vrac/', login_required(views_vrac.vrac_list), name='vrac_list'),
    path('ventes/vrac/nouveau/', login_required(views_vrac.vrac_create), name='vrac_new'),
    path('ventes/vrac/<uuid:pk>/', login_required(views_vrac.vrac_detail), name='vrac_detail'),
    
    path('ventes/conditions/', page('Conditions'), name='conditions_list'),
    path('ventes/expeditions/', page('Expéditions'), name='expeditions_list'),
]
