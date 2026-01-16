"""
Modèles pour la gestion unifiée des contacts (tiers)
Un Contact peut avoir plusieurs rôles : CLIENT, FOURNISSEUR, PROSPECT, TRANSPORTEUR, etc.

NOTE: Le modèle était anciennement nommé 'Partner'. Des alias sont conservés
pour la rétrocompatibilité.
"""

import uuid
import re
from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from apps.accounts.models import Organization


# =============================================================================
# MODÈLE DE BASE
# =============================================================================

class BasePartnerModel(models.Model):
    """Modèle de base pour tous les modèles partners"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='partners_%(class)s_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_version = models.PositiveIntegerField(default=1)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if self.pk and self._state.adding is False:
            self.row_version += 1
        super().save(*args, **kwargs)


# =============================================================================
# RÔLES DES CONTACTS
# =============================================================================

class ContactRole(models.Model):
    """
    Rôles possibles pour un partenaire.
    Table de référence avec rôles prédéfinis + possibilité d'en ajouter.
    """
    ROLE_CLIENT = 'client'
    ROLE_SUPPLIER = 'supplier'
    ROLE_PROSPECT = 'prospect'
    ROLE_CARRIER = 'carrier'
    ROLE_SUBCONTRACTOR = 'subcontractor'
    ROLE_OTHER = 'other'
    
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_SUPPLIER, 'Fournisseur'),
        (ROLE_PROSPECT, 'Prospect'),
        (ROLE_CARRIER, 'Transporteur'),
        (ROLE_SUBCONTRACTOR, 'Prestataire'),
        (ROLE_OTHER, 'Autre'),
    ]
    
    code = models.CharField(max_length=20, choices=ROLE_CHOICES, primary_key=True)
    label = models.CharField(max_length=50)
    icon = models.CharField(max_length=30, default='bi-person')
    color = models.CharField(max_length=20, default='secondary')
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'partners_role'
        ordering = ['sort_order', 'label']
        verbose_name = 'Rôle partenaire'
        verbose_name_plural = 'Rôles partenaires'
    
    def __str__(self):
        return self.label
    
    @classmethod
    def ensure_defaults(cls):
        """Crée les rôles par défaut s'ils n'existent pas"""
        defaults = [
            {'code': cls.ROLE_CLIENT, 'label': 'Client', 'icon': 'bi-person-check', 'color': 'primary', 'sort_order': 1},
            {'code': cls.ROLE_SUPPLIER, 'label': 'Fournisseur', 'icon': 'bi-truck', 'color': 'success', 'sort_order': 2},
            {'code': cls.ROLE_PROSPECT, 'label': 'Prospect', 'icon': 'bi-person-plus', 'color': 'warning', 'sort_order': 3},
            {'code': cls.ROLE_CARRIER, 'label': 'Transporteur', 'icon': 'bi-box-seam', 'color': 'info', 'sort_order': 4},
            {'code': cls.ROLE_SUBCONTRACTOR, 'label': 'Prestataire', 'icon': 'bi-tools', 'color': 'secondary', 'sort_order': 5},
            {'code': cls.ROLE_OTHER, 'label': 'Autre', 'icon': 'bi-person', 'color': 'dark', 'sort_order': 99},
        ]
        for data in defaults:
            cls.objects.get_or_create(code=data['code'], defaults=data)


# =============================================================================
# CONTACT (TIERS UNIFIÉ)
# =============================================================================

class Contact(BasePartnerModel):
    """
    Modèle central unifié pour tous les tiers :
    - Clients
    - Fournisseurs
    - Prospects
    - Transporteurs
    - Prestataires
    
    Un même Contact peut avoir PLUSIEURS rôles.
    """
    
    # Type de personne
    TYPE_INDIVIDUAL = 'individual'
    TYPE_COMPANY = 'company'
    TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, 'Personne physique'),
        (TYPE_COMPANY, 'Personne morale'),
    ]
    
    # Segment commercial (pour les clients)
    SEGMENT_CHOICES = [
        ('individual', 'Particulier'),
        ('business', 'Professionnel'),
        ('wine_shop', 'Caviste'),
        ('export', 'Export'),
        ('restaurant', 'CHR'),
        ('distributor', 'Distributeur'),
        ('other', 'Autre'),
    ]
    
    # --- Identification ---
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Code unique auto-généré (PAR-00001)"
    )
    display_id = models.PositiveIntegerField(
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Identifiant numérique court pour URLs"
    )
    
    # --- Type et identité ---
    partner_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_COMPANY,
        help_text="Personne physique ou morale"
    )
    
    # Nom principal
    name = models.CharField(
        max_length=200,
        help_text="Raison sociale ou Nom complet"
    )
    name_normalized = models.CharField(
        max_length=200,
        editable=False,
        help_text="Nom normalisé pour recherche"
    )
    
    # Pour les personnes physiques
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Segment commercial
    segment = models.CharField(
        max_length=20,
        choices=SEGMENT_CHOICES,
        blank=True,
        help_text="Segment commercial (optionnel)"
    )
    
    # --- Rôles (M2M) ---
    roles = models.ManyToManyField(
        ContactRole,
        related_name='contacts',
        blank=True,
        help_text="Rôles du partenaire (client, fournisseur, etc.)"
    )
    
    # --- Coordonnées principales ---
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, help_text="Téléphone principal")
    mobile = models.CharField(max_length=30, blank=True, help_text="Téléphone mobile")
    website = models.URLField(max_length=200, blank=True)
    
    # --- Identification légale ---
    siret = models.CharField(max_length=14, blank=True, help_text="SIRET (14 chiffres)")
    siren = models.CharField(max_length=9, blank=True, help_text="SIREN (9 chiffres)")
    vat_number = models.CharField(max_length=20, blank=True, help_text="N° TVA intracommunautaire")
    naf_code = models.CharField(max_length=10, blank=True, help_text="Code NAF/APE")
    
    # --- Localisation ---
    country_code = models.CharField(max_length=2, default='FR', help_text="Code pays ISO")
    language = models.CharField(max_length=5, default='fr', help_text="Langue préférée")
    timezone = models.CharField(max_length=50, default='Europe/Paris')
    currency = models.CharField(max_length=3, default='EUR', help_text="Devise par défaut")
    
    # --- Statut ---
    is_active = models.BooleanField(default=True, help_text="Partenaire actif")
    is_archived = models.BooleanField(default=False, help_text="Archivé (masqué par défaut)")
    
    # --- Notes et tags ---
    notes = models.TextField(blank=True, help_text="Notes internes")
    internal_ref = models.CharField(max_length=50, blank=True, help_text="Référence interne libre")
    
    # --- Recherche full-text ---
    search_vector = SearchVectorField(null=True, blank=True)
    
    # --- Métadonnées ---
    source = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Source d'acquisition (import, site web, salon...)"
    )
    
    class Meta:
        db_table = 'partners_partner'
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['name']
        indexes = [
            GinIndex(fields=['name_normalized'], name='partner_name_gin'),
            GinIndex(fields=['search_vector'], name='partner_search_gin'),
            models.Index(fields=['organization', 'is_active'], name='partner_org_active_idx'),
            models.Index(fields=['organization', 'segment'], name='partner_org_segment_idx'),
            models.Index(fields=['organization', 'updated_at', 'id'], name='partner_keyset_idx'),
            models.Index(fields=['vat_number'], name='partner_vat_idx'),
            models.Index(fields=['siret'], name='partner_siret_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name_normalized'],
                name='unique_partner_name_per_org'
            ),
            models.UniqueConstraint(
                fields=['organization', 'vat_number'],
                name='unique_partner_vat_per_org',
                condition=models.Q(vat_number__isnull=False) & ~models.Q(vat_number='')
            ),
        ]
    
    def __str__(self):
        roles_str = ', '.join(r.label for r in self.roles.all()[:2])
        if roles_str:
            return f"{self.name} ({roles_str})"
        return self.name
    
    def save(self, *args, **kwargs):
        # Normalisation du nom
        self.name_normalized = self._normalize_name(self.name)
        
        # Génération code si nouveau
        if not self.code:
            self.code = self._generate_code()
        
        if not self.display_id:
            self.display_id = self._generate_display_id()
        
        # Normalisation TVA
        if self.vat_number:
            self.vat_number = self.vat_number.upper().replace(' ', '')
        
        # Extraction SIREN depuis SIRET
        if self.siret and len(self.siret) == 14 and not self.siren:
            self.siren = self.siret[:9]
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def _normalize_name(name):
        """Normalise le nom pour recherche et déduplication"""
        if not name:
            return ''
        # Lowercase, suppression accents et caractères spéciaux
        import unicodedata
        normalized = unicodedata.normalize('NFKD', name.lower())
        normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
        # Garder uniquement alphanum et espaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        # Normaliser espaces
        return ' '.join(normalized.split())
    
    def _generate_code(self):
        """Génère un code unique CON-00001"""
        prefix = "CON-"
        last = Contact.objects.filter(code__startswith=prefix).order_by('-code').first()
        if last and last.code:
            try:
                num = int(last.code.split(prefix)[-1])
            except ValueError:
                num = 0
        else:
            num = 0
        return f"{prefix}{num + 1:05d}"
    
    def _generate_display_id(self):
        """Génère un ID numérique court"""
        last_id = Contact.objects.exclude(display_id__isnull=True).order_by('-display_id').values_list('display_id', flat=True).first() or 0
        return last_id + 1
    
    # --- Helpers rôles ---
    @property
    def is_client(self):
        return self.roles.filter(code=ContactRole.ROLE_CLIENT).exists()
    
    @property
    def is_supplier(self):
        return self.roles.filter(code=ContactRole.ROLE_SUPPLIER).exists()
    
    @property
    def is_prospect(self):
        return self.roles.filter(code=ContactRole.ROLE_PROSPECT).exists()
    
    @property
    def is_carrier(self):
        return self.roles.filter(code=ContactRole.ROLE_CARRIER).exists()
    
    def add_role(self, role_code):
        """Ajoute un rôle au contact"""
        role, _ = ContactRole.objects.get_or_create(code=role_code)
        self.roles.add(role)
    
    def remove_role(self, role_code):
        """Retire un rôle au contact"""
        self.roles.filter(code=role_code).delete()
    
    @property
    def role_codes(self):
        """Liste des codes de rôles"""
        return list(self.roles.values_list('code', flat=True))
    
    # --- Adresse principale ---
    @property
    def primary_address(self):
        """Retourne l'adresse principale (facturation par défaut)"""
        return self.addresses.filter(is_default=True).first() or self.addresses.first()
    
    @property
    def billing_address(self):
        """Adresse de facturation"""
        return self.addresses.filter(address_type='billing').first() or self.primary_address
    
    @property
    def shipping_address(self):
        """Adresse de livraison"""
        return self.addresses.filter(address_type='shipping').first() or self.primary_address
    
    # --- Contact principal ---
    @property
    def primary_contact(self):
        """Contact principal (interlocuteur)"""
        return self.contact_persons.filter(is_primary=True).first() or self.contact_persons.first()
    
    # --- Helpers affichage ---
    @property
    def display_name(self):
        """Nom d'affichage complet"""
        if self.partner_type == self.TYPE_INDIVIDUAL and self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.name
    
    @property
    def short_name(self):
        """Nom court"""
        if len(self.name) > 30:
            return self.name[:27] + '...'
        return self.name
    
    @property
    def roles_display(self):
        """Affichage des rôles"""
        return ', '.join(r.label for r in self.roles.all())
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('partners:partner_detail', kwargs={'display_id': self.display_id})


