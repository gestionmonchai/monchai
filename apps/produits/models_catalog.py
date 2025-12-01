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
    """Base model with UUID, organization and row_version."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    is_active = models.BooleanField(default=True)

    # Tronc commun v2
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

        # Unité + prix
        if not self.unit_id:
            errors["unit"] = "Unité de vente requise."
        if not self.price_eur_u or self.price_eur_u <= 0:
            errors["price_eur_u"] = "Prix de vente (> 0) requis."

        # TVA par défaut selon type
        if not self.vat_rate:
            self.vat_rate = 5.5 if self.product_type == ProductType.VIN else (20 if self.product_type == ProductType.SERVICE else 20)

        # Contraintes par type
        if self.product_type == ProductType.VIN:
            if not self.volume_l or self.volume_l <= 0:
                errors["volume_l"] = "Volume par unité (L) requis pour un vin."
            if not (self.container or "").strip():
                errors["container"] = "Contenant requis (ex. 75cL)."

        if self.product_type == ProductType.SERVICE:
            self.stockable = False

        # Sourcing (mini-règles)
        # Si domaine et création, la vue vérifiera >=1 ligne cuvée

        if errors:
            raise ValidationError(errors)


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
    qty = models.PositiveIntegerField(default=0)
    warehouse = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "sku"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.sku} – {self.qty} u"
