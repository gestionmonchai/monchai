from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from monchai.apps.accounts.models import Domaine


class DRMExport(models.Model):
    """Modèle pour les exports DRM (Déclaration Récapitulative Mensuelle)"""
    
    STATUS_CHOICES = [
        ("brouillon", "Brouillon"),
        ("genere", "Généré"),
        ("transmis", "Transmis"),
        ("valide", "Validé")
    ]
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="drm_exports")
    periode = models.CharField(
        "Période",
        max_length=7,  # Format YYYY-MM
        help_text="Format : YYYY-MM (ex: 2025-09)"
    )
    region = models.CharField(
        "Région",
        max_length=50,
        default="Loire",
        help_text="Région viticole pour l'export DRM"
    )
    status = models.CharField("Statut", max_length=15, choices=STATUS_CHOICES, default="brouillon")
    
    # Totaux calculés
    stock_debut_hl = models.DecimalField(
        "Stock début (HL)",
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    entrees_hl = models.DecimalField(
        "Entrées (HL)",
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    sorties_hl = models.DecimalField(
        "Sorties (HL)",
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    pertes_hl = models.DecimalField(
        "Pertes (HL)",
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    stock_fin_hl = models.DecimalField(
        "Stock fin (HL)",
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Fichiers générés
    chemin_csv = models.CharField("Chemin du CSV", max_length=255, blank=True)
    chemin_pdf = models.CharField("Chemin du PDF", max_length=255, blank=True)
    checksums = models.JSONField("Checksums", default=dict)
    data = models.JSONField("Données exportées", default=dict)
    
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Export DRM"
        verbose_name_plural = "Exports DRM"
        unique_together = [("domaine", "periode")]
        ordering = ["-periode", "-created_at"]
    
    def __str__(self):
        return f"DRM {self.domaine.nom} - {self.periode} ({self.get_status_display()})"


class DRMLigneProduit(models.Model):
    """Détail par produit/appellation pour l'export DRM"""
    
    drm_export = models.ForeignKey(DRMExport, on_delete=models.CASCADE, related_name="lignes_produits")
    appellation = models.CharField("Appellation", max_length=100)
    couleur = models.CharField(
        "Couleur",
        max_length=20,
        choices=[
            ("rouge", "Rouge"),
            ("blanc", "Blanc"),
            ("rose", "Rosé"),
            ("autre", "Autre")
        ]
    )
    
    # Volumes par type de mouvement
    stock_debut_hl = models.DecimalField(
        "Stock début (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    entrees_vendange_hl = models.DecimalField(
        "Entrées vendange (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    entrees_autres_hl = models.DecimalField(
        "Autres entrées (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    sorties_vente_hl = models.DecimalField(
        "Sorties vente (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    sorties_autres_hl = models.DecimalField(
        "Autres sorties (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    pertes_hl = models.DecimalField(
        "Pertes (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock_fin_hl = models.DecimalField(
        "Stock fin (HL)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    references_lots = models.JSONField("Références des lots", default=list)
    
    class Meta:
        verbose_name = "Ligne produit DRM"
        verbose_name_plural = "Lignes produits DRM"
        unique_together = [("drm_export", "appellation", "couleur")]
    
    def __str__(self):
        return f"{self.appellation} {self.couleur} - {self.stock_fin_hl} HL"
