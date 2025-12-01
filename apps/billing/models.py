"""
Modèles pour la facturation et comptabilité
DB Roadmap 04 - Facturation & Comptabilité
"""

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Organization
from apps.sales.models import Customer, Order, TaxCode
from apps.stock.models import SKU

User = get_user_model()


class BaseBillingModel(models.Model):
    """
    Modèle de base pour tous les modèles de facturation
    Fournit UUID, organisation, row_version et timestamps
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class Invoice(BaseBillingModel):
    """
    Facture - invoice
    Document de facturation avec numérotation séquentielle
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('issued', 'Émise'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name="Client"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name="Commande d'origine"
    )
    number = models.CharField(
        max_length=20,
        help_text="Numéro de facture (généré automatiquement)"
    )
    date_issue = models.DateField(
        default=timezone.now,
        help_text="Date d'émission"
    )
    due_date = models.DateField(help_text="Date d'échéance")
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Statut de la facture"
    )
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total HT"
    )
    total_tva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total TVA"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total TTC"
    )
    
    # Métadonnées
    notes = models.TextField(blank=True, help_text="Notes internes")

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        unique_together = [['organization', 'number']]
        ordering = ['-date_issue', '-number']
        indexes = [
            models.Index(fields=['organization', 'customer', 'date_issue']),
            models.Index(fields=['organization', 'status', 'date_issue']),
            models.Index(fields=['organization', 'number']),
        ]

    def __str__(self):
        return f"Facture {self.number} - {self.customer.legal_name}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation pour customer et order
        if self.customer and self.customer.organization != self.organization:
            raise ValidationError({
                'customer': 'Le client doit appartenir à la même organisation.'
            })
        
        if self.order and self.order.organization != self.organization:
            raise ValidationError({
                'order': 'La commande doit appartenir à la même organisation.'
            })
        
        # Validation: due_date >= date_issue
        if self.due_date and self.date_issue and self.due_date < self.date_issue:
            raise ValidationError({
                'due_date': 'La date d\'échéance doit être postérieure à la date d\'émission.'
            })

    def calculate_totals(self):
        """Recalcule les totaux à partir des lignes"""
        lines = self.lines.all()
        
        self.total_ht = sum(line.total_ht for line in lines)
        self.total_tva = sum(line.total_tva for line in lines)
        self.total_ttc = sum(line.total_ttc for line in lines)

    @property
    def is_overdue(self):
        """La facture est-elle en retard de paiement ?"""
        return (
            self.status == 'issued' and 
            timezone.now().date() > self.due_date
        )

    @property
    def amount_paid(self):
        """Montant déjà payé via réconciliations"""
        return sum(
            reconciliation.amount_allocated 
            for reconciliation in self.reconciliations.all()
        )

    @property
    def amount_due(self):
        """Montant restant dû"""
        return self.total_ttc - self.amount_paid


class InvoiceLine(BaseBillingModel):
    """
    Ligne de facture - invoice_line
    Détail des produits/services facturés
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Facture"
    )
    sku = models.ForeignKey(
        SKU,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produit (SKU)"
    )
    description = models.CharField(max_length=200, help_text="Description")
    qty = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
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
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Remise en pourcentage"
    )
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        verbose_name="Code TVA"
    )
    
    # Totaux calculés
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total HT de la ligne"
    )
    total_tva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TVA de la ligne"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TTC de la ligne"
    )

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
        ordering = ['id']

    def __str__(self):
        return f"{self.description} x{self.qty}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.invoice and self.sku:
            if self.invoice.organization != self.sku.organization:
                raise ValidationError({
                    'sku': 'Le produit doit appartenir à la même organisation que la facture.'
                })

    def save(self, *args, **kwargs):
        # Calcul automatique des totaux
        self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcule les totaux de la ligne avec arrondi bancaire"""
        from decimal import ROUND_HALF_UP
        
        # Prix après remise
        unit_price_discounted = self.unit_price
        if self.discount_pct > 0:
            unit_price_discounted = self.unit_price * (Decimal('100') - self.discount_pct) / Decimal('100')
        
        # Total HT (arrondi à 2 décimales)
        self.total_ht = (unit_price_discounted * self.qty).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        # Total TVA (arrondi à 2 décimales)
        if self.tax_code:
            self.total_tva = (self.total_ht * self.tax_code.rate_pct / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            self.total_tva = Decimal('0')
        
        # Total TTC
        self.total_ttc = self.total_ht + self.total_tva


class CreditNote(BaseBillingModel):
    """
    Avoir - credit_note
    Document d'annulation ou remboursement partiel/total
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='credit_notes',
        verbose_name="Facture d'origine"
    )
    number = models.CharField(
        max_length=20,
        help_text="Numéro d'avoir (généré automatiquement)"
    )
    date_issue = models.DateField(
        default=timezone.now,
        help_text="Date d'émission"
    )
    reason = models.CharField(
        max_length=200,
        help_text="Motif de l'avoir"
    )
    
    # Totaux (négatifs)
    total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total HT (négatif)"
    )
    total_tva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TVA (négatif)"
    )
    total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total TTC (négatif)"
    )

    class Meta:
        verbose_name = "Avoir"
        verbose_name_plural = "Avoirs"
        unique_together = [['organization', 'number']]
        ordering = ['-date_issue', '-number']

    def __str__(self):
        return f"Avoir {self.number} - {self.invoice.number}"


class Payment(BaseBillingModel):
    """
    Paiement - payment
    Encaissement client avec méthode de paiement
    """
    PAYMENT_METHODS = [
        ('sepa', 'Virement SEPA'),
        ('card', 'Carte bancaire'),
        ('cheque', 'Chèque'),
        ('cash', 'Espèces'),
        ('transfer', 'Virement'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name="Client"
    )
    method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        help_text="Méthode de paiement"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Montant encaissé"
    )
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise")
    date_received = models.DateField(
        default=timezone.now,
        help_text="Date de réception"
    )
    reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Référence du paiement (chèque, virement, etc.)"
    )
    notes = models.TextField(blank=True, help_text="Notes")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_received']
        indexes = [
            models.Index(fields=['organization', 'customer', 'date_received']),
            models.Index(fields=['organization', 'method', 'date_received']),
        ]

    def __str__(self):
        return f"Paiement {self.amount}€ - {self.customer.legal_name}"

    @property
    def amount_allocated(self):
        """Montant déjà alloué aux factures"""
        return sum(
            reconciliation.amount_allocated 
            for reconciliation in self.reconciliations.all()
        )

    @property
    def amount_unallocated(self):
        """Montant non encore alloué"""
        return self.amount - self.amount_allocated


class Reconciliation(BaseBillingModel):
    """
    Réconciliation - reconciliation
    Lettrage entre paiements et factures
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='reconciliations',
        verbose_name="Paiement"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='reconciliations',
        verbose_name="Facture"
    )
    amount_allocated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Montant alloué"
    )

    class Meta:
        verbose_name = "Réconciliation"
        verbose_name_plural = "Réconciliations"
        unique_together = [['payment', 'invoice']]
        ordering = ['created_at']

    def __str__(self):
        return f"Lettrage {self.amount_allocated}€ - {self.invoice.number}"

    def clean(self):
        super().clean()
        
        # Validation: même organisation et même client
        if self.payment and self.invoice:
            if self.payment.organization != self.invoice.organization:
                raise ValidationError({
                    'invoice': 'Le paiement et la facture doivent appartenir à la même organisation.'
                })
            
            if self.payment.customer != self.invoice.customer:
                raise ValidationError({
                    'invoice': 'Le paiement et la facture doivent concerner le même client.'
                })