# =============================================================================
# ADRESSES
# =============================================================================

class Address(BasePartnerModel):
    """
    Adresses multiples pour un contact.
    Types : facturation, livraison, siège, autre.
    """
    ADDRESS_TYPE_CHOICES = [
        ('billing', 'Facturation'),
        ('shipping', 'Livraison'),
        ('headquarters', 'Siège social'),
        ('warehouse', 'Entrepôt'),
        ('other', 'Autre'),
    ]
    
    partner = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    
    label = models.CharField(max_length=100, blank=True, help_text="Libellé (ex: Siège Paris)")
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default='billing'
    )
    is_default = models.BooleanField(default=False, help_text="Adresse par défaut")
    
    # Adresse
    street = models.CharField(max_length=200, help_text="Rue et numéro")
    street2 = models.CharField(max_length=200, blank=True, help_text="Complément d'adresse")
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, help_text="Région/État")
    country = models.CharField(max_length=2, default='FR', help_text="Code pays ISO")
    
    # Contact livraison
    contact_name = models.CharField(max_length=100, blank=True, help_text="Nom du contact sur site")
    contact_phone = models.CharField(max_length=30, blank=True, help_text="Téléphone contact")
    
    # Instructions livraison
    delivery_instructions = models.TextField(blank=True, help_text="Instructions de livraison")
    delivery_hours = models.CharField(max_length=100, blank=True, help_text="Créneaux horaires")
    
    # Géolocalisation
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    class Meta:
        db_table = 'partners_address'
        verbose_name = 'Adresse'
        verbose_name_plural = 'Adresses'
        ordering = ['-is_default', 'address_type', 'label']
        indexes = [
            models.Index(fields=['partner', 'address_type']),
            models.Index(fields=['postal_code']),
        ]
    
    def __str__(self):
        return f"{self.label or self.get_address_type_display()} - {self.city}"
    
    @property
    def full_address(self):
        """Adresse complète sur une ligne"""
        parts = [self.street]
        if self.street2:
            parts.append(self.street2)
        parts.append(f"{self.postal_code} {self.city}")
        if self.country != 'FR':
            parts.append(self.country)
        return ', '.join(parts)
    
    @property
    def multiline_address(self):
        """Adresse sur plusieurs lignes"""
        lines = [self.street]
        if self.street2:
            lines.append(self.street2)
        lines.append(f"{self.postal_code} {self.city}")
        if self.country != 'FR':
            lines.append(self.country)
        return '\n'.join(lines)
    
    def save(self, *args, **kwargs):
        # Si is_default, retirer le default des autres
        if self.is_default:
            Address.objects.filter(
                partner=self.partner,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# =============================================================================
# INTERLOCUTEURS (CONTACTS)
# =============================================================================

class ContactPerson(BasePartnerModel):
    """
    Interlocuteurs liés à un contact.
    Ex: acheteur, comptable, commercial, etc.
    """
    ROLE_CHOICES = [
        ('general', 'Contact général'),
        ('buyer', 'Acheteur'),
        ('seller', 'Commercial'),
        ('accounting', 'Comptabilité'),
        ('logistics', 'Logistique'),
        ('technical', 'Technique'),
        ('management', 'Direction'),
        ('other', 'Autre'),
    ]
    
    partner = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='contact_persons'
    )
    
    # Identité
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True, help_text="Fonction")
    department = models.CharField(max_length=100, blank=True, help_text="Service")
    
    # Coordonnées
    email = models.EmailField(max_length=254, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    
    # Rôle et statut
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='general')
    is_primary = models.BooleanField(default=False, help_text="Contact principal")
    is_active = models.BooleanField(default=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'partners_contact_person'
        verbose_name = 'Interlocuteur'
        verbose_name_plural = 'Interlocuteurs'
        ordering = ['-is_primary', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['partner', 'role']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.job_title or self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Si is_primary, retirer le primary des autres
        if self.is_primary:
            ContactPerson.objects.filter(
                partner=self.partner,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# =============================================================================
# PROFIL CLIENT (données spécifiques ventes)
# =============================================================================

class ClientProfile(BasePartnerModel):
    """
    Profil client avec données spécifiques aux ventes.
    OneToOne avec Contact (créé quand rôle CLIENT ajouté).
    """
    PAYMENT_TERMS_CHOICES = [
        ('immediate', 'Comptant'),
        ('15d', '15 jours'),
        ('30d', '30 jours'),
        ('45d', '45 jours'),
        ('60d', '60 jours'),
        ('end_of_month', 'Fin de mois'),
        ('custom', 'Personnalisé'),
    ]
    
    PRICE_CATEGORY_CHOICES = [
        ('public', 'Tarif public'),
        ('pro', 'Tarif pro'),
        ('export', 'Tarif export'),
        ('custom', 'Tarif spécial'),
    ]
    
    partner = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    
    # Conditions commerciales
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='30d'
    )
    payment_terms_custom = models.CharField(max_length=100, blank=True)
    
    price_category = models.CharField(
        max_length=20,
        choices=PRICE_CATEGORY_CHOICES,
        default='public'
    )
    
    default_discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Remise par défaut (%)"
    )
    
    # Encours
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Plafond d'encours autorisé"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Encours actuel (calculé)"
    )
    
    # Comptabilité
    accounting_code = models.CharField(max_length=20, blank=True, help_text="Compte comptable client")
    
    # Statistiques (dénormalisées pour perfs)
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
        help_text="CA total cumulé"
    )
    total_orders = models.PositiveIntegerField(default=0, help_text="Nombre total de commandes")
    last_order_date = models.DateField(null=True, blank=True)
    average_basket = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Panier moyen"
    )
    
    # Préférences
    preferred_shipping_method = models.CharField(max_length=50, blank=True)
    preferred_carrier = models.CharField(max_length=100, blank=True)
    
    # Documents
    cgv_accepted = models.BooleanField(default=False)
    cgv_accepted_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'partners_client_profile'
        verbose_name = 'Profil client'
        verbose_name_plural = 'Profils clients'
    
    def __str__(self):
        return f"Profil client: {self.partner.name}"
    
    @property
    def available_credit(self):
        """Crédit disponible"""
        return max(Decimal('0'), self.credit_limit - self.current_balance)
    
    @property
    def is_over_limit(self):
        """Encours dépassé ?"""
        return self.current_balance > self.credit_limit > 0


