import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ParcelleOperationType(models.Model):
    """
    Référentiel d'opérations agronomiques affichées dans le journal.
    Ex : taille, traitement, travail_sol, palissage, effeuillage, fertilisation, irrigation, autre
    """
    code = models.SlugField(primary_key=True)
    label = models.CharField(max_length=80)
    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["order", "label"]

    def __str__(self) -> str:
        return f"{self.label} ({self.code})"


class ParcelleJournalEntry(models.Model):
    """Ligne de journal en lecture seule (écrite par services/signaux)."""
    # id auto-généré par Django (BigAutoField)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)
    parcelle = models.ForeignKey('referentiels.Parcelle', on_delete=models.CASCADE, related_name='journal')

    # Typologie d'opération
    op_type = models.ForeignKey(ParcelleOperationType, on_delete=models.PROTECT)

    # Fenêtre temporelle
    date = models.DateField()
    date_end = models.DateField(null=True, blank=True)

    # Surface et rangs concernés (optionnel)
    surface_ha = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    rangs = models.CharField(max_length=120, blank=True)

    # Détails agronomiques
    resume = models.CharField(max_length=240, blank=True)
    notes = models.TextField(blank=True)

    # Pièces jointes (ex: photo intervention, facture)
    attachments = models.JSONField(default=list, blank=True)  # [{name,url},...]

    # Coûts analytiques (snapshot)
    cout_mo_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cout_matiere_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cout_total_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Provenance (lien vers l’objet source)
    source_ct = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    source_id = models.CharField(max_length=64, blank=True)
    source = GenericForeignKey('source_ct', 'source_id')

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'parcelle', 'date']),
            models.Index(fields=['organization', 'op_type']),
        ]
        ordering = ['-date', '-created_at']

    def __str__(self) -> str:
        return f"{self.parcelle} - {self.op_type.label} - {self.date}"
