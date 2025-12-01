"""
Modèles cœur viticole - DB Roadmap 01
Référentiels, ressources terrain, produits, traçabilité lots
"""

from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from apps.accounts.models import Organization


class BaseViticultureModel(models.Model):
    """Modèle de base pour tous les modèles viticulture"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        help_text="Organisation propriétaire"
    )
    row_version = models.PositiveIntegerField(
        default=1,
        help_text="Version pour locking optimiste"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Soft delete")
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Incrémente row_version à chaque sauvegarde"""
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)


# ============================================================================
# RÉFÉRENTIELS
# ============================================================================

class GrapeVariety(BaseViticultureModel):
    """
    Cépage - grape_variety
    Roadmap: UNIQUE(organization_id, name_norm)
    """
    
    COLOR_CHOICES = [
        ('rouge', 'Rouge'),
        ('blanc', 'Blanc'),
        ('rose', 'Rosé'),
    ]
    
    name = models.CharField(max_length=100, help_text="Nom du cépage")
    name_norm = models.CharField(
        max_length=100, 
        help_text="Nom normalisé pour unicité",
        editable=False
    )
    color = models.CharField(
        max_length=10, 
        choices=COLOR_CHOICES,
        help_text="Couleur du raisin"
    )
    
    class Meta:
        verbose_name = "Cépage"
        verbose_name_plural = "Cépages"
        unique_together = [['organization', 'name_norm']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name_norm']),
            models.Index(fields=['organization', 'color']),
        ]
    
    def clean(self):
        """Validation et normalisation"""
        if self.name:
            self.name_norm = self.name.lower().strip()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_color_display()})"


class Appellation(BaseViticultureModel):
    """
    Appellation - appellation
    Roadmap: UNIQUE(organization_id, name_norm)
    """
    
    TYPE_CHOICES = [
        ('aoc', 'AOC'),
        ('igp', 'IGP'),
        ('vsig', 'VSIG'),
        ('autre', 'Autre'),
    ]
    
    name = models.CharField(max_length=200, help_text="Nom de l'appellation")
    name_norm = models.CharField(
        max_length=200, 
        help_text="Nom normalisé pour unicité",
        editable=False
    )
    type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES,
        help_text="Type d'appellation"
    )
    region = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Région viticole"
    )
    
    class Meta:
        verbose_name = "Appellation"
        verbose_name_plural = "Appellations"
        unique_together = [['organization', 'name_norm']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name_norm']),
            models.Index(fields=['organization', 'type']),
        ]
    
    def clean(self):
        """Validation et normalisation"""
        if self.name:
            self.name_norm = self.name.lower().strip()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Vintage(BaseViticultureModel):
    """
    Millésime - vintage
    Roadmap: CHECK(1900 <= year <= current_year+1), UNIQUE(organization_id, year)
    """
    
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year + 1)
        ],
        help_text="Année du millésime"
    )
    
    class Meta:
        verbose_name = "Millésime"
        verbose_name_plural = "Millésimes"
        unique_together = [['organization', 'year']]
        ordering = ['-year']
        indexes = [
            models.Index(fields=['organization', 'year']),
        ]
    
    def clean(self):
        """Validation plage année"""
        current_year = timezone.now().year
        if self.year and (self.year < 1900 or self.year > current_year + 1):
            raise ValidationError(
                f"L'année doit être entre 1900 et {current_year + 1}"
            )
    
    def __str__(self):
        return str(self.year)


