from rest_framework import serializers
from .models import Parcelle


class ParcelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcelle
        fields = [
            "id",
            "tenant_id",
            "name",
            "geojson",
            "area_m2",
            "perimeter_m",
            "lod1",
            "lod2",
            "lod3",
            "created_at",
        ]
