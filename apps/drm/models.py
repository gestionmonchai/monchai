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
    # id auto-généré par Django (BigAutoField)
    code_inao = models.CharField(max_length=32)
    code_nc = models.CharField(max_length=32)
    appellation_label = models.CharField(max_length=160, blank=True)
    color = models.CharField(max_length=16, blank=True)
    condition_text = models.TextField(blank=True)
    packaging_min_l = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    packaging_max_l = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    abv_min_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    abv_max_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("code_inao", "code_nc")
        indexes = [
            models.Index(fields=["code_inao"]),
            models.Index(fields=["code_nc"]),
            models.Index(fields=["appellation_label", "color"]),
            models.Index(fields=["packaging_max_l", "abv_max_pct"]),
        ]

    def __str__(self) -> str:
        return f"{self.code_inao} / {self.code_nc}"
