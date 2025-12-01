"""
Modèles pour la gestion des clients - Roadmap 36
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from apps.accounts.models import Organization
from .validators import (
    AdvancedEmailValidator, PhoneE164Validator, VATNumberValidator,
    CountryCodeValidator, CustomerNameValidator
)


class BaseClientModel(models.Model):
    """Modèle de base pour tous les modèles clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='clients_%(class)s_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_version = models.PositiveIntegerField(default=1)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)


class Customer(BaseClientModel):
    """
    Modèle Customer selon Roadmap 36
    Segments: individual, business, wine_shop, export, other
    """
    
    SEGMENT_CHOICES = [
        ('individual', 'Particulier'),
        ('business', 'Professionnel'),
        ('wine_shop', 'Caviste'),
        ('export', 'Export'),
        ('other', 'Autre'),
    ]
    
    # Champs obligatoires
    segment = models.CharField(max_length=20, choices=SEGMENT_CHOICES)
    name = models.CharField(
        max_length=120, 
        validators=[CustomerNameValidator()],
        help_text="Nom du client (2-120 caractères)"
    )
    name_norm = models.CharField(
        max_length=120, 
        help_text="Nom normalisé pour recherche (généré automatiquement)"
    )
    
    # Champs optionnels avec validateurs avancés
    vat_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[VATNumberValidator()],
        help_text="Numéro de TVA intracommunautaire (requis pour business/export)"
    )
    country_code = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        validators=[CountryCodeValidator()],
        help_text="Code pays ISO 3166-1 alpha-2 (FR, DE, IT...)"
    )
    email = models.EmailField(
        max_length=254,
        blank=True, 
        null=True,
        validators=[AdvancedEmailValidator()],
        help_text="Adresse email (normalisée automatiquement)"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[PhoneE164Validator()],
        help_text="Téléphone au format E.164 (+33123456789)"
    )
    
    # État
    is_active = models.BooleanField(default=True)
    
    # Champ de recherche full-text
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        db_table = 'clients_customer'
        indexes = [
            # Index pour recherche trigram sur nom normalisé
            GinIndex(fields=['name_norm'], name='clients_cust_name_norm_gin'),
            # Index pour recherche full-text
            GinIndex(fields=['search_vector'], name='clients_cust_search_gin'),
            # Index pour filtres fréquents
            models.Index(fields=['organization', 'segment'], name='clients_cust_org_segment_idx'),
            models.Index(fields=['organization', 'is_active'], name='clients_cust_org_active_idx'),
            # Index pour tri et pagination keyset
            models.Index(fields=['organization', 'updated_at', 'id'], name='clients_cust_keyset_idx'),
        ]
        constraints = [
            # Contrainte d'unicité pour numéro de TVA par organisation (NULLS NOT DISTINCT)
            models.UniqueConstraint(
                fields=['organization', 'vat_number'],
                name='unique_customer_vat_per_org',
                condition=models.Q(vat_number__isnull=False)
            ),
            # Contrainte d'unicité pour nom par organisation
            models.UniqueConstraint(
                fields=['organization', 'name_norm'],
                name='unique_customer_name_per_org'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_segment_display()})"
    
    def save(self, *args, **kwargs):
        # Normalisation automatique des champs
        self._normalize_fields()
        
        super().save(*args, **kwargs)
    
    def _normalize_fields(self):
        """Normalise les champs avant sauvegarde"""
        from .validators import CustomerNameValidator, PhoneE164Validator, VATNumberValidator
        
        # Normalisation du nom
        if self.name:
            self.name = self.name.strip()
            self.name_norm = CustomerNameValidator.normalize_name(self.name)
        
        # Normalisation de l'email
        if self.email:
            self.email = self.email.lower().strip()
        
        # Normalisation du téléphone
        if self.phone:
            self.phone = PhoneE164Validator.normalize_phone(self.phone, self.country_code)
        
        # Normalisation du numéro de TVA
        if self.vat_number:
            self.vat_number = VATNumberValidator.normalize_vat(self.vat_number)
        
        # Normalisation du code pays
        if self.country_code:
            self.country_code = self.country_code.upper().strip()
    
    def clean(self):
        """Validation métier avancée"""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validation du numéro de TVA pour business et export
        if self.segment in ['business', 'export'] and not self.vat_number:
            errors['vat_number'] = 'Le numéro de TVA est requis pour les segments Professionnel et Export.'
        
        # Validation cohérence pays/TVA
        if self.vat_number and self.country_code:
            vat_country = self.vat_number[:2] if len(self.vat_number) >= 2 else ''
            if vat_country != self.country_code:
                errors['vat_number'] = f'Le numéro de TVA doit correspondre au pays {self.country_code}.'
        
        # Validation cohérence pays/téléphone
        if self.phone and self.country_code:
            try:
                validator = PhoneE164Validator(self.country_code)
                validator(self.phone)
            except ValidationError as e:
                errors['phone'] = str(e.message)
        
        # Validation de l'organisation
        if hasattr(self, 'organization') and self.organization:
            # Vérifier que tous les objets liés appartiennent à la même organisation
            pass
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def display_name(self):
        """Nom d'affichage avec segment"""
        return f"{self.name} ({self.get_segment_display()})"
    
    @property
    def masked_phone(self):
        """Téléphone masqué pour GDPR"""
        if not self.phone or len(self.phone) < 4:
            return self.phone
        return self.phone[:2] + '*' * (len(self.phone) - 4) + self.phone[-2:]
    
    @property
    def masked_email(self):
        """Email masqué pour GDPR"""
        if not self.email or '@' not in self.email:
            return self.email
        local, domain = self.email.split('@', 1)
        if len(local) <= 2:
            return self.email
        return local[:2] + '*' * (len(local) - 2) + '@' + domain