class UnitOfMeasure(BaseViticultureModel):
    """
    Unité de mesure - unit_of_measure
    Roadmap: base_ratio_to_l pour conversion en litres
    """
    
    code = models.CharField(max_length=10, help_text="Code court (L, hL, BT)")
    name = models.CharField(max_length=50, help_text="Nom complet")
    base_ratio_to_l = models.DecimalField(
        max_digits=10, 
        decimal_places=6,
        help_text="Ratio de conversion vers litres (1 hL = 100 L)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Unité par défaut pour l'organisation"
    )
    
    class Meta:
        verbose_name = "Unité de mesure"
        verbose_name_plural = "Unités de mesure"
        unique_together = [['organization', 'code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class CuveeModel(BaseViticultureModel):
    """
    Cuvée Modèle (identité pérenne)
    Sert de template pour créer les cuvées annuelles.
    """

    name = models.CharField(max_length=120, help_text="Nom du modèle de cuvée")
    code = models.CharField(max_length=40, blank=True, help_text="Code interne (optionnel)")
    default_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        help_text="Unité de mesure par défaut"
    )
    appellation_target = models.ForeignKey(
        Appellation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Appellation visée (INAO)"
    )
    recette = models.JSONField(default=dict, blank=True, help_text="Règles recette: cépages attendus, élevage cible, mentions")
    style = models.CharField(max_length=20, blank=True, help_text="Style (rouge/blanc/rosé/…)")

    class Meta:
        verbose_name = "Modèle de cuvée"
        verbose_name_plural = "Modèles de cuvées"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name", "appellation_target"],
                name="uniq_cuveemodel_org_name_appellation",
            )
        ]

    def clean(self):
        if self.default_uom and self.default_uom.organization != self.organization:
            raise ValidationError("L'unité par défaut doit appartenir à la même organisation")
        if self.appellation_target and self.appellation_target.organization != self.organization:
            raise ValidationError("L'appellation doit appartenir à la même organisation")

    def __str__(self):
        return self.name

# ============================================================================
# RESSOURCES TERRAIN
# ============================================================================
class VineyardPlot(BaseViticultureModel):
    """
    Parcelle de vignes - vineyard_plot
    Roadmap: UNIQUE(organization_id, name), FK same org, CHECK area_ha > 0
    """
    
    name = models.CharField(max_length=100, help_text="Nom de la parcelle")
    area_ha = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Surface en hectares"
    )
    grape_variety = models.ForeignKey(
        GrapeVariety,
        on_delete=models.PROTECT,
        help_text="Cépage principal planté"
    )
    appellation = models.ForeignKey(
        Appellation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Appellation de la parcelle"
    )
    planting_year = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year)
        ],
        help_text="Année de plantation"
    )
    
    class Meta:
        verbose_name = "Parcelle de vignes"
        verbose_name_plural = "Parcelles de vignes"
        unique_together = [['organization', 'name']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'grape_variety']),
            models.Index(fields=['organization', 'appellation']),
        ]
    
    def clean(self):
        """Validation contraintes same org"""
        if self.grape_variety and self.grape_variety.organization != self.organization:
            raise ValidationError("Le cépage doit appartenir à la même organisation")
        
        if self.appellation and self.appellation.organization != self.organization:
            raise ValidationError("L'appellation doit appartenir à la même organisation")
        
        current_year = timezone.now().year
        if self.planting_year and (self.planting_year < 1900 or self.planting_year > current_year):
            raise ValidationError(
                f"L'année de plantation doit être entre 1900 et {current_year}"
            )
    
    def __str__(self):
        return f"{self.name} ({self.area_ha} ha)"


# ============================================================================
# PRODUITS
# ============================================================================

class Cuvee(BaseViticultureModel):
    """
    Cuvée - cuvee
    Roadmap: UNIQUE(organization_id, name), FK vers UoM, appellation, vintage
    """
    
    name = models.CharField(max_length=100, help_text="Nom de la cuvée")
    code = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Code produit (optionnel)"
    )
    # Lien vers le modèle pérenne (nullable pour migration de données)
    model = models.ForeignKey(
        'CuveeModel',
        on_delete=models.PROTECT,
        related_name='vintages',
        null=True,
        blank=True,
        help_text="Modèle de cuvée (identité pérenne)"
    )
    default_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        help_text="Unité de mesure par défaut"
    )
    appellation = models.ForeignKey(
        Appellation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Appellation de la cuvée"
    )
    vintage = models.ForeignKey(
        Vintage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Millésime de la cuvée"
    )
    
    class Meta:
        verbose_name = "Cuvée"
        verbose_name_plural = "Cuvées"
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'vintage']),
            models.Index(fields=['organization', 'appellation']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'model', 'vintage'],
                condition=Q(model__isnull=False) & Q(vintage__isnull=False),
                name='uniq_org_model_vintage_not_null',
            )
        ]
    
    def clean(self):
        """Validation contraintes same org"""
        if self.default_uom and self.default_uom.organization != self.organization:
            raise ValidationError("L'unité de mesure doit appartenir à la même organisation")
        
        if self.appellation and self.appellation.organization != self.organization:
            raise ValidationError("L'appellation doit appartenir à la même organisation")
        
        if self.vintage and self.vintage.organization != self.organization:
            raise ValidationError("Le millésime doit appartenir à la même organisation")
        if self.model and self.model.organization != self.organization:
            raise ValidationError("Le modèle de cuvée doit appartenir à la même organisation")
    
    def can_close(self) -> bool:
        """Retourne True si la cuvée peut être clôturée (pas de lots techniques actifs).
        Actifs = statuts en_cours | stabilise | pret_mise.
        """
        try:
            return not self.lots_techniques.filter(statut__in=[
                'en_cours', 'stabilise', 'pret_mise'
            ]).exists()
        except Exception:
            # Si la relation n'est pas disponible (app non chargé), rester permissif
            return True
    
    def __str__(self):
        vintage_str = f" {self.vintage.year}" if self.vintage else ""
        return f"{self.name}{vintage_str}"


