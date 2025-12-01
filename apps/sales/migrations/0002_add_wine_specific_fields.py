# Generated migration for wine-specific fields
from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        # ========================================
        # CUSTOMER - Segments professionnels
        # ========================================
        migrations.AddField(
            model_name='customer',
            name='customer_segment',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('particulier', 'Particulier'),
                    ('caviste', 'Caviste'),
                    ('restaurant', 'Restaurant / CHR'),
                    ('grossiste', 'Grossiste'),
                    ('export', 'Export / Importateur'),
                    ('oenotourisme', 'Œnotourisme / Hôtel'),
                ],
                default='particulier',
                help_text="Segment client pour tarification"
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='tax_regime',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('normal', 'TVA normale'),
                    ('autoliquidation', 'Autoliquidation UE'),
                    ('export', 'Export hors UE'),
                ],
                default='normal',
                help_text="Régime fiscal"
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='requires_dae',
            field=models.BooleanField(
                default=False,
                help_text="Nécessite Document Accompagnement Export"
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='allocation_priority',
            field=models.PositiveIntegerField(
                default=5,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(10)
                ],
                help_text="Priorité allocation (1=VIP, 10=standard)"
            ),
        ),
        
        # ========================================
        # QUOTE - Vente en primeur
        # ========================================
        migrations.AddField(
            model_name='quote',
            name='is_primeur',
            field=models.BooleanField(
                default=False,
                help_text="Vente en primeur (livraison différée)"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='vintage_year',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text="Année du millésime"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='expected_delivery_date',
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Date de livraison prévue (primeur)"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='primeur_campaign',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Nom de la campagne primeur (ex: Primeur 2024)"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='primeur_discount_pct',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal('0'),
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('100'))
                ],
                help_text="Remise primeur en %"
            ),
        ),
        
        # Livraison
        migrations.AddField(
            model_name='quote',
            name='delivery_method',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('retrait', 'Retrait à la cave'),
                    ('local', 'Livraison locale'),
                    ('transporteur', 'Transporteur national'),
                    ('export', 'Export international'),
                    ('coursier', 'Coursier express'),
                ],
                default='retrait',
                help_text="Mode de livraison"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='delivery_cost',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal('0'),
                help_text="Frais de port"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='delivery_notes',
            field=models.TextField(
                blank=True,
                help_text="Instructions de livraison"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='requires_signature',
            field=models.BooleanField(
                default=False,
                help_text="Signature requise à la livraison"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='temperature_controlled',
            field=models.BooleanField(
                default=False,
                help_text="Transport réfrigéré (été)"
            ),
        ),
        
        # Réglementation
        migrations.AddField(
            model_name='quote',
            name='age_verification',
            field=models.BooleanField(
                default=False,
                help_text="Vérification âge 18+ effectuée"
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='campaign',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Campagne marketing (portes ouvertes, salon...)"
            ),
        ),
        
        # ========================================
        # ORDER - Mêmes champs que Quote
        # ========================================
        migrations.AddField(
            model_name='order',
            name='is_primeur',
            field=models.BooleanField(
                default=False,
                help_text="Vente en primeur (livraison différée)"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='vintage_year',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text="Année du millésime"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='expected_delivery_date',
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Date de livraison prévue (primeur)"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='actual_delivery_date',
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Date de livraison effective"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='primeur_campaign',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Nom de la campagne primeur"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='primeur_discount_pct',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal('0'),
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('100'))
                ],
                help_text="Remise primeur en %"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_method',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('retrait', 'Retrait à la cave'),
                    ('local', 'Livraison locale'),
                    ('transporteur', 'Transporteur national'),
                    ('export', 'Export international'),
                    ('coursier', 'Coursier express'),
                ],
                default='retrait',
                help_text="Mode de livraison"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_cost',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal('0'),
                help_text="Frais de port"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_notes',
            field=models.TextField(
                blank=True,
                help_text="Instructions de livraison"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='tracking_number',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Numéro de suivi colis"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='requires_signature',
            field=models.BooleanField(
                default=False,
                help_text="Signature requise à la livraison"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='temperature_controlled',
            field=models.BooleanField(
                default=False,
                help_text="Transport réfrigéré (été)"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='age_verification',
            field=models.BooleanField(
                default=False,
                help_text="Vérification âge 18+ effectuée"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='campaign',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Campagne marketing"
            ),
        ),
        
        # ========================================
        # QUOTELINE - Détails viticoles
        # ========================================
        migrations.AddField(
            model_name='quoteline',
            name='vintage_year',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text="Millésime du vin"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='format',
            field=models.CharField(
                max_length=20,
                default='75cl',
                help_text="Format (75cl, 150cl, 300cl...)"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='format_label',
            field=models.CharField(
                max_length=50,
                default='Bouteille',
                help_text="Libellé format (Bouteille, Magnum...)"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='appellation',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Appellation (AOC, IGP...)"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='alcohol_degree',
            field=models.DecimalField(
                max_digits=4,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Degré alcoolique (% vol.)"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='lot_number',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text="Numéro de lot (traçabilité)"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='crd_number',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text="Numéro capsule CRD"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='packaging_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('unite', 'À l\'unité'),
                    ('carton_6', 'Carton de 6'),
                    ('carton_12', 'Carton de 12'),
                    ('palette', 'Palette'),
                ],
                default='unite',
                help_text="Type de conditionnement"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='packaging_notes',
            field=models.TextField(
                blank=True,
                help_text="Instructions emballage spécial"
            ),
        ),
        migrations.AddField(
            model_name='quoteline',
            name='is_sample',
            field=models.BooleanField(
                default=False,
                help_text="Échantillon gratuit"
            ),
        ),
        
        # ========================================
        # ORDERLINE - Mêmes champs que QuoteLine
        # ========================================
        migrations.AddField(
            model_name='orderline',
            name='vintage_year',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text="Millésime du vin"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='format',
            field=models.CharField(
                max_length=20,
                default='75cl',
                help_text="Format (75cl, 150cl, 300cl...)"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='format_label',
            field=models.CharField(
                max_length=50,
                default='Bouteille',
                help_text="Libellé format (Bouteille, Magnum...)"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='appellation',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text="Appellation (AOC, IGP...)"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='alcohol_degree',
            field=models.DecimalField(
                max_digits=4,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Degré alcoolique (% vol.)"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='lot_number',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text="Numéro de lot (traçabilité)"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='crd_number',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text="Numéro capsule CRD"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='packaging_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('unite', 'À l\'unité'),
                    ('carton_6', 'Carton de 6'),
                    ('carton_12', 'Carton de 12'),
                    ('palette', 'Palette'),
                ],
                default='unite',
                help_text="Type de conditionnement"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='packaging_notes',
            field=models.TextField(
                blank=True,
                help_text="Instructions emballage spécial"
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='is_sample',
            field=models.BooleanField(
                default=False,
                help_text="Échantillon gratuit"
            ),
        ),
        
        # ========================================
        # INDEX pour performance
        # ========================================
        migrations.AddIndex(
            model_name='quote',
            index=models.Index(fields=['organization', 'is_primeur', 'vintage_year'], name='sales_quote_primeur_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['organization', 'is_primeur', 'expected_delivery_date'], name='sales_order_primeur_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['organization', 'customer_segment'], name='sales_customer_segment_idx'),
        ),
    ]