# =============================================================================
# PROFIL FOURNISSEUR (données spécifiques achats)
# =============================================================================

class SupplierProfile(BasePartnerModel):
    """
    Profil fournisseur avec données spécifiques aux achats.
    OneToOne avec Contact (créé quand rôle FOURNISSEUR ajouté).
    """
    PAYMENT_TERMS_CHOICES = [
        ('immediate', 'Comptant'),
        ('15d', '15 jours'),
        ('30d', '30 jours'),
        ('45d', '45 jours'),
        ('60d', '60 jours'),
        ('end_of_month', 'Fin de mois'),
        ('custom', 'Personnalisé'),
    ]
    
    INCOTERM_CHOICES = [
        ('exw', 'EXW - Ex Works'),
        ('fca', 'FCA - Free Carrier'),
        ('cpt', 'CPT - Carriage Paid To'),
        ('cip', 'CIP - Carriage Insurance Paid'),
        ('dap', 'DAP - Delivered at Place'),
        ('dpu', 'DPU - Delivered at Place Unloaded'),
        ('ddp', 'DDP - Delivered Duty Paid'),
        ('fob', 'FOB - Free on Board'),
        ('cif', 'CIF - Cost Insurance Freight'),
    ]
    
    partner = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name='supplier_profile'
    )
    
    # Conditions d'achat
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='30d'
    )
    payment_terms_custom = models.CharField(max_length=100, blank=True)
    
    incoterm = models.CharField(
        max_length=10,
        choices=INCOTERM_CHOICES,
        blank=True
    )
    
    # Délais
    lead_time_days = models.PositiveIntegerField(
        default=0,
        help_text="Délai de livraison moyen (jours)"
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Montant minimum de commande"
    )
    
    # Comptabilité
    accounting_code = models.CharField(max_length=20, blank=True, help_text="Compte comptable fournisseur")
    
    # Statistiques
    total_purchases = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Total achats cumulé"
    )
    total_orders = models.PositiveIntegerField(default=0, help_text="Nombre total de commandes")
    last_order_date = models.DateField(null=True, blank=True)
    
    # Qualité
    quality_rating = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(5)],
        help_text="Note qualité (0-5)"
    )
    is_approved = models.BooleanField(default=False, help_text="Fournisseur agréé")
    approval_date = models.DateField(null=True, blank=True)
    
    # Catégories produits
    product_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Catégories de produits fournis"
    )
    
    class Meta:
        db_table = 'partners_supplier_profile'
        verbose_name = 'Profil fournisseur'
        verbose_name_plural = 'Profils fournisseurs'
    
    def __str__(self):
        return f"Profil fournisseur: {self.partner.name}"