# ============================================================================
# TRAÇABILITÉ (LOTS & ASSEMBLAGES)
# ============================================================================

class Warehouse(BaseViticultureModel):
    """
    Entrepôt/Chai - warehouse
    Référence pour localisation des lots
    """
    
    name = models.CharField(max_length=100, help_text="Nom de l'entrepôt")
    location = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Localisation/adresse"
    )
    
    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        unique_together = [['organization', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Lot(BaseViticultureModel):
    """
    Lot de production - lot
    Roadmap: UNIQUE(organization_id, code), CHECK volume_l >= 0
    """
    
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('elevage', 'Élevage'),
        ('stabilise', 'Stabilisé'),
        ('embouteille', 'Embouteillé'),
        ('archive', 'Archivé'),
    ]
    
    code = models.CharField(max_length=50, help_text="Code unique du lot")
    cuvee = models.ForeignKey(
        Cuvee,
        on_delete=models.PROTECT,
        related_name='lots',
        help_text="Cuvée du lot"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        help_text="Entrepôt de stockage"
    )
    volume_l = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Volume en litres"
    )
    alcohol_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        null=True, blank=True,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('20'))
        ],
        help_text="Degré d'alcool (%)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='en_cours',
        help_text="Statut du lot"
    )
    
    class Meta:
        verbose_name = "Lot de production"
        verbose_name_plural = "Lots de production"
        unique_together = [['organization', 'code']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'cuvee']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'warehouse']),
        ]
    
    def clean(self):
        """Validation contraintes same org"""
        if self.cuvee and self.cuvee.organization != self.organization:
            raise ValidationError("La cuvée doit appartenir à la même organisation")
        
        if self.warehouse and self.warehouse.organization != self.organization:
            raise ValidationError("L'entrepôt doit appartenir à la même organisation")
    
    def __str__(self):
        return f"{self.code} - {self.cuvee.name} ({self.volume_l}L)"


class LotGrapeRatio(models.Model):
    """
    Composition cépages d'un lot - lot_grape_ratio
    Roadmap: PK(lot_id, grape_variety_id), CHECK ratio_pct BETWEEN 0 AND 100
    """
    
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        related_name='grape_ratios'
    )
    grape_variety = models.ForeignKey(
        GrapeVariety,
        on_delete=models.PROTECT
    )
    ratio_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        help_text="Pourcentage du cépage (0-100%)"
    )
    
    class Meta:
        verbose_name = "Composition cépage"
        verbose_name_plural = "Compositions cépages"
        unique_together = [['lot', 'grape_variety']]
        ordering = ['-ratio_pct']
    
    def clean(self):
        """Validation same org"""
        if self.grape_variety and self.lot and \
           self.grape_variety.organization != self.lot.organization:
            raise ValidationError("Le cépage doit appartenir à la même organisation que le lot")
    
    def __str__(self):
        return f"{self.lot.code}: {self.grape_variety.name} ({self.ratio_pct}%)"


class LotAssemblage(models.Model):
    """
    Assemblage de lots - lot_assemblage
    Roadmap: PK(parent_lot_id, child_lot_id, created_at), CHECK volume_l > 0
    """
    
    parent_lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        related_name='assemblages_as_parent',
        help_text="Lot résultant de l'assemblage"
    )
    child_lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        related_name='assemblages_as_child',
        help_text="Lot source de l'assemblage"
    )
    volume_l = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Volume assemblé en litres"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Assemblage de lots"
        verbose_name_plural = "Assemblages de lots"
        unique_together = [['parent_lot', 'child_lot', 'created_at']]
        ordering = ['-created_at']
    
    def clean(self):
        """Validation anti-cycle et same org"""
        if self.parent_lot == self.child_lot:
            raise ValidationError("Un lot ne peut pas s'assembler avec lui-même")
        
        if self.parent_lot and self.child_lot and \
           self.parent_lot.organization != self.child_lot.organization:
            raise ValidationError("Les lots doivent appartenir à la même organisation")
        
        # TODO: Validation anti-cycle DFS côté service
    
    def __str__(self):
        return f"{self.parent_lot.code} ← {self.child_lot.code} ({self.volume_l}L)"


