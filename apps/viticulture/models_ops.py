"""
Modèles d'opérations viticoles par parcelle (journal de parcelle)
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import BaseViticultureModel


class ParcelleOperation(BaseViticultureModel):
    """Journal des opérations viticoles sur une parcelle.
    Ex: taille, traitement, palissage, rognage, travail du sol, observation, etc.
    """
    TYPE_CHOICES = [
        ("taille", "Taille"),
        ("traitement", "Traitement phyto"),
        ("palissage", "Palissage / Liage"),
        ("rognage", "Rognage"),
        ("effeuillage", "Effeuillage"),
        ("travail_sol", "Travail du sol"),
        ("fertilisation", "Fertilisation / Amendements"),
        ("irrigation", "Irrigation"),
        ("observation", "Observation"),
        ("vendange", "Vendange"),
        ("autre", "Autre"),
    ]

    parcelle = models.ForeignKey(
        'referentiels.Parcelle',
        on_delete=models.PROTECT,
        related_name='operations',
        help_text="Parcelle concernée"
    )
    operation_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateField(default=timezone.now)
    label = models.CharField(max_length=120, blank=True, help_text="Intitulé court")
    produit = models.CharField(max_length=120, blank=True, help_text="Produit utilisé (si traitement)")
    dose = models.CharField(max_length=60, blank=True, help_text="Dose/ha ou quantité")
    duree_h = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Durée (heures)")
    cout_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Coût (€)")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Opération de parcelle"
        verbose_name_plural = "Opérations de parcelle"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'parcelle', 'date']),
            models.Index(fields=['organization', 'operation_type', 'date']),
        ]

    def __str__(self) -> str:
        t = dict(self.TYPE_CHOICES).get(self.operation_type, self.operation_type)
        return f"{t} - {self.parcelle} - {self.date}"

    def clean(self):
        try:
            if self.parcelle and self.organization and getattr(self.parcelle, 'organization_id', None) != self.organization_id:
                raise ValidationError("La parcelle doit appartenir à la même organisation que l'opération.")
        except Exception:
            # En cas d'objet partiel lors de migrations
            pass
