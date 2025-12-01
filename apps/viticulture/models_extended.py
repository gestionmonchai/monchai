"""
Modèles étendus complémentaires (Lot) pour la viticulture.
Note: Les modèles CuveeDetail et associés sont définis dans models.py
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import BaseViticultureModel, Lot, Cuvee, Vintage


# ============================================================================
# MODÈLES ÉTENDUS POUR FICHE LOT COMPLÈTE
# ============================================================================

class LotDetail(BaseViticultureModel):
    """
    Détails étendus d'un lot - fiche technique complète
    """

    lot = models.OneToOneField(
        Lot,
        on_delete=models.CASCADE,
        related_name='detail',
        help_text="Lot de référence"
    )

    # Identification avancée
    millesime_majoritaire = models.ForeignKey(
        Vintage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Millésime majoritaire du lot"
    )

    # Localisation & contenants
    emplacement_rangee = models.CharField(max_length=50, blank=True)
    emplacement_travee = models.CharField(max_length=50, blank=True)
    emplacement_niveau = models.CharField(max_length=50, blank=True)
    temperature_cible_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    ouillage_requis = models.BooleanField(default=False)
    ouillage_periodicite_jours = models.PositiveIntegerField(null=True, blank=True)
    ouillage_dernier_controle = models.DateField(null=True, blank=True)

    # Volumes & analytique
    volume_brut_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume_net_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    titre_alcoolique_pct = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    sr_g_l = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ph = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    at_g_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    so2_libre_mg_l = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    so2_total_mg_l = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Qualité & process
    ETAT_MICROBIO_CHOICES = [
        ('ok', 'OK'),
        ('surveillance', 'Surveillance'),
        ('action', 'Action requise'),
    ]
    etat_microbio = models.CharField(max_length=20, choices=ETAT_MICROBIO_CHOICES, blank=True)
    clarification_technique = models.CharField(max_length=50, blank=True, help_text="Collage/Filtration/Autre")
    clarification_details = models.TextField(blank=True)
    elevage_type = models.CharField(max_length=50, blank=True)
    elevage_duree_mois = models.PositiveIntegerField(null=True, blank=True)

    # Coûts & valorisation
    cout_matieres_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cout_main_oeuvre_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cout_unitaire_eur_l = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    VALORISATION_CHOICES = [
        ('cmp', 'Coût moyen pondéré (CMP)'),
        ('fifo', 'FIFO'),
    ]
    valorisation_methode = models.CharField(max_length=10, choices=VALORISATION_CHOICES, default='cmp')

    # Lien commercial & réglementaire
    DESTINATION_CHOICES = [
        ('vrac', 'Vrac'),
        ('mise_bouteille', 'Mise bouteille'),
        ('bib', 'BIB'),
        ('tirage_effervescent', 'Tirage effervescent'),
    ]
    destinations = models.CharField(max_length=100, blank=True, help_text="Destinations (CSV)")
    drm_categorie = models.CharField(max_length=50, blank=True)
    certifications = models.CharField(max_length=100, blank=True, help_text="Certifications sur ce lot")
    etiquetage_mentions = models.TextField(blank=True)
    etiquetage_allergenes = models.TextField(blank=True)

    # Notes
    observations = models.TextField(blank=True)

    class Meta:
        verbose_name = "Détail de lot"
        verbose_name_plural = "Détails de lots"
        ordering = ['-created_at']

    def __str__(self):
        return f"Détail lot {self.lot.code}"

    @property
    def pertes_cumulees_l(self):
        if self.volume_brut_l is not None and self.volume_net_l is not None:
            return self.volume_brut_l - self.volume_net_l
        return None


class LotContainer(BaseViticultureModel):
    """Contenant associé à un lot (cuve, fût...)"""
    CONTAINER_CHOICES = [
        ('cuve', 'Cuve'),
        ('fut', 'Fût'),
        ('barrique', 'Barrique'),
        ('autre', 'Autre'),
    ]
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='contenants')
    type = models.CharField(max_length=20, choices=CONTAINER_CHOICES)
    capacite_l = models.DecimalField(max_digits=10, decimal_places=2)
    volume_occupe_l = models.DecimalField(max_digits=10, decimal_places=2)
    identifiant = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Contenant de lot"
        verbose_name_plural = "Contenants de lot"
        ordering = ['type', 'identifiant']

    def __str__(self):
        return f"{self.get_type_display()} {self.identifiant} ({self.volume_occupe_l}L)"


class LotSourceCuvee(models.Model):
    """Sources cuvées d'un lot (traçabilité ascendante)"""
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='sources_cuvees')
    cuvee = models.ForeignKey(Cuvee, on_delete=models.PROTECT)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Source cuvée"
        verbose_name_plural = "Sources cuvées"
        unique_together = ['lot', 'cuvee']

    def __str__(self):
        return f"{self.cuvee.name} ({self.pourcentage or 0}%)"


