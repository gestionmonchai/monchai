from __future__ import annotations
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
import uuid

from apps.viticulture.models import Cuvee as ViticultureCuvee
from apps.viticulture.models import Appellation as ViticultureAppellation
from apps.accounts.models import Organization
from apps.referentiels.models import Unite
from apps.core.tenancy import TenantManager
from apps.sales.models import Customer  # supplier as Customer
from apps.production.models import LotTechnique
from .models_catalog import Product  # register Product model for FK resolution


class Mise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_of = models.CharField(max_length=20, unique=True)
    date = models.DateField(default=timezone.now)
    campagne = models.CharField(max_length=9)
    notes = models.TextField(blank=True)
    execution_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    STATE_CHOICES = (
        ("brouillon", "Brouillon"),
        ("terminee", "Terminée"),
    )
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default="brouillon")
    created_at = models.DateTimeField(auto_now_add=True)
    # Hotfix: derive org via source lots linked through lines
    TENANT_ORG_LOOKUPS = (
        'lignes__lot_tech_source__cuvee__organization',
        'lignes__lot_tech_source__source__organization',
    )
    objects = TenantManager()

    class Meta:
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:
        return self.code_of


class LotCommercial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mise = models.ForeignKey(Mise, on_delete=models.CASCADE, related_name="lots")
    code_lot = models.CharField(max_length=64, unique=True)
    cuvee = models.ForeignKey(ViticultureCuvee, on_delete=models.PROTECT, related_name="lots_commerciaux", null=True, blank=True)
    format_ml = models.PositiveIntegerField(default=750)
    date_mise = models.DateField()
    quantite_unites = models.PositiveIntegerField(default=0)
    stock_disponible = models.PositiveIntegerField(default=0)
    inao_code = models.CharField(max_length=32, blank=True)
    nc_code = models.CharField(max_length=32, blank=True)
    emb_code = models.CharField(max_length=32, blank=True)
    capsule_crd = models.BooleanField(default=False)
    capsule_crd_color = models.CharField(max_length=20, blank=True)
    capsule_marking = models.CharField(max_length=64, blank=True)
    TENANT_ORG_LOOKUPS = (
        'mise__lignes__lot_tech_source__cuvee__organization',
        'mise__lignes__lot_tech_source__source__organization',
        'cuvee__organization',
    )
    objects = TenantManager()

    class Meta:
        ordering = ("-date_mise", "-id")

    def __str__(self) -> str:
        return f"{self.code_lot} ({self.quantite_unites} u)"


class MiseLigne(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mise = models.ForeignKey(Mise, on_delete=models.CASCADE, related_name="lignes")
    lot_tech_source = models.ForeignKey(LotTechnique, on_delete=models.PROTECT, related_name="utilisations_mise")
    format_ml = models.PositiveIntegerField(default=750)
    quantite_unites = models.PositiveIntegerField(default=0)
    pertes_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    TENANT_ORG_LOOKUPS = (
        'lot_tech_source__cuvee__organization',
        'lot_tech_source__source__organization',
    )
    objects = TenantManager()

    class Meta:
        ordering = ("id",)


class ProductSourcingCuvee(models.Model):
    """Sourcing Domaine: composition par cuvée pour un produit (vin)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('produits.Product', related_name='source_cuvees', on_delete=models.CASCADE)
    cuvee = models.ForeignKey(ViticultureCuvee, on_delete=models.PROTECT)
    ratio_pct = models.DecimalField("Ratio (%)", max_digits=6, decimal_places=3, default=100)
    allow_other_vintages = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)


class PurchaseBatchVrac(models.Model):
    """Achat de vrac (négoce)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Customer, on_delete=models.PROTECT)
    appellation = models.ForeignKey(ViticultureAppellation, null=True, blank=True, on_delete=models.SET_NULL)
    vintage = models.PositiveIntegerField(null=True, blank=True)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2)
    price_eur_hl = models.DecimalField(max_digits=10, decimal_places=2)
    contract_ref = models.CharField(max_length=100, blank=True)
    received_at = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-received_at', '-id')


class ProductSourcingVrac(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField('produits.Product', related_name='source_vrac', on_delete=models.CASCADE)
    fifo = models.BooleanField(default=True)


class PurchaseBatchBottle(models.Model):
    """Achat de bouteilles (négoce)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Customer, on_delete=models.PROTECT)
    product_label = models.CharField(max_length=200)
    ean_supplier = models.CharField(max_length=64, blank=True)
    unit = models.ForeignKey(Unite, on_delete=models.PROTECT)
    qty_u = models.DecimalField(max_digits=12, decimal_places=2)
    cost_eur_u = models.DecimalField(max_digits=10, decimal_places=4)
    received_at = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-received_at', '-id')


class ProductSourcingBottle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField('produits.Product', related_name='source_bottle', on_delete=models.CASCADE)
    ean_override = models.CharField("EAN interne (override)", max_length=64, blank=True)
