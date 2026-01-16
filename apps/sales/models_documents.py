"""
Modèles pour la gestion des templates de documents
Système d'édition réutilisable pour devis, factures, commandes, etc.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.accounts.models import Organization


class DocumentTemplate(models.Model):
    """
    Template de document réutilisable
    Supporte devis, factures, commandes, bons de livraison, etc.
    """
    
    DOCUMENT_TYPES = [
        ('quote', 'Devis'),
        ('order', 'Commande'),
        ('invoice', 'Facture'),
        ('delivery', 'Bon de livraison'),
        ('proforma', 'Facture pro forma'),
        ('credit_note', 'Avoir'),
        ('receipt', 'Reçu'),
        ('estimate', 'Estimation'),
    ]
    
    PAPER_SIZES = [
        ('A4', 'A4 (210 x 297 mm)'),
        ('LETTER', 'Lettre US (216 x 279 mm)'),
        ('A5', 'A5 (148 x 210 mm)'),
    ]
    
    ORIENTATIONS = [
        ('portrait', 'Portrait'),
        ('landscape', 'Paysage'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='document_templates',
        verbose_name="Organisation"
    )
    
    # Identification
    name = models.CharField(
        max_length=200,
        help_text="Nom du template (ex: 'Devis standard', 'Facture viticole')"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        help_text="Type de document"
    )
    description = models.TextField(
        blank=True,
        help_text="Description du template"
    )
    
    # Configuration
    is_default = models.BooleanField(
        default=False,
        help_text="Template par défaut pour ce type de document"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Template actif"
    )
    
    # Mise en page
    paper_size = models.CharField(
        max_length=10,
        choices=PAPER_SIZES,
        default='A4',
        help_text="Format papier"
    )
    orientation = models.CharField(
        max_length=10,
        choices=ORIENTATIONS,
        default='portrait',
        help_text="Orientation"
    )
    margin_top = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('20.0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Marge haute (mm)"
    )
    margin_bottom = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('20.0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Marge basse (mm)"
    )
    margin_left = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('20.0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Marge gauche (mm)"
    )
    margin_right = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('20.0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Marge droite (mm)"
    )
    
    # Contenu HTML
    html_header = models.TextField(
        blank=True,
        help_text="En-tête HTML (logo, coordonnées, etc.)"
    )
    html_body = models.TextField(
        help_text="Corps du document HTML (avec variables)"
    )
    html_footer = models.TextField(
        blank=True,
        help_text="Pied de page HTML (mentions légales, CGV, etc.)"
    )
    
    # CSS personnalisé
    custom_css = models.TextField(
        blank=True,
        help_text="Styles CSS personnalisés"
    )
    
    # Configuration en blocs (nouveau builder visuel)
    blocks_config = models.JSONField(
        blank=True,
        null=True,
        default=None,
        help_text="Configuration JSON des blocs du builder visuel"
    )
    
    # Image de fond (papier à en-tête)
    background_image = models.ImageField(
        upload_to='document_templates/backgrounds/',
        blank=True,
        null=True,
        help_text="Image de fond du document (papier à en-tête)"
    )
    
    # Mode d'édition
    EDITOR_MODES = [
        ('blocks', 'Éditeur visuel (blocs)'),
        ('html', 'Éditeur HTML (avancé)'),
    ]
    editor_mode = models.CharField(
        max_length=10,
        choices=EDITOR_MODES,
        default='blocks',
        help_text="Mode d'édition du template"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates',
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Template de document"
        verbose_name_plural = "Templates de documents"
        ordering = ['document_type', '-is_default', 'name']
        unique_together = [['organization', 'name', 'document_type']]
        indexes = [
            models.Index(fields=['organization', 'document_type', 'is_default']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        default_marker = " [Défaut]" if self.is_default else ""
        return f"{self.get_document_type_display()} - {self.name}{default_marker}"
    
    def save(self, *args, **kwargs):
        # Si ce template est défini comme défaut, retirer le flag des autres
        if self.is_default:
            DocumentTemplate.objects.filter(
                organization=self.organization,
                document_type=self.document_type,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def available_variables(self):
        """
        Retourne les variables disponibles selon le type de document
        """
        base_vars = {
            'organization': {
                'name': 'Nom de l\'organisation',
                'address': 'Adresse',
                'postal_code': 'Code postal',
                'city': 'Ville',
                'country': 'Pays',
                'phone': 'Téléphone',
                'email': 'Email',
                'website': 'Site web',
                'vat_number': 'Numéro TVA',
                'siret': 'SIRET',
            },
            'customer': {
                'legal_name': 'Nom/Raison sociale',
                'billing_address': 'Adresse facturation',
                'billing_postal_code': 'Code postal facturation',
                'billing_city': 'Ville facturation',
                'billing_country': 'Pays facturation',
                'vat_number': 'Numéro TVA client',
            },
            'document': {
                'number': 'Numéro du document',
                'date': 'Date',
                'date_issue': 'Date d\'émission',
                'valid_until': 'Valable jusqu\'au',
                'due_date': 'Date d\'échéance',
                'currency': 'Devise',
                'status': 'Statut',
            },
            'totals': {
                'total_ht': 'Total HT',
                'total_tax': 'Total TVA',
                'total_ttc': 'Total TTC',
            },
            'lines': 'Liste des lignes (tableau)',
        }
        
        # Variables spécifiques au type de document
        if self.document_type in ['quote', 'estimate']:
            base_vars['document']['reference'] = 'Référence devis'
        elif self.document_type == 'order':
            base_vars['document']['delivery_date'] = 'Date de livraison'
            base_vars['document']['payment_method'] = 'Mode de paiement'
        elif self.document_type == 'invoice':
            base_vars['document']['payment_terms'] = 'Conditions de paiement'
            base_vars['document']['invoice_number'] = 'Numéro de facture'
        elif self.document_type == 'delivery':
            base_vars['document']['delivery_address'] = 'Adresse de livraison'
            base_vars['document']['carrier'] = 'Transporteur'
        
        return base_vars
    
    def get_variable_help_text(self):
        """
        Retourne un texte d'aide pour les variables disponibles
        """
        help_lines = []
        for category, vars_dict in self.available_variables.items():
            if isinstance(vars_dict, dict):
                help_lines.append(f"\n{category.upper()}:")
                for var, desc in vars_dict.items():
                    help_lines.append(f"  {{{{ {category}.{var} }}}} - {desc}")
            else:
                help_lines.append(f"\n{{{{ {category} }}}} - {vars_dict}")
        
        return '\n'.join(help_lines)


class DocumentPreset(models.Model):
    """
    Presets de configuration pour les documents
    (couleurs, polices, styles prédéfinis)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='document_presets',
        verbose_name="Organisation"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Nom du preset (ex: 'Viticole bordeaux', 'Moderne épuré')"
    )
    description = models.TextField(blank=True)
    
    # Couleurs
    primary_color = models.CharField(
        max_length=7,
        default='#8B1538',
        help_text="Couleur primaire (hex)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#d4af37',
        help_text="Couleur secondaire (hex)"
    )
    text_color = models.CharField(
        max_length=7,
        default='#333333',
        help_text="Couleur du texte (hex)"
    )
    
    # Polices
    font_family = models.CharField(
        max_length=200,
        default='Inter, sans-serif',
        help_text="Police principale"
    )
    font_size_base = models.IntegerField(
        default=10,
        help_text="Taille de police de base (pt)"
    )
    
    # Logo
    logo_width = models.IntegerField(
        default=150,
        help_text="Largeur du logo (px)"
    )
    logo_position = models.CharField(
        max_length=10,
        choices=[('left', 'Gauche'), ('center', 'Centre'), ('right', 'Droite')],
        default='left',
        help_text="Position du logo"
    )
    
    # CSS généré
    generated_css = models.TextField(
        blank=True,
        help_text="CSS généré automatiquement à partir des paramètres"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preset de document"
        verbose_name_plural = "Presets de documents"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def generate_css(self):
        """
        Génère le CSS à partir des paramètres du preset
        """
        css = f"""
:root {{
    --primary-color: {self.primary_color};
    --secondary-color: {self.secondary_color};
    --text-color: {self.text_color};
    --font-family: {self.font_family};
    --font-size-base: {self.font_size_base}pt;
}}

body {{
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    color: var(--text-color);
}}

.header {{
    border-bottom: 2px solid var(--primary-color);
}}

.logo {{
    width: {self.logo_width}px;
    text-align: {self.logo_position};
}}

h1, h2, h3 {{
    color: var(--primary-color);
}}

.total-row {{
    background-color: {self.primary_color}15;
    border-top: 2px solid var(--primary-color);
}}

.highlight {{
    color: var(--secondary-color);
    font-weight: bold;
}}
        """
        
        return css.strip()
    
    def save(self, *args, **kwargs):
        # Générer le CSS automatiquement
        self.generated_css = self.generate_css()
        super().save(*args, **kwargs)