class LotSourceLot(models.Model):
    """Sources lots d'un lot (assemblages)"""
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='sources_lots')
    source_lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name='utilisations_comme_source')
    volume_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Source lot"
        verbose_name_plural = "Sources lots"
        unique_together = ['lot', 'source_lot']

    def __str__(self):
        return f"{self.source_lot.code} -> {self.lot.code} ({self.pourcentage or 0}%)"


class LotIntervention(BaseViticultureModel):
    """Intervention réalisée sur le lot (journal)"""
    INTERVENTION_CHOICES = [
        ('chaptalisation', 'Chaptalisation'),
        ('acidification', 'Acidification'),
        ('so2', 'Ajout SO₂'),
        ('batonnage', 'Bâtonnage'),
        ('soutirage', 'Soutirage'),
        ('fml', 'Fermentation malolactique'),
        ('filtration', 'Filtration'),
        ('collage', 'Collage'),
        ('correction', 'Correction autre'),
        ('remontage', 'Remontage'),
        ('pigeage', 'Pigeage'),
        ('ouillage', 'Ouillage'),
        ('pressurage', 'Pressurage/Écoulage'),
        ('debourbage', 'Débourbage'),
        ('inoculation_levures', 'Inoculation levures'),
        ('inoculation_bacteries', 'Inoculation bactéries'),
        ('delestage', 'Délestage'),
        ('debut_fa', 'Début FA'),
        ('fin_fa', 'Fin FA'),
        ('debut_fml', 'Début FML'),
        ('fin_fml', 'Fin FML'),
    ]
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='interventions')
    type = models.CharField(max_length=30, choices=INTERVENTION_CHOICES)
    date = models.DateField()
    notes = models.TextField(blank=True)
    volume_in_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume_out_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cout_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    drm_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Intervention de lot"
        verbose_name_plural = "Interventions de lot"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} - {self.date}"


class LotMeasurement(BaseViticultureModel):
    """Mesures ponctuelles sur lot: température, densité, etc."""
    MEAS_CHOICES = [
        ('temperature', 'Température (°C)'),
        ('densite', 'Densité'),
        ('sucre', 'Sucres (g/L)'),
        ('ph', 'pH'),
    ]
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='measurements')
    type = models.CharField(max_length=20, choices=MEAS_CHOICES)
    date = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=16, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Mesure de lot"
        verbose_name_plural = "Mesures de lot"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} = {self.value} {self.unit}" 


class LotDocument(BaseViticultureModel):
    """Pièce jointe liée au lot"""
    DOC_CHOICES = [
        ('analyse_labo', 'Analyse labo'),
        ('cip', 'CIP'),
        ('photo', 'Photo'),
        ('pdf', 'PDF'),
        ('autre', 'Autre'),
    ]
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='lots/documents/')
    type = models.CharField(max_length=20, choices=DOC_CHOICES, default='autre')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document de lot"
        verbose_name_plural = "Documents de lot"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Doc {self.get_type_display()} - {self.lot.code}"
