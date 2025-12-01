from django.db import models


class Parcelle(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=120)
    geojson = models.JSONField()  # Feature Polygon/MultiPolygon
    area_m2 = models.FloatField(null=True, blank=True)
    perimeter_m = models.FloatField(null=True, blank=True)
    lod1 = models.JSONField(null=True, blank=True)
    lod2 = models.JSONField(null=True, blank=True)
    lod3 = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tenant_id"])]
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant_id})"
