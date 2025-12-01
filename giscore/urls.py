from django.urls import path
from . import views, mvt

urlpatterns = [
    path("api/parcelles", views.parcelles, name="parcelles"),
    path("api/parcelles/<int:pk>", views.parcelle_item, name="parcelle_item"),
    path("tiles/<int:z>/<int:x>/<int:y>.mvt", mvt.tiles_mvt, name="tiles_mvt"),
]
