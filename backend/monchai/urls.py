"""
URL configuration for monchai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

# View pour healthcheck
from django.http import JsonResponse
def healthcheck(request):
    return JsonResponse({"status": "ok", "db": True, "version": "1.0.0"})

# Simple API root view
class APIRoot(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            "message": "Bienvenue sur l'API Mon Chai",
            "version": "1.0.0",
            "documentation": "Documentation à venir"
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # UI endpoints (main app)
    path('', include('monchai.apps.core.urls')),
    
    # API endpoints
    path('api/', APIRoot.as_view(), name='api-root'),
    path('api/auth/', include('monchai.apps.accounts.urls')),
    path('api/core/', include(('monchai.apps.core.urls', 'core-api'), namespace='core-api')),
    path('api/sales/', include('monchai.apps.sales.urls')),
    path('api/drm/', include('monchai.apps.drm.urls')),
    
    # Healthcheck
    path('healthz/', healthcheck, name='healthcheck'),
]
