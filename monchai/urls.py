"""
URL configuration for Mon Chai project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.accounts.views import dashboard_placeholder, landing_page
from apps.accounts import views_settings as account_settings_views
from giscore.views import embed_parcelles

# Vue pour rediriger la racine vers landing ou dashboard
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/tableau-de-bord/')
    return redirect('/monchai/')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('monchai/', landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path('parametres/facturation/', account_settings_views.billing_settings, name='billing_settings_pretty'),
    path('parametres/general/', account_settings_views.general_settings, name='general_settings_pretty'),
    # Core aggregator: mount once without namespace to expose top-level app namespaces
    path('', include('apps.core.urls')),
    # Cadastre clone app (MapLibre + Mes parcelles)
    path('', include('cadastre_app.urls')),
    # Urbanisme API & embeds
    path('', include('urbanisme.urls')),
    # Auth routes (invariant technique: /auth/*)
    path('auth/', include('apps.accounts.urls')),
    # API routes (invariant technique: /api/auth/*)
    path('api/auth/', include('apps.accounts.api_urls', namespace='api_auth')),
    # AI Help API
    path('api/', include('apps.ai.urls', namespace='ai')),
    # GIS core API and tiles
    path('', include('giscore.urls')),
    # Apps
    path('onboarding/', include('apps.onboarding.urls')),
    path('catalogue/', include('apps.catalogue.urls')),
    # Partners (Contacts unifiés) - dans référentiels
    path('referentiels/contacts/', include('apps.partners.urls', namespace='partners')),
    path('viticulture/', include('apps.viticulture.urls')),
    path('comptabilite/', include('apps.billing.urls', namespace='compta')),
    
    # New Commerce App (Achats/Ventes unifiés - Refonte URL 2025)
    # path('commerce/', include('apps.commerce.urls', namespace='commerce')), # DEPRECATED
    
    path('achats/', include('apps.commerce.urls_achats', namespace='achats')),
    path('ventes/', include('apps.commerce.urls_ventes', namespace='ventes')),
    
    # Sales app (legacy - integrated into ventes)
    # path('sales/', include('apps.sales.urls')),
    
    # Production app (namespaced include)
    path('production/', include(('apps.production.urls', 'production'), namespace='production')),
    # Dashboard placeholder
    path('tableau-de-bord/', dashboard_placeholder, name='dashboard'),
    # Embed Parcelles viewer
    path('embed/parcelles', embed_parcelles, name='embed_parcelles'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