class AccountMap(BaseBillingModel):
    """
    Plan comptable - account_map
    Mapping vers comptes comptables pour export
    """
    MAPPING_TYPES = [
        ('product', 'Produit'),
        ('customer', 'Client'),
        ('tax', 'Taxe'),
        ('payment_method', 'Méthode de paiement'),
    ]

    mapping_type = models.CharField(
        max_length=20,
        choices=MAPPING_TYPES,
        help_text="Type de mapping"
    )
    key = models.CharField(
        max_length=50,
        help_text="Clé de référence (ID produit, code taxe, etc.)"
    )
    account_code = models.CharField(
        max_length=10,
        help_text="Code compte comptable"
    )
    account_name = models.CharField(
        max_length=100,
        help_text="Libellé du compte"
    )

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Comptes comptables"
        unique_together = [['organization', 'mapping_type', 'key']]
        ordering = ['mapping_type', 'account_code']

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class GLEntry(BaseBillingModel):
    """
    Écriture comptable - gl_entry
    Journal général avec écritures automatiques
    """
    JOURNAL_CHOICES = [
        ('VEN', 'Ventes'),
        ('BAN', 'Banque'),
        ('OD', 'Opérations diverses'),
    ]

    DOC_TYPE_CHOICES = [
        ('invoice', 'Facture'),
        ('payment', 'Paiement'),
        ('credit_note', 'Avoir'),
    ]

    journal = models.CharField(
        max_length=3,
        choices=JOURNAL_CHOICES,
        help_text="Code journal"
    )
    date = models.DateField(help_text="Date comptable")
    doc_type = models.CharField(
        max_length=15,
        choices=DOC_TYPE_CHOICES,
        help_text="Type de document"
    )
    doc_id = models.UUIDField(help_text="ID du document source")
    doc_number = models.CharField(
        max_length=20,
        help_text="Numéro du document"
    )
    account_code = models.CharField(
        max_length=10,
        help_text="Code compte comptable"
    )
    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Montant débit"
    )
    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Montant crédit"
    )
    label = models.CharField(max_length=100, help_text="Libellé de l'écriture")

    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ['-date', 'journal', 'doc_number']
        indexes = [
            models.Index(fields=['organization', 'journal', 'date']),
            models.Index(fields=['organization', 'account_code', 'date']),
            models.Index(fields=['organization', 'doc_type', 'doc_id']),
        ]

    def __str__(self):
        return f"{self.journal} - {self.account_code} - {self.label}"

    def clean(self):
        super().clean()
        
        # Validation: soit débit soit crédit (pas les deux)
        if self.debit > 0 and self.credit > 0:
            raise ValidationError(
                'Une écriture ne peut pas avoir à la fois un débit et un crédit.'
            )
        
        if self.debit == 0 and self.credit == 0:
            raise ValidationError(
                'Une écriture doit avoir soit un débit soit un crédit.'
            )
