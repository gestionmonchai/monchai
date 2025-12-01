from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # API endpoints (no conflict with existing urbanisme endpoints)
    path("api/parcel/by-id", views.api_parcel_by_id),
    path("api/parcel/by-ref", views.api_parcel_by_ref),
    path("api/me/parcels", views.my_parcels),
    path("api/me/parcels/<int:pk>", views.my_parcel_item),

    # Viewer page
    path("cadastre/viewer/", TemplateView.as_view(template_name="cadastre_app/viewer.html")),
]
