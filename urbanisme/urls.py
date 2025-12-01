from django.urls import path
from . import views

urlpatterns = [
    path("api/cadastre/parcel", views.parcel, name="urbanisme_parcel"),
    path("api/plu/zones", views.plu_zones, name="urbanisme_plu_zones"),
    path("api/cadastre/wfs", views.cadastre_wfs, name="urbanisme_cadastre_wfs"),  # optionnel
    path("embed/cadastre-wms", views.embed_cadastre_wms, name="embed_cadastre_wms"),
    path("api/geocode", views.geocode, name="urbanisme_geocode"),
    path("urbanisme/viewer", views.viewer, name="urbanisme_viewer"),
]
