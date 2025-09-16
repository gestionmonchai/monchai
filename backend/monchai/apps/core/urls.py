from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ParcelleViewSet, VendangeViewSet, CuveViewSet,
    LotViewSet, MouvementViewSet, BouteilleLotViewSet
)
from .views_ui import (
    dashboard, vendange_wizard, mouvement_inter_cuves, mise_en_bouteille_form,
    parcelles_list, vendanges_list, cuves_list, mouvements_list, valider_mouvement
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
    # API endpoints
    path('api/', include(router.urls)),
    
    # UI endpoints
    path('', dashboard, name='dashboard'),
    path('parcelles/', parcelles_list, name='parcelles'),
    path('vendanges/', vendanges_list, name='vendanges'),
    path('cuves/', cuves_list, name='cuves'),
    path('mouvements/', mouvements_list, name='mouvements'),
    
    # HTMX endpoints
    path('vendange/wizard/', vendange_wizard, name='vendange_wizard'),
    path('mouvement/inter-cuves/', mouvement_inter_cuves, name='mouvement_inter_cuves'),
    path('mise-en-bouteille/', mise_en_bouteille_form, name='mise_en_bouteille_form'),
    path('mouvement/<int:mouvement_id>/valider/', valider_mouvement, name='valider_mouvement'),
]
