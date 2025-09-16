from django.db import models
from django.core.validators import MinValueValidator
from monchai.apps.accounts.models import Domaine


class Parcelle(models.Model):
    """Modèle pour les parcelles de vignes"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="parcelles")
    nom = models.CharField("Nom", max_length=100)
    cepage = models.CharField("Cépage", max_length=100)
    surface_ha = models.DecimalField(
        "Surface (ha)",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    lat = models.FloatField("Latitude", null=True, blank=True)
    lng = models.FloatField("Longitude", null=True, blank=True)
    annee_plantation = models.PositiveIntegerField("Année de plantation", null=True, blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
    
    def __str__(self):
        return f"{self.nom} - {self.cepage}"


class Vendange(models.Model):
    """Modèle pour les vendanges"""
    
    TYPE_CHOICES = [
        ("vendange_vers_cuve", "Vendange vers cuve"),
        ("inter_cuves", "Inter-cuves"),
        ("perte", "Perte"),
        ("mise_en_bouteille", "Mise en bouteille"),
        ("vente_sortie_stock", "Vente sortie stock"),
        ("autre", "Autre")
    ]
    
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("valide", "Validé"),
        ("verrouille", "Verrouillé")
    ]
    
    parcelle = models.ForeignKey(Parcelle, on_delete=models.CASCADE, related_name="vendanges")
    date = models.DateField("Date")
    volume_hl = models.DecimalField("Volume (HL)", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    dechets_hl = models.DecimalField("Déchets (HL)", max_digits=10, decimal_places=2, default=0)
    commentaire = models.TextField("Commentaire", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Vendange"
        verbose_name_plural = "Vendanges"
    
    def __str__(self):
        return f"{self.parcelle.nom} - {self.date}"


class Cuve(models.Model):
    """Modèle pour les cuves"""
    
    MATERIAU_CHOICES = [
        ("inox", "Inox"),
        ("beton", "Béton"),
        ("bois", "Bois"),
        ("fibre", "Fibre"),
        ("autre", "Autre")
    ]
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="cuves")
    nom = models.CharField("Nom", max_length=100)
    capacite_hl = models.DecimalField(
        "Capacité (hl)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    materiau = models.CharField("Matériau", max_length=10, choices=MATERIAU_CHOICES, default="inox")
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Cuve"
        verbose_name_plural = "Cuves"
    
    def __str__(self):
        return f"{self.nom} ({self.capacite_hl} hl)"


class Lot(models.Model):
    """Modèle pour les lots de vin en cuve"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="lots")
    cuve = models.ForeignKey(Cuve, on_delete=models.CASCADE, related_name="lots")
    volume_disponible_hl = models.DecimalField(
        "Volume disponible (hl)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    ref_interne = models.CharField("Référence interne", max_length=100, blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Lot"
        verbose_name_plural = "Lots"
    
    def __str__(self):
        return f"{self.cuve.nom} - {self.ref_interne or 'sans réf'} ({self.volume_disponible_hl} hl)"


class Mouvement(models.Model):
    """Modèle pour les mouvements de vin (journal)"""
    
    TYPE_CHOICES = [
        ("vendange_vers_cuve", "Vendange vers cuve"),
        ("inter_cuves", "Inter-cuves"),
        ("perte", "Perte"),
        ("mise_en_bouteille", "Mise en bouteille"),
        ("vente_sortie_stock", "Vente sortie stock"),
        ("autre", "Autre")
    ]
    
    STATUS_CHOICES = [
        ("draft", "Brouillon"),
        ("valide", "Validé"),
        ("verrouille", "Verrouillé")
    ]
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="mouvements")
    type = models.CharField("Type", max_length=20, choices=TYPE_CHOICES)
    source_lot = models.ForeignKey(
        Lot,
        on_delete=models.PROTECT,
        related_name="mouvements_source",
        null=True,
        blank=True
    )
    destination_cuve = models.ForeignKey(
        Cuve,
        on_delete=models.PROTECT,
        related_name="mouvements_destination",
        null=True,
        blank=True
    )
    volume_hl = models.DecimalField(
        "Volume (hl)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    pertes_hl = models.DecimalField(
        "Pertes (hl)",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    date = models.DateField("Date")
    status = models.CharField("Statut", max_length=10, choices=STATUS_CHOICES, default="draft")
    verrouille = models.BooleanField("Verrouillé", default=False)
    commentaire = models.TextField("Commentaire", blank=True)
    produit_id = models.PositiveIntegerField("ID Produit", null=True, blank=True, help_text="Pour les mouvements de vente")
    meta_json = models.JSONField("Métadonnées", default=dict, blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Mouvement"
        verbose_name_plural = "Mouvements"
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.date} - {self.volume_hl} hl"


class BouteilleLot(models.Model):
    """Modèle pour les lots de bouteilles (mise en bouteille)"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="bouteille_lots")
    source_lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="bouteille_lots")
    nb_bouteilles = models.PositiveIntegerField("Nombre de bouteilles")
    contenance_ml = models.PositiveIntegerField("Contenance (ml)")
    date = models.DateField("Date de mise en bouteille")
    ref_interne = models.CharField("Référence interne", max_length=100, blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Lot de bouteilles"
        verbose_name_plural = "Lots de bouteilles"
    
    def __str__(self):
        return f"{self.source_lot.ref_interne} - {self.nb_bouteilles} x {self.contenance_ml}ml"
