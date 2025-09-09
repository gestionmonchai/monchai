from django.db import models
from monchai.apps.accounts.models import Domaine


class DRMExport(models.Model):
    """Modèle pour les exports DRM (Déclaration Récapitulative Mensuelle)"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="drm_exports")
    periode = models.CharField(
        "Période",
        max_length=7,  # Format YYYY-MM
        help_text="Format : YYYY-MM (ex: 2025-09)"
    )
    chemin_csv = models.CharField("Chemin du CSV", max_length=255)
    chemin_pdf = models.CharField("Chemin du PDF", max_length=255)
    checksums = models.JSONField("Checksums", default=dict)
    data = models.JSONField("Données exportées", default=dict)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    
    class Meta:
        verbose_name = "Export DRM"
        verbose_name_plural = "Exports DRM"
        unique_together = [("domaine", "periode")]
    
    def __str__(self):
        return f"DRM {self.domaine.nom} - {self.periode}"
