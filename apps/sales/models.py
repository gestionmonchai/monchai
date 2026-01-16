"""
Modèles pour la gestion des ventes, clients et pricing
DB Roadmap 03 - Ventes, Clients & Pricing
"""

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Organization
from apps.stock.models import SKU, Warehouse
from apps.catalogue.models import Article

User = get_user_model()


class BaseSalesMixin(models.Model):
    """
    Mixin de base pour tous les modèles de ventes
    Fournit organisation, row_version et timestamps
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Organisation"
    )
    row_version = models.PositiveIntegerField(default=1, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)


class BaseSalesModel(BaseSalesMixin):
    """
    Modèle de base standard avec UUID
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TaxCode(BaseSalesModel):
    """
    Code taxe - tax_code
    Gestion TVA française et européenne
    """
    code = models.CharField(max_length=10, help_text="Code court (TVA20, TVA10, etc.)")
    name = models.CharField(max_length=100, help_text="Nom complet")
    rate_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Taux en pourcentage (ex: 20.00 pour 20%)"
    )
    country = models.CharField(
        max_length=2,
        default='FR',
        help_text="Code pays ISO (FR, DE, etc.)"
    )
    is_active = models.BooleanField(default=True, help_text="Code taxe actif")

    class Meta:
        verbose_name = "Code taxe"
        verbose_name_plural = "Codes taxes"
        unique_together = [['organization', 'code']]
        ordering = ['country', 'rate_pct']

    def __str__(self):
        return f"{self.code} - {self.rate_pct}% ({self.country})"


# =============================================================================
# CUSTOMER - IMPORTÉ DEPUIS PARTNERS
# =============================================================================
# Le modèle Customer est maintenant unifié avec Contact dans apps.partners
# Cette classe était un doublon - utiliser Contact depuis partners à la place
from apps.partners.models import Contact as Customer


class PriceList(BaseSalesMixin):
    """
    Grille tarifaire - price_list
    Système de prix flexible avec validité
    Utilise une PK entière (BigAuto) pour des URLs plus conviviales
    """
    name = models.CharField(max_length=100, help_text="Nom de la grille tarifaire")
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise de la grille")
    valid_from = models.DateField(help_text="Date de début de validité")
    valid_to = models.DateField(null=True, blank=True, help_text="Date de fin de validité (optionnelle)")
    is_active = models.BooleanField(default=True, help_text="Grille active")

    class Meta:
        verbose_name = "Grille tarifaire"
        verbose_name_plural = "Grilles tarifaires"
        unique_together = [['organization', 'name']]
        ordering = ['-valid_from', 'name']

    def __str__(self):
        return f"{self.name} ({self.currency})"

    def clean(self):
        super().clean()
        
        # Validation: valid_to doit être après valid_from
        if self.valid_to and self.valid_to <= self.valid_from:
            raise ValidationError({
                'valid_to': 'La date de fin doit être postérieure à la date de début.'
            })

    def is_valid_at(self, date=None):
        """La grille est-elle valide à une date donnée ?"""
        if date is None:
            date = timezone.now().date()
        
        if date < self.valid_from:
            return False
        
        if self.valid_to and date > self.valid_to:
            return False
        
        return self.is_active


class PriceItem(BaseSalesModel):
    """
    Élément de prix - price_item
    Prix par Article avec seuils de quantité et remises
    """
    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Grille tarifaire"
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        verbose_name="Article",
        null=True,
        blank=True
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Prix unitaire"
    )
    min_qty = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Quantité minimum pour ce prix (optionnel)"
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Remise en pourcentage"
    )

    class Meta:
        verbose_name = "Élément de prix"
        verbose_name_plural = "Éléments de prix"
        # unique_together = [['price_list', 'article', 'min_qty']]
        ordering = ['article', 'min_qty']
        indexes = [
            models.Index(fields=['price_list', 'article', 'min_qty']),
        ]

    def __str__(self):
        qty_info = f" (min {self.min_qty})" if self.min_qty else ""
        return f"{self.article.name}: {self.unit_price}€{qty_info}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation pour price_list et article
        if self.price_list and self.article:
            if self.price_list.organization != self.article.organization:
                raise ValidationError({
                    'article': 'L\'article doit appartenir à la même organisation que la grille tarifaire.'
                })

    @property
    def effective_price(self):
        """Prix effectif après remise"""
        if self.discount_pct > 0:
            return self.unit_price * (Decimal('100') - self.discount_pct) / Decimal('100')
        return self.unit_price


class CustomerPriceList(models.Model):
    """
    Association client - grille tarifaire
    Relation many-to-many avec métadonnées
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Priorité (1 = plus haute priorité)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grille client"
        verbose_name_plural = "Grilles clients"
        unique_together = [['customer', 'price_list']]
        ordering = ['customer', 'priority']

    def __str__(self):
        return f"{self.customer.legal_name} → {self.price_list.name}"


class Quote(BaseSalesModel):
    """
    Devis - quote
    Document de vente avant commande
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('lost', 'Perdu'),
        ('expired', 'Expiré'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='quotes',
        verbose_name="Client"
    )
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise du devis")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Statut du devis"
    )
    valid_until = models.DateField(help_text="Date limite de validité")
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total HT"
    )
    total_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total taxes"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total TTC"
    )

    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'customer']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
        ]

    def __str__(self):
        return f"Devis {self.id.hex[:8]} - {self.customer.legal_name}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation pour customer
        if self.customer and self.customer.organization != self.organization:
            raise ValidationError({
                'customer': 'Le client doit appartenir à la même organisation.'
            })

    @property
    def is_expired(self):
        """Le devis est-il expiré ?"""
        return timezone.now().date() > self.valid_until

    def calculate_totals(self):
        """Recalcule les totaux à partir des lignes"""
        lines = self.lines.all()
        
        self.total_ht = sum(line.total_ht for line in lines)
        self.total_tax = sum(line.total_tax for line in lines)
        self.total_ttc = sum(line.total_ttc for line in lines)


