from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, DomaineViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'domaines', DomaineViewSet)
router.register(r'profiles', ProfileViewSet)

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
]