# =============================================================================
# TAGS CONTACTS
# =============================================================================

class ContactTag(BasePartnerModel):
    """Tags pour catégoriser les contacts"""
    
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6c757d')
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'partners_tag'
        verbose_name = 'Tag partenaire'
        verbose_name_plural = 'Tags partenaires'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_partner_tag_per_org'
            ),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ContactTagLink(models.Model):
    """Liaison M2M Contact <-> Tag"""
    
    partner = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='tag_links')
    tag = models.ForeignKey(ContactTag, on_delete=models.CASCADE, related_name='contact_links')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'partners_tag_link'
        unique_together = ['partner', 'tag']
    
    def __str__(self):
        return f"{self.partner.name} - {self.tag.name}"


# =============================================================================
# HISTORIQUE / TIMELINE
# =============================================================================

class ContactEvent(BasePartnerModel):
    """
    Événements liés à un contact (timeline).
    Devis, commandes, factures, notes, appels, emails, etc.
    """
    EVENT_TYPES = [
        ('note', 'Note'),
        ('call', 'Appel'),
        ('email', 'Email'),
        ('meeting', 'Rendez-vous'),
        ('quote', 'Devis'),
        ('order', 'Commande'),
        ('delivery', 'Livraison'),
        ('invoice', 'Facture'),
        ('payment', 'Paiement'),
        ('complaint', 'Réclamation'),
        ('other', 'Autre'),
    ]
    
    partner = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='note')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField(default=timezone.now)
    
    # Référence vers objet lié (générique)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)
    
    # Auteur
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partner_events_created'
    )
    
    class Meta:
        db_table = 'partners_event'
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['partner', 'event_type']),
            models.Index(fields=['partner', '-event_date']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"


# =============================================================================
# ALIAS POUR RÉTROCOMPATIBILITÉ
# =============================================================================
# Ces alias permettent la compatibilité avec le code existant
# qui utilise encore les anciens noms Partner, PartnerRole, etc.

Partner = Contact
PartnerRole = ContactRole
PartnerTag = ContactTag
PartnerTagLink = ContactTagLink
PartnerEvent = ContactEvent
Customer = Contact  # Alias legacy depuis apps.clients
