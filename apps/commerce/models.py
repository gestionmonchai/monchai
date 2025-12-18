import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.accounts.models import Organization
from apps.clients.models import Customer
from apps.produits.models_catalog import SKU

class CommercialDocument(models.Model):
    """
    Document commercial unifié (Devis, Commande, BL, Facture, Avoir).
    Remplace les anciens modèles séparés de sales/billing.
    """
    
    # Types de documents
    TYPE_QUOTE = 'quote'
    TYPE_ORDER = 'order'
    TYPE_DELIVERY = 'delivery'  # BL (vente) ou BR (achat)
    TYPE_INVOICE = 'invoice'
    TYPE_CREDIT_NOTE = 'credit_note'
    
    TYPE_CHOICES = [
        (TYPE_QUOTE, 'Devis / Proforma'),
        (TYPE_ORDER, 'Commande'),
        (TYPE_DELIVERY, 'Bon de Livraison / Réception'),
        (TYPE_INVOICE, 'Facture'),
        (TYPE_CREDIT_NOTE, 'Avoir'),
    ]

    # Sens (Achat ou Vente)
    SIDE_SALE = 'sale'
    SIDE_PURCHASE = 'purchase'
    SIDE_CHOICES = [
        (SIDE_SALE, 'Vente'),
        (SIDE_PURCHASE, 'Achat'),
    ]
    
    # Statuts
    STATUS_DRAFT = 'draft'      # Brouillon
    STATUS_SENT = 'sent'        # Envoyé (Devis)
    STATUS_VALIDATED = 'validated' # Validé (Commande)
    STATUS_EXECUTED = 'executed' # Livré / Réceptionné
    STATUS_ISSUED = 'issued'    # Émis / Comptabilisé (Facture)
    STATUS_PAID = 'paid'        # Payé (Soldé)
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_SENT, 'Envoyé'),
        (STATUS_VALIDATED, 'Validé'),
        (STATUS_EXECUTED, 'Exécuté'),
        (STATUS_ISSUED, 'Émis'),
        (STATUS_PAID, 'Payé / Soldé'),
        (STATUS_CANCELLED, 'Annulé'),
    ]
    
    # Modes de vente (Logique métier)
    MODE_STANDARD = 'standard'
    MODE_VRAC = 'vrac'
    MODE_PRIMEUR = 'primeur'
    MODE_SERVICE = 'service'
    
    MODE_CHOICES = [
        (MODE_STANDARD, 'Standard'),
        (MODE_VRAC, 'Vrac'),
        (MODE_PRIMEUR, 'Primeur'),
        (MODE_SERVICE, 'Service / Prestation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='commerce_documents')
    
    # En-tête
    number = models.CharField("Numéro", max_length=50, blank=True, db_index=True)
    reference = models.CharField("Référence externe", max_length=100, blank=True, help_text="Réf client ou fournisseur")
    
    date_issue = models.DateField("Date d'émission", default=timezone.now)
    date_due = models.DateField("Date d'échéance", null=True, blank=True)
    
    # Classification
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, default=SIDE_SALE, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    sale_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_STANDARD)
    
    # Relations
    client = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='commercial_documents', verbose_name="Tiers (Client/Fournisseur)")
    
    # Chaînage (ex: Devis -> Commande -> Facture)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="Document parent")
    
    # Champs spécifiques Primeur / Vrac / Logistique
    delivery_date_expected = models.DateField("Date livraison prévue", null=True, blank=True)
    shipping_address = models.TextField("Adresse de livraison", blank=True)
    
    # Totaux (Dénormalisés pour perfs)
    currency = models.CharField(max_length=3, default='EUR')
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    amount_paid = models.DecimalField("Montant réglé", max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_issue', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'type', 'status']),
            models.Index(fields=['organization', 'client']),
        ]
        verbose_name = "Document commercial"
        verbose_name_plural = "Documents commerciaux"

    def __str__(self):
        return f"{self.get_type_display()} {self.number} - {self.client}"

    @property
    def amount_due(self):
        return self.total_ttc - self.amount_paid
        
    @property
    def is_paid(self):
        return self.amount_paid >= self.total_ttc and self.total_ttc > 0


class CommercialLine(models.Model):
    """
    Ligne de document commercial (Article, Qté, Prix).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(CommercialDocument, on_delete=models.CASCADE, related_name='lines')
    
    # Article (optionnel pour ligne libre)
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, null=True, blank=True, related_name='commercial_lines')
    
    # Description (Snapshot)
    description = models.CharField(max_length=255)
    
    # Valeurs
    quantity = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField("Prix unitaire", max_digits=12, decimal_places=4) # 4 décimales pour précision
    discount_pct = models.DecimalField("Remise %", max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField("Taux TVA", max_digits=5, decimal_places=2, default=20)
    
    # Totaux ligne (calculés)
    amount_ht = models.DecimalField(max_digits=12, decimal_places=2)
    amount_tax = models.DecimalField(max_digits=12, decimal_places=2)
    amount_ttc = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Traçabilité / Vrac
    lot_number = models.CharField("Numéro de lot", max_length=100, blank=True)
    
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = "Ligne commerciale"

    def save(self, *args, **kwargs):
        # Calcul automatique
        price = Decimal(self.unit_price)
        qty = Decimal(self.quantity)
        discount = Decimal(self.discount_pct) / 100
        tax = Decimal(self.tax_rate) / 100
        
        base_ht = price * qty
        remise = base_ht * discount
        
        self.amount_ht = (base_ht - remise).quantize(Decimal('0.01'))
        self.amount_tax = (self.amount_ht * tax).quantize(Decimal('0.01'))
        self.amount_ttc = self.amount_ht + self.amount_tax
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Paiement (Encaissement ou Décaissement)
    Lié à un document ou un acompte.
    """
    METHOD_CHOICES = [
        ('virement', 'Virement'),
        ('cb', 'Carte Bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('prelevement', 'Prélèvement'),
        ('autre', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='commerce_payments')
    
    # Lien document (Facture ou Commande pour acompte)
    document = models.ForeignKey(CommercialDocument, on_delete=models.CASCADE, related_name='payments')
    
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='virement')
    reference = models.CharField(max_length=100, blank=True, help_text="Numéro chèque, virement...")
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.amount}€ ({self.get_method_display()}) on {self.date}"
