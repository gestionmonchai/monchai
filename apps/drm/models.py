from __future__ import annotations
from django.db import models
from django.utils import timezone
import uuid
from apps.accounts.models import Organization


class DRMLine(models.Model):
    TYPE_CHOICES = (
        ("entree", "Entrée"),
        ("mise", "Mise"),
        ("sortie", "Sortie"),
        ("perte", "Perte"),
        ("vrac", "Vrac"),
    )

    # id auto-généré par Django (BigAutoField)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2)
    ref_kind = models.CharField(max_length=32)
    ref_id = models.BigIntegerField(null=True, blank=True)
    campagne = models.CharField(max_length=9)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date", "-created_at")
        indexes = [
            models.Index(fields=["organization", "date", "type"]),
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.type} {self.volume_l} L"


class INAOCode(models.Model):
    """
    Codes vinicoles interprofessionnels (INAO/Douanes).
    Source: https://www.douane.gouv.fr - Codes vinicoles interprofessionnels 2024
    """
    CATEGORIE_CHOICES = [
        ('aop_blanc', 'AOP Blancs'),
        ('aop_rouge_rose', 'AOP Rouges et Rosés'),
        ('igp_blanc', 'IGP Blancs'),
        ('igp_rouge_rose', 'IGP Rouges et Rosés'),
        ('autre', 'Autre'),
    ]
    
    # id auto-généré par Django (BigAutoField)
    code_inao = models.CharField(max_length=32, verbose_name="Code vinicole interprofessionnel")
    code_nc = models.CharField(max_length=32, verbose_name="Nomenclature combinée (NC)")
    appellation_label = models.CharField(max_length=255, blank=True, verbose_name="Libellé appellation")
    categorie = models.CharField(max_length=50, blank=True, verbose_name="Catégorie")
    categorie_code = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='autre', verbose_name="Type")
    region = models.CharField(max_length=100, blank=True, verbose_name="Région viticole")
    color = models.CharField(max_length=16, blank=True, verbose_name="Couleur")
    date_validite = models.DateField(null=True, blank=True, verbose_name="Date début validité")
    contenance = models.CharField(max_length=20, blank=True, verbose_name="Contenance", help_text="Ex: <=2 (litres)")
    condition_text = models.TextField(blank=True, verbose_name="Conditions")
    packaging_min_l = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    packaging_max_l = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    abv_min_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    abv_max_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("appellation_label", "code_inao")
        verbose_name = "Code INAO"
        verbose_name_plural = "Codes INAO"
        indexes = [
            models.Index(fields=["code_inao"]),
            models.Index(fields=["code_nc"]),
            models.Index(fields=["appellation_label"]),
            models.Index(fields=["categorie_code", "region"]),
        ]

    def __str__(self) -> str:
        return f"{self.appellation_label} ({self.code_inao})"
