from django.db import models


class UserParcel(models.Model):
    # Multi-tenant (optionnel) + appartenance user (string id, ou FK si besoin)
    tenant_id = models.CharField(max_length=64, db_index=True, blank=True, default="")
    user_id = models.CharField(max_length=64, db_index=True)

    # Identité parcelle (idpar façon cadastre.data.gouv.fr, ex: 35238000CV0132)
    parcelle_id = models.CharField(max_length=20, db_index=True)
    insee = models.CharField(max_length=5, db_index=True)
    section = models.CharField(max_length=3)
    numero = models.CharField(max_length=4)

    label = models.CharField(max_length=160, blank=True, default="")
    harvested_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    geojson = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant_id", "user_id", "parcelle_id")]
        ordering = ["-updated_at"]