# ============================================================================
# MODÈLES ÉTENDUS POUR FICHE CUVÉE COMPLÈTE
# ============================================================================

class CuveeDetail(BaseViticultureModel):
    """
    Détails étendus d'une cuvée - fiche technique complète
    """
    
    # Référence vers la cuvée de base
    cuvee = models.OneToOneField(
        Cuvee,
        on_delete=models.CASCADE,
        related_name='detail',
        help_text="Cuvée de référence"
    )
    
    # === IDENTIFICATION ÉTENDUE ===
    TYPE_VIN_CHOICES = [
        ('rouge', 'Rouge'),
        ('blanc', 'Blanc'),
        ('rose', 'Rosé'),
        ('petillant', 'Pétillant'),
        ('doux', 'Doux'),
        ('sec', 'Sec'),
        ('moelleux', 'Moelleux'),
        ('liquoreux', 'Liquoreux'),
    ]
    
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('fini', 'Fini'),
        ('vendu', 'Vendu'),
        ('archive', 'Archivé'),
    ]
    
    type_vin = models.CharField(
        max_length=20,
        choices=TYPE_VIN_CHOICES,
        default='rouge',
        help_text="Type de vin"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_cours',
        help_text="Statut de la cuvée"
    )
    
    numero_interne = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Numéro interne unique"
    )

    # === ORIGINE & ÉLABORATION ===
    parcelles = models.ManyToManyField(
        'VineyardPlot',
        through='CuveeParcelleRatio',
        help_text="Parcelles utilisées"
    )
    volume_total_hl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Volume total vinifié (HL)"
    )
    date_vendange_debut = models.DateField(
        null=True, blank=True,
        help_text="Date de début des vendanges"
    )
    date_vendange_fin = models.DateField(
        null=True, blank=True,
        help_text="Date de fin des vendanges"
    )
    VENDANGE_CHOICES = [
        ('manuelle', 'Manuelle'),
        ('mecanique', 'Mécanique'),
        ('mixte', 'Mixte'),
    ]
    methode_vendange = models.CharField(
        max_length=20,
        choices=VENDANGE_CHOICES,
        blank=True,
        help_text="Méthode de vendange"
    )
    VINIFICATION_CHOICES = [
        ('cuve_inox', 'Cuve inox'),
        ('cuve_beton', 'Cuve béton'),
        ('fut_chene', 'Fût chêne'),
        ('amphore', 'Amphore'),
        ('maceration_carbonique', 'Macération carbonique'),
        ('autre', 'Autre'),
    ]
    methode_vinification = models.CharField(
        max_length=30,
        choices=VINIFICATION_CHOICES,
        blank=True,
        help_text="Méthode de vinification"
    )
    duree_elevage_mois = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MaxValueValidator(120)],
        help_text="Durée d'élevage en mois"
    )
    ELEVAGE_CHOICES = [
        ('cuve', 'Cuve'),
        ('fut_neuf', 'Fût neuf'),
        ('fut_ancien', 'Fût ancien'),
        ('barrique', 'Barrique'),
        ('demi_muid', 'Demi-muid'),
        ('autre', 'Autre'),
    ]
    contenant_elevage = models.CharField(
        max_length=20,
        choices=ELEVAGE_CHOICES,
        blank=True,
        help_text="Contenant d'élevage"
    )
    # === ANALYSES TECHNIQUES ===
    degre_alcool_potentiel = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('20'))],
        help_text="Degré alcool potentiel (%)"
    )
    degre_alcool_final = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('20'))],
        help_text="Degré alcool final (%)"
    )
    sucres_residuels = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Sucres résiduels (g/L)"
    )
    ph = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('2.5')), MaxValueValidator(Decimal('4.5'))],
        help_text="pH"
    )
    acidite_totale = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Acidité totale (g/L H2SO4)"
    )
    so2_libre = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="SO2 libre (mg/L)"
    )
    so2_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="SO2 total (mg/L)"
    )

    # === COMMERCIAL ===
    prix_revient_estime = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Prix de revient estimé (€/L)"
    )
    
    certifications = models.CharField(
        max_length=100,
        blank=True,
        help_text="Certifications (séparées par des virgules)"
    )
    etiquette_image = models.ImageField(
        upload_to='cuvees/etiquettes/',
        null=True, blank=True,
        help_text="Image de l'étiquette"
    )
    
    # === NOTES & SUIVI ===
    notes_internes = models.TextField(
        blank=True,
        help_text="Notes internes pour l'équipe"
    )
    
    notes_degustation = models.TextField(
        blank=True,
        help_text="Notes de dégustation"
    )
    
    class Meta:
        verbose_name = "Détail de cuvée"
        verbose_name_plural = "Détails de cuvées"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Détail {self.cuvee.name}"
    
    @property
    def volume_total_l(self):
        """Volume total en litres"""
        if self.volume_total_hl:
            return self.volume_total_hl * 100
        return None


