from rest_framework import serializers
from .models import UserParcel


class UserParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserParcel
        fields = [
            "id",
            "tenant_id",
            "user_id",
            "parcelle_id",
            "insee",
            "section",
            "numero",
            "label",
            "harvested_pct",
            "geojson",
            "created_at",
            "updated_at",
        ]
