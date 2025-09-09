from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ParcelleViewSet, VendangeViewSet, CuveViewSet,
    LotViewSet, MouvementViewSet, BouteilleLotViewSet
)

router = DefaultRouter()
router.register(r'parcelles', ParcelleViewSet)
router.register(r'vendanges', VendangeViewSet)
router.register(r'cuves', CuveViewSet)
router.register(r'lots', LotViewSet)
router.register(r'mouvements', MouvementViewSet)
router.register(r'bouteille_lots', BouteilleLotViewSet)

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
]
