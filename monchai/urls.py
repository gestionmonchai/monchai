"""
URL configuration for Mon Chai project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.accounts.views import dashboard_placeholder, landing_page
from giscore.views import embed_parcelles

# Vue pour rediriger la racine vers landing ou dashboard
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return redirect('/monchai/')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('monchai/', landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
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
    path('clients/', include('apps.clients.urls')),
    path('viticulture/', include('apps.viticulture.urls')),
    # Sales app (grilles tarifaires sous /clients/tarifs/)
    path('clients/', include('apps.sales.urls')),
    # Production app (namespaced include)
    path('production/', include(('apps.production.urls', 'production'), namespace='production')),
    # Dashboard placeholder
    path('dashboard/', dashboard_placeholder, name='dashboard'),
    # Embed Parcelles viewer
    path('embed/parcelles', embed_parcelles, name='embed_parcelles'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