class QuoteLine(BaseSalesModel):
    """
    Ligne de devis - quote_line
    Détail des produits dans un devis
    """
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Devis"
    )
    sku = models.ForeignKey(
        SKU,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produit (SKU)"
    )
    description = models.CharField(max_length=200, help_text="Description du produit")
    qty = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Prix unitaire HT"
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Remise en pourcentage"
    )
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        verbose_name="Code taxe"
    )
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total HT de la ligne"
    )
    total_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total taxes de la ligne"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TTC de la ligne"
    )

    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"
        ordering = ['id']

    def __str__(self):
        return f"{self.sku.label} x{self.qty}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.quote and self.sku:
            if self.quote.organization != self.sku.organization:
                raise ValidationError({
                    'sku': 'Le produit doit appartenir à la même organisation que le devis.'
                })

    def save(self, *args, **kwargs):
        # Calcul automatique des totaux
        self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcule les totaux de la ligne"""
        # Prix après remise
        unit_price_discounted = self.unit_price
        if self.discount_pct > 0:
            unit_price_discounted = self.unit_price * (Decimal('100') - self.discount_pct) / Decimal('100')
        
        # Total HT
        self.total_ht = unit_price_discounted * self.qty
        
        # Total taxes
        if self.tax_code:
            self.total_tax = self.total_ht * self.tax_code.rate_pct / Decimal('100')
        else:
            self.total_tax = Decimal('0')
        
        # Total TTC
        self.total_ttc = self.total_ht + self.total_tax


class Order(BaseSalesModel):
    """
    Commande - order
    Document de vente confirmé avec gestion stock
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('fulfilled', 'Expédiée'),
        ('cancelled', 'Annulée'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Impayé'),
        ('partial', 'Partiellement payé'),
        ('paid', 'Payé'),
        ('refunded', 'Remboursé'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Client"
    )
    quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Devis d'origine"
    )
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise de la commande")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Statut de la commande"
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        help_text="Statut de paiement"
    )
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total HT"
    )
    total_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total taxes"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total TTC"
    )

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'customer']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
        ]

    def __str__(self):
        return f"Commande {self.id.hex[:8]} - {self.customer.legal_name}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation pour customer et quote
        if self.customer and self.customer.organization != self.organization:
            raise ValidationError({
                'customer': 'Le client doit appartenir à la même organisation.'
            })
        
        if self.quote and self.quote.organization != self.organization:
            raise ValidationError({
                'quote': 'Le devis doit appartenir à la même organisation.'
            })

    def calculate_totals(self):
        """Recalcule les totaux à partir des lignes"""
        lines = self.lines.all()
        
        self.total_ht = sum(line.total_ht for line in lines)
        self.total_tax = sum(line.total_tax for line in lines)
        self.total_ttc = sum(line.total_ttc for line in lines)


class OrderLine(BaseSalesModel):
    """
    Ligne de commande - order_line
    Détail des produits dans une commande
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Commande"
    )
    sku = models.ForeignKey(
        SKU,
        on_delete=models.PROTECT,
        verbose_name="Produit (SKU)"
    )
    description = models.CharField(max_length=200, help_text="Description du produit")
    qty = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Prix unitaire HT"
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Remise en pourcentage"
    )
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        verbose_name="Code taxe"
    )
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total HT de la ligne"
    )
    total_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total taxes de la ligne"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TTC de la ligne"
    )

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
        ordering = ['id']

    def __str__(self):
        return f"{self.sku.label} x{self.qty}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.order and self.sku:
            if self.order.organization != self.sku.organization:
                raise ValidationError({
                    'sku': 'Le produit doit appartenir à la même organisation que la commande.'
                })

    def save(self, *args, **kwargs):
        # Calcul automatique des totaux
        self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcule les totaux de la ligne"""
        # Prix après remise
        unit_price_discounted = self.unit_price
        if self.discount_pct > 0:
            unit_price_discounted = self.unit_price * (Decimal('100') - self.discount_pct) / Decimal('100')
        
        # Total HT
        self.total_ht = unit_price_discounted * self.qty
        
        # Total taxes
        if self.tax_code:
            self.total_tax = self.total_ht * self.tax_code.rate_pct / Decimal('100')
        else:
            self.total_tax = Decimal('0')
        
        # Total TTC
        self.total_ttc = self.total_ht + self.total_tax


class StockReservation(BaseSalesModel):
    """
    Réservation de stock - stock_reservation
    Réservation automatique lors de la confirmation de commande
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Commande"
    )
    sku = models.ForeignKey(
        SKU,
        on_delete=models.PROTECT,
        verbose_name="Produit (SKU)"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name="Entrepôt"
    )
    qty_units = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantité réservée"
    )

    class Meta:
        verbose_name = "Réservation de stock"
        verbose_name_plural = "Réservations de stock"
        unique_together = [['order', 'sku', 'warehouse']]
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['organization', 'sku', 'warehouse']),
            models.Index(fields=['organization', 'order']),
        ]

    def __str__(self):
        return f"Réservation {self.sku.label} x{self.qty_units} ({self.warehouse.name})"

    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.order and self.sku:
            if self.order.organization != self.sku.organization:
                raise ValidationError({
                    'sku': 'Le produit doit appartenir à la même organisation que la commande.'
                })
        
        if self.warehouse and self.warehouse.organization != self.organization:
            raise ValidationError({
                'warehouse': 'L\'entrepôt doit appartenir à la même organisation.'
            })