class CustomerTag(BaseClientModel):
    """Tags pour catégoriser les clients"""
    
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7, 
        default='#6c757d',
        help_text="Couleur hexadécimale pour l'affichage"
    )
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'clients_customer_tag'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_customer_tag_per_org'
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'name'], name='clients_tag_org_name_idx'),
        ]
    
    def __str__(self):
        return self.name


class CustomerTagLink(BaseClientModel):
    """Liaison many-to-many entre Customer et CustomerTag"""
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='tag_links')
    tag = models.ForeignKey(CustomerTag, on_delete=models.CASCADE, related_name='customer_links')
    
    class Meta:
        db_table = 'clients_customer_tag_link'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'customer', 'tag'],
                name='unique_customer_tag_link'
            ),
        ]
        indexes = [
            models.Index(fields=['customer'], name='clients_tag_link_customer_idx'),
            models.Index(fields=['tag'], name='clients_tag_link_tag_idx'),
        ]
    
    def clean(self):
        """Validation métier"""
        from django.core.exceptions import ValidationError
        
        # Vérifier que customer, tag et organization sont cohérents
        if self.customer and self.tag and self.organization:
            if self.customer.organization != self.organization:
                raise ValidationError('Le client doit appartenir à la même organisation.')
            if self.tag.organization != self.organization:
                raise ValidationError('Le tag doit appartenir à la même organisation.')
    
    def __str__(self):
        return f"{self.customer.name} - {self.tag.name}"


class CustomerActivity(BaseClientModel):
    """
    Activité client pour tracking (préparation roadmap 38)
    """
    
    ACTIVITY_TYPES = [
        ('contact', 'Contact'),
        ('quote', 'Devis'),
        ('order', 'Commande'),
        ('invoice', 'Facture'),
        ('payment', 'Paiement'),
        ('visit', 'Visite'),
        ('email', 'Email'),
        ('call', 'Appel'),
        ('note', 'Note'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    
    # Références optionnelles vers d'autres objets
    ref_type = models.CharField(max_length=50, blank=True, help_text="Type d'objet référencé")
    ref_id = models.UUIDField(blank=True, null=True, help_text="ID de l'objet référencé")
    
    class Meta:
        db_table = 'clients_customer_activity'
        indexes = [
            models.Index(fields=['customer', 'activity_date'], name='clients_act_cust_date_idx'),
            models.Index(fields=['organization', 'activity_type'], name='clients_act_org_type_idx'),
            models.Index(fields=['ref_type', 'ref_id'], name='clients_act_ref_idx'),
        ]
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.customer.name} - {self.title} ({self.activity_date.strftime('%d/%m/%Y')})"
