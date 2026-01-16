from __future__ import annotations
from decimal import Decimal
import uuid

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator

from apps.accounts.models import Organization
from apps.viticulture.models import Cuvee as ViticultureCuvee
from apps.referentiels.models import Unite


class ProductType(models.TextChoices):
    VIN = "vin", "Vin"
    PRODUIT = "produit", "Produit dérivé"
    SERVICE = "service", "Service"


class ProductSourceMode(models.TextChoices):
    DOMAINE = "domaine", "Domaine (interne)"
    NEGOCE_VRAC = "negoce_vrac", "Négoce (vrac)"
    NEGOCE_BOUT = "negoce_bout", "Négoce (bouteilles)"
    LIBRE = "libre", "Libre (sans source)"


class BaseCatalogModel(models.Model):
    """Base model with BigAutoField, organization and row_version."""
    # id auto-généré par Django (BigAutoField)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='+')
    row_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)


class Product(BaseCatalogModel):
    """
    Product catalogue entry (vin + dérivés).
    - For wine, link to viticulture.Cuvee to aggregate stock from LotCommercial.
    """
    TYPE_CHOICES = [
        ("wine", "Vin"),
        ("food", "Alimentaire"),
        ("merch", "Merch"),
        ("other", "Autre"),
    ]

    type_code = models.CharField(max_length=10, choices=TYPE_CHOICES)
    # Universel v2
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.VIN)
    name = models.CharField("Nom / Étiquette", max_length=150)
    brand = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(max_length=180, unique=True)
    cuvee = models.ForeignKey(ViticultureCuvee, on_delete=models.PROTECT, null=True, blank=True)
    tax_class = models.CharField(max_length=30, blank=True)
    attrs = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True, verbose_name="Tags")
    is_active = models.BooleanField(default=True)

    # Flags de profil
    is_buyable = models.BooleanField("Achetable", default=False, help_text="Peut être acheté (Profil Achat)")
    is_sellable = models.BooleanField("Vendable", default=False, help_text="Peut être vendu (Profil Vente)")
    is_consumable = models.BooleanField("Consommable", default=False, help_text="Pour usage interne (ne pas revendre)")

    # Tronc commun v2 (Legacy Sales Fields - to be moved to SalesProfile eventually)
    unit = models.ForeignKey(Unite, verbose_name="Unité de vente", on_delete=models.PROTECT, null=True, blank=True)
    price_eur_u = models.DecimalField("Prix de vente (€ / u)", max_digits=10, decimal_places=2, null=True, blank=True)
    vat_rate = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=20)
    stockable = models.BooleanField(default=True)

    # Mode de sourcing
    source_mode = models.CharField(max_length=20, choices=ProductSourceMode.choices, default=ProductSourceMode.DOMAINE)

    # Champs Vin
    volume_l = models.DecimalField("Volume par unité (L)", max_digits=6, decimal_places=3, null=True, blank=True)
    container = models.CharField("Contenant", max_length=50, blank=True)
    ean = models.CharField("Code EAN", max_length=64, blank=True)

    # Champs Produit dérivé
    family = models.CharField("Famille", max_length=50, blank=True)
    net_content = models.CharField("Poids/Volume unitaire", max_length=50, blank=True)
    dluo = models.DateField("DLUO/DLC", null=True, blank=True)
    allergens = models.CharField("Allergènes / mentions", max_length=250, blank=True)

    # Champs Service
    service_category = models.CharField("Catégorie service", max_length=50, blank=True)
    duration = models.DecimalField("Durée (h/j)", max_digits=6, decimal_places=2, null=True, blank=True)
    capacity = models.PositiveIntegerField("Capacité (pers.)", null=True, blank=True)

    # Présentation
    image = models.ImageField(upload_to="produits/", null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "type_code", "is_active"]),
            models.Index(fields=["organization", "slug"]),
        ]
        ordering = ["name"]
        unique_together = [["organization", "name"]]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}

        # Nom
        if not (self.name or "").strip():
            errors["name"] = "Nom requis."

        # Unité + prix (Validation seulement si vendable)
        if self.is_sellable:
            if not self.unit_id:
                # Fallback to SalesProfile unit if handled there, but for now enforcing here if field is used
                pass 
            # if not self.price_eur_u or self.price_eur_u <= 0:
            #     errors["price_eur_u"] = "Prix de vente (> 0) requis."

        # TVA par défaut selon type
        if not self.vat_rate:
            self.vat_rate = 5.5 if self.product_type == ProductType.VIN else (20 if self.product_type == ProductType.SERVICE else 20)

        # Contraintes par type
        if self.product_type == ProductType.VIN:
            if not self.volume_l or self.volume_l <= 0:
                pass # errors["volume_l"] = "Volume par unité (L) requis pour un vin."
            if not (self.container or "").strip():
                pass # errors["container"] = "Contenant requis (ex. 75cL)."

        if self.product_type == ProductType.SERVICE:
            self.stockable = False

        if errors:
            raise ValidationError(errors)

    @property
    def sales_profile(self):
        try:
            return self.salesprofile
        except SalesProfile.DoesNotExist:
            return None

    @property
    def purchase_profile(self):
        try:
            return self.purchaseprofile
        except PurchaseProfile.DoesNotExist:
            return None


