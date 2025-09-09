from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DRMExportViewSet

router = DefaultRouter()
router.register(r'exports', DRMExportViewSet)

app_name = 'drm'

urlpatterns = [
    path('', include(router.urls)),
]
