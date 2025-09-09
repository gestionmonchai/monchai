from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProduitViewSet, ClientViewSet, CommandeViewSet,
    LigneCommandeViewSet, FactureViewSet, PaiementViewSet
)

router = DefaultRouter()
router.register(r'produits', ProduitViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'commandes', CommandeViewSet)
router.register(r'lignes_commande', LigneCommandeViewSet)
router.register(r'factures', FactureViewSet)
router.register(r'paiements', PaiementViewSet)

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
]