class PurchaseProfile(BaseCatalogModel):
    """
    Profil Achat lié à un produit.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='purchaseprofile')
    purchase_unit = models.ForeignKey(Unite, verbose_name="Unité d'achat", on_delete=models.PROTECT)
    main_supplier = models.ForeignKey('partners.Contact', verbose_name="Fournisseur principal", on_delete=models.SET_NULL, null=True, blank=True)
    # cost_price = models.DecimalField("Prix d'achat HT", max_digits=10, decimal_places=4, null=True, blank=True)

    def __str__(self):
        return f"Achat: {self.product.name}"


class SalesProfile(BaseCatalogModel):
    """
    Profil Vente lié à un produit.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='salesprofile')
    commercial_name = models.CharField("Nom commercial", max_length=150, blank=True, help_text="Si différent du nom interne")
    sales_unit = models.ForeignKey(Unite, verbose_name="Unité de vente", on_delete=models.PROTECT)
    sales_price = models.DecimalField("Prix de vente (€ / u)", max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=20)
    
    def __str__(self):
        return f"Vente: {self.product.name}"

    def save(self, *args, **kwargs):
        # Sync legacy fields on Product
        if self.product:
            self.product.price_eur_u = self.sales_price
            self.product.vat_rate = self.vat_rate
            self.product.unit = self.sales_unit
            self.product.save(update_fields=['price_eur_u', 'vat_rate', 'unit'])
        super().save(*args, **kwargs)



class SKU(BaseCatalogModel):
    """
    Sellable variant.
    - unite: FK -> referentiels.Unite (no duplication)
    - normalized_ml: computed from Unite when type is volume
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="skus")
    name = models.CharField(max_length=150)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT)
    pack_of = models.PositiveIntegerField(null=True, blank=True)
    barcode = models.CharField(max_length=64, blank=True)
    internal_ref = models.CharField(max_length=64, blank=True)
    default_price_ht = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0"))])
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "product", "is_active"]),
        ]
        ordering = ["name"]
        unique_together = [["organization", "product", "unite", "name"]]

    def __str__(self) -> str:
        return f"{self.product.name} – {self.name}"

    @property
    def normalized_ml(self) -> int | None:
        """
        Return normalized milliliters for volume units, else None.
        int(round(unite.facteur_conversion * 1000)) when type_unite == 'volume'.
        """
        if not self.unite:
            return None
        try:
            if self.unite.type_unite == "volume" and self.unite.facteur_conversion is not None:
                return int(round(float(self.unite.facteur_conversion) * 1000))
        except Exception:
            return None
        return None


class InventoryItem(BaseCatalogModel):
    """Simple stock item for non-wine SKUs (quantities in units)."""
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name="inventory")
    qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    warehouse = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "sku"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.sku} – {self.qty} u"


class StockMovement(BaseCatalogModel):
    """Log of stock movements for SKUs."""
    MOVEMENT_TYPES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('adjustment', 'Ajustement'),
    ]
    
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='movements')
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    source_doc_type = models.CharField(max_length=50, blank=True) # e.g. "delivery"
    source_doc_id = models.UUIDField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
