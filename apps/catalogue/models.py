"""
Modèles pour le catalogue et la gestion des lots
Roadmap Cut #4 : Catalogue & lots
"""

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from apps.accounts.models import Organization
from apps.referentiels.models import Cuvee, Entrepot, Unite


class Lot(models.Model):
    """
    Modèle pour les lots de production
    Roadmap items 21, 22, 23: /lots – Liste, création, détail lots
    """
    
    STATUT_CHOICES = [
        ('production', 'En production'),
        ('fermentation', 'En fermentation'),
        ('elevage', 'En élevage'),
        ('assemblage', 'En assemblage'),
        ('conditionnement', 'En conditionnement'),
        ('stock', 'En stock'),
        ('vendu', 'Vendu'),
        ('perdu', 'Perdu/Détruit'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='lots')
    cuvee = models.ForeignKey(Cuvee, on_delete=models.CASCADE, related_name='lots')
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='lots')
    
    # Identification
    numero_lot = models.CharField(max_length=50, verbose_name="Numéro de lot")
    millesime = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        verbose_name="Millésime"
    )
    
    # Volumes et quantités
    volume_initial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Volume initial"
    )
    unite_volume = models.ForeignKey(
        Unite,
        on_delete=models.PROTECT,
        related_name='lots_volume',
        limit_choices_to={'type_unite': 'volume'},
        verbose_name="Unité de volume"
    )
    volume_actuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume actuel"
    )
    
    # Caractéristiques techniques
    degre_alcool = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Degré d'alcool (%)"
    )
    densite = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.8), MaxValueValidator(1.2)],
        verbose_name="Densité"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='production',
        verbose_name="Statut"
    )
    date_creation = models.DateField(verbose_name="Date de création du lot")
    date_fin_prevue = models.DateField(blank=True, null=True, verbose_name="Date de fin prévue")
    
    # Informations complémentaires
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lot"
        verbose_name_plural = "Lots"
        unique_together = ['organization', 'numero_lot', 'millesime']
        ordering = ['-millesime', 'numero_lot']
    
    def __str__(self):
        return f"{self.numero_lot} - {self.cuvee.nom} {self.millesime}"
    
    def get_absolute_url(self):
        return reverse('catalogue:lot_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Initialiser volume_actuel avec volume_initial si nouveau lot
        if not self.pk and not self.volume_actuel:
            self.volume_actuel = self.volume_initial
        super().save(*args, **kwargs)
    
    @property
    def volume_consomme(self):
        """Volume consommé (initial - actuel)"""
        return self.volume_initial - self.volume_actuel
    
    @property
    def pourcentage_restant(self):
        """Pourcentage de volume restant"""
        if self.volume_initial > 0:
            return (self.volume_actuel / self.volume_initial) * 100
        return 0
    
    @property
    def est_epuise(self):
        """True si le lot est épuisé (volume actuel = 0)"""
        return self.volume_actuel <= 0


class MouvementLot(models.Model):
    """
    Modèle pour l'historique des mouvements de lots
    Roadmap item 23: /lots/:id – Détail lot (historique mouvements)
    """
    
    TYPE_MOUVEMENT_CHOICES = [
        ('creation', 'Création du lot'),
        ('transfert_entrepot', 'Transfert d\'entrepôt'),
        ('assemblage', 'Assemblage'),
        ('soutirage', 'Soutirage'),
        ('filtration', 'Filtration'),
        ('conditionnement', 'Conditionnement'),
        ('vente', 'Vente'),
        ('perte', 'Perte/Casse'),
        ('correction', 'Correction manuelle'),
        ('autre', 'Autre'),
    ]
    
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='mouvements')
    
    # Type et description
    type_mouvement = models.CharField(
        max_length=20,
        choices=TYPE_MOUVEMENT_CHOICES,
        verbose_name="Type de mouvement"
    )
    description = models.CharField(max_length=200, verbose_name="Description")
    
    # Volumes
    volume_avant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume avant"
    )
    volume_mouvement = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Volume du mouvement"
    )
    volume_apres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume après"
    )
    
    # Entrepôts (pour les transferts)
    entrepot_source = models.ForeignKey(
        Entrepot,
        on_delete=models.PROTECT,
        related_name='mouvements_sortie',
        blank=True,
        null=True,
        verbose_name="Entrepôt source"
    )
    entrepot_destination = models.ForeignKey(
        Entrepot,
        on_delete=models.PROTECT,
        related_name='mouvements_entree',
        blank=True,
        null=True,
        verbose_name="Entrepôt destination"
    )
    
    # Métadonnées
    date_mouvement = models.DateTimeField(verbose_name="Date du mouvement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mouvement de lot"
        verbose_name_plural = "Mouvements de lots"
        ordering = ['-date_mouvement']
    
    def __str__(self):
        return f"{self.lot.numero_lot} - {self.get_type_mouvement_display()} ({self.date_mouvement.strftime('%d/%m/%Y')})"