class CuveeParcelleRatio(models.Model):
    """
    Ratio des parcelles dans une cuvée
    """
    cuvee_detail = models.ForeignKey(
        CuveeDetail,
        on_delete=models.CASCADE,
        help_text="Détail de la cuvée"
    )
    parcelle = models.ForeignKey(
        VineyardPlot,
        on_delete=models.CASCADE,
        help_text="Parcelle"
    )
    pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Pourcentage de la parcelle (%)"
    )

    class Meta:
        verbose_name = "Ratio parcelle"
        verbose_name_plural = "Ratios parcelles"
        unique_together = [['cuvee_detail', 'parcelle']]

    def __str__(self):
        return f"{self.parcelle.name}: {self.pourcentage}%"


class CuveeCepageRatio(models.Model):
    """
    Composition en cépages d'une cuvée
    """
    cuvee_detail = models.ForeignKey(
        CuveeDetail,
        on_delete=models.CASCADE,
        related_name='cepages_ratios',
        help_text="Détail de la cuvée"
    )
    cepage = models.ForeignKey(
        GrapeVariety,
        on_delete=models.CASCADE,
        help_text="Cépage"
    )
    pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Pourcentage du cépage (%)"
    )

    class Meta:
        verbose_name = "Ratio cépage"
        verbose_name_plural = "Ratios cépages"
        unique_together = [['cuvee_detail', 'cepage']]

    def __str__(self):
        return f"{self.cepage.name}: {self.pourcentage}%"


class CuveeAnalyse(models.Model):
    """
    Analyses périodiques d'une cuvée
    """
    cuvee_detail = models.ForeignKey(
        CuveeDetail,
        on_delete=models.CASCADE,
        related_name='analyses',
        help_text="Détail de la cuvée"
    )
    date_analyse = models.DateField(
        default=timezone.now,
        help_text="Date de l'analyse"
    )
    type_analyse = models.CharField(
        max_length=50,
        help_text="Type d'analyse"
    )
    resultats = models.JSONField(
        help_text="Résultats de l'analyse (JSON)"
    )
    laboratoire = models.CharField(
        max_length=100,
        blank=True,
        help_text="Laboratoire d'analyse"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes sur l'analyse"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analyse de cuvée"
        verbose_name_plural = "Analyses de cuvées"
        ordering = ['-date_analyse']

    def __str__(self):
        return f"{self.type_analyse} - {self.date_analyse}"

# ---------------------------------------------------------------------------
# Import des modèles étendus (Lot) pour enregistrement par Django
# ---------------------------------------------------------------------------
try:
    from .models_extended import (
        LotDetail,
        LotContainer,
        LotSourceCuvee,
        LotSourceLot,
        LotIntervention,
        LotDocument,
    )
except Exception:
    # Autoriser l'import même si models_extended comporte des dépendances manquantes
    pass

# ---------------------------------------------------------------------------
# Import des modèles Journal de parcelle (lecture seule) pour enregistrement
# ---------------------------------------------------------------------------
try:
    from .models_parcelle_journal import (
        ParcelleOperationType,  # noqa: F401
        ParcelleJournalEntry,   # noqa: F401
    )
except Exception:
    # Autoriser l'import même si environnement partiel/migrations
    pass

# ---------------------------------------------------------------------------
# Import des modèles Opérations de parcelle
# ---------------------------------------------------------------------------
try:
    from .models_ops import ParcelleOperation  # noqa: F401
except Exception:
    pass
