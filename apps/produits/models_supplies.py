"""
Modèles pour la gestion des Fournitures (Supplies)
Distinct des Produits (Products) qui sont destinés à la vente.

Fournitures = ce qu'on achète (matières premières, consommables, équipements)
Produits = ce qu'on vend (vins, articles commercialisables)
"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from apps.accounts.models import Organization
from apps.referentiels.models import Unite, Entrepot


class SupplyCategory(models.Model):
    """
    Catégories de fournitures.
    Ex: Matières sèches, Produits œnologiques, Emballages, Équipements, Services...
    """
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='supply_categories'
    )
    name = models.CharField("Nom", max_length=100)
    code = models.CharField("Code", max_length=20, blank=True)
    description = models.TextField("Description", blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="Catégorie parente"
    )
    sort_order = models.PositiveIntegerField("Ordre", default=0)
    is_active = models.BooleanField("Actif", default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'produits_supply_category'
        verbose_name = "Catégorie de fourniture"
        verbose_name_plural = "Catégories de fournitures"
        ordering = ['sort_order', 'name']
        unique_together = ['organization', 'name']

    def __str__(self):
        return self.name


class SupplyType(models.TextChoices):
    """Types de fournitures"""
    RAW_MATERIAL = "raw_material", "Matière première"
    CONSUMABLE = "consumable", "Consommable"
    PACKAGING = "packaging", "Emballage"
    OENOLOGICAL = "oenological", "Produit œnologique"
    EQUIPMENT = "equipment", "Équipement"
    SERVICE = "service", "Service / Prestation"
    OTHER = "other", "Autre"


class Supply(models.Model):
    """
    Modèle pour les Fournitures (ce qu'on achète).
    
    Exemples :
    - Matières sèches : bouteilles, bouchons, capsules, étiquettes, cartons
    - Produits œnologiques : levures, enzymes, SO2, tanins
    - Consommables : filtres, gaz, produits d'entretien
    - Équipements : petits matériels, outillage
    - Services : analyses labo, prestataires
    """
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='supplies'
    )
    category = models.ForeignKey(
        SupplyCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='supplies',
        verbose_name="Catégorie"
    )
    
    # Identification
    supply_type = models.CharField(
        "Type", 
        max_length=20, 
        choices=SupplyType.choices, 
        default=SupplyType.CONSUMABLE
    )
    name = models.CharField("Désignation", max_length=200)
    reference = models.CharField(
        "Référence interne", 
        max_length=50, 
        blank=True, 
        help_text="Code article interne"
    )
    supplier_ref = models.CharField(
        "Réf. fournisseur", 
        max_length=50, 
        blank=True, 
        help_text="Référence chez le fournisseur"
    )
    description = models.TextField("Description", blank=True)
    slug = models.SlugField(max_length=220, blank=True)
    
    # Unités et conditionnement
    unit = models.ForeignKey(
        Unite, 
        verbose_name="Unité d'achat", 
        on_delete=models.PROTECT,
        related_name='supplies'
    )
    packaging_qty = models.DecimalField(
        "Qté par conditionnement", 
        max_digits=10, 
        decimal_places=2, 
        default=1,
        help_text="Ex: 1000 bouchons par carton"
    )
    min_order_qty = models.DecimalField(
        "Qté min. commande", 
        max_digits=10, 
        decimal_places=2, 
        default=1
    )
    
    # Prix et coûts
    purchase_price = models.DecimalField(
        "Prix d'achat HT", 
        max_digits=10, 
        decimal_places=4, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    vat_rate = models.DecimalField(
        "TVA (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=20
    )
    last_purchase_price = models.DecimalField(
        "Dernier PA", 
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Dernier prix d'achat constaté"
    )
    last_purchase_date = models.DateField(
        "Date dernier achat", 
        null=True, 
        blank=True
    )
    
    # Fournisseur principal
    main_supplier = models.ForeignKey(
        'partners.Contact', 
        verbose_name="Fournisseur principal", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supplied_items',
        limit_choices_to={'roles__code': 'FOURNISSEUR'}
    )
    
    # Gestion de stock
    is_stockable = models.BooleanField(
        "Géré en stock", 
        default=True,
        help_text="Si actif, le système suit les quantités"
    )
    stock_min = models.DecimalField(
        "Stock minimum", 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Seuil d'alerte stock bas"
    )
    stock_max = models.DecimalField(
        "Stock maximum", 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Stock cible (0 = pas de limite)"
    )
    lead_time_days = models.PositiveIntegerField(
        "Délai appro. (jours)", 
        default=7,
        help_text="Délai de réapprovisionnement moyen"
    )
    
    # Caractéristiques techniques
    specs = models.JSONField(
        "Spécifications", 
        default=dict, 
        blank=True,
        help_text="Caractéristiques techniques (dimensions, matière, etc.)"
    )
    
    # Statut
    is_active = models.BooleanField("Actif", default=True)
    is_discontinued = models.BooleanField(
        "Arrêté", 
        default=False,
        help_text="Produit arrêté, ne plus commander"
    )
    
    # Métadonnées
    notes = models.TextField("Notes internes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'produits_supply'
        verbose_name = "Fourniture"
        verbose_name_plural = "Fournitures"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['organization', 'supply_type', 'is_active']),
            models.Index(fields=['organization', 'reference']),
        ]
        unique_together = [['organization', 'reference']]

    def __str__(self):
        if self.reference:
            return f"[{self.reference}] {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:220]
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)

    @property
    def price_ttc(self):
        """Prix TTC"""
        return self.purchase_price * (1 + self.vat_rate / 100)
    
    @property
    def needs_reorder(self):
        """True si le stock est sous le seuil minimum"""
        if not self.is_stockable or self.stock_min <= 0:
            return False
        current = self.current_stock
        return current < self.stock_min
    
    @property
    def current_stock(self):
        """Stock actuel total (toutes localisations)"""
        from django.db.models import Sum
        result = self.stock_lines.aggregate(total=Sum('quantity'))
        return result['total'] or Decimal('0')


class SupplyStock(models.Model):
    """
    Stock de fournitures par emplacement.
    """
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='supply_stocks'
    )
    supply = models.ForeignKey(
        Supply, 
        on_delete=models.CASCADE, 
        related_name='stock_lines'
    )
    location = models.ForeignKey(
        Entrepot, 
        on_delete=models.PROTECT, 
        related_name='supply_stocks',
        verbose_name="Emplacement"
    )
    
    # Traçabilité optionnelle
    batch_number = models.CharField(
        "N° de lot", 
        max_length=50, 
        blank=True, 
        default=""
    )
    expiry_date = models.DateField(
        "Date d'expiration", 
        null=True, 
        blank=True
    )
    
    # Quantité
    quantity = models.DecimalField(
        "Quantité", 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    reserved_qty = models.DecimalField(
        "Qté réservée", 
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Quantité réservée pour production"
    )
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'produits_supply_stock'
        verbose_name = "Stock fourniture"
        verbose_name_plural = "Stocks fournitures"
        unique_together = ['supply', 'location', 'batch_number']
        ordering = ['supply', 'location']

    def __str__(self):
        loc = f" @ {self.location.nom}" if self.location else ""
        batch = f" [{self.batch_number}]" if self.batch_number else ""
        return f"{self.supply.name}{batch}: {self.quantity}{loc}"
    
    @property
    def available_qty(self):
        """Quantité disponible (non réservée)"""
        return self.quantity - self.reserved_qty


class SupplyMovement(models.Model):
    """
    Mouvements de stock fournitures (journal).
    """
    MOVE_IN = 'in'
    MOVE_OUT = 'out'
    MOVE_ADJUST = 'adjust'
    MOVE_TRANSFER = 'transfer'
    
    MOVE_CHOICES = [
        (MOVE_IN, 'Entrée (Réception)'),
        (MOVE_OUT, 'Sortie (Consommation)'),
        (MOVE_ADJUST, 'Ajustement (Inventaire)'),
        (MOVE_TRANSFER, 'Transfert'),
    ]
    
    REASON_CHOICES = [
        ('purchase', 'Achat / Réception'),
        ('production', 'Production'),
        ('return', 'Retour fournisseur'),
        ('loss', 'Perte / Casse'),
        ('inventory', 'Inventaire'),
        ('transfer', 'Transfert interne'),
        ('other', 'Autre'),
    ]

    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='supply_movements'
    )
    supply = models.ForeignKey(
        Supply, 
        on_delete=models.CASCADE, 
        related_name='movements'
    )
    location = models.ForeignKey(
        Entrepot, 
        on_delete=models.PROTECT, 
        related_name='supply_movements',
        verbose_name="Emplacement"
    )
    
    movement_type = models.CharField(
        "Type", 
        max_length=10, 
        choices=MOVE_CHOICES
    )
    reason = models.CharField(
        "Motif", 
        max_length=20, 
        choices=REASON_CHOICES, 
        default='other'
    )
    quantity = models.DecimalField(
        "Quantité", 
        max_digits=12, 
        decimal_places=2
    )
    
    batch_number = models.CharField("N° lot", max_length=50, blank=True, default="")
    
    # Référence document source
    reference = models.CharField(
        "Référence", 
        max_length=100, 
        blank=True,
        help_text="Ex: Bon réception #123, OF #456"
    )
    
    # Pour les transferts
    destination_location = models.ForeignKey(
        Entrepot, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='supply_movements_in',
        verbose_name="Destination"
    )
    
    notes = models.TextField("Notes", blank=True)
    date = models.DateTimeField("Date")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    class Meta:
        db_table = 'produits_supply_movement'
        verbose_name = "Mouvement fourniture"
        verbose_name_plural = "Mouvements fournitures"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.supply.name}"


# =============================================================================
# ALIAS POUR FACILITER L'IMPORT
# =============================================================================
Fourniture = Supply
CategorieFourniture = SupplyCategory
StockFourniture = SupplyStock
MouvementFourniture = SupplyMovement
