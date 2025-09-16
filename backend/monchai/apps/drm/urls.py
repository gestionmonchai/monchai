from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DRMExportViewSet
from .views_ui import export_list

router = DefaultRouter()
router.register(r'exports', DRMExportViewSet)

app_name = 'drm'

# URLs pour l'API
api_urlpatterns = [
    path('', include(router.urls)),
]

# URLs pour l'interface utilisateur
ui_urlpatterns = [
    path('exports/', export_list, name='export_list'),
]

urlpatterns = api_urlpatterns + ui_urlpatterns
