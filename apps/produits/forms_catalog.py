from __future__ import annotations
from decimal import Decimal
from typing import Any

from django import forms

from .models_catalog import Product, SKU, ProductType, PurchaseProfile, SalesProfile
from apps.viticulture.models import Cuvee
from apps.referentiels.models import Unite
from apps.partners.models import Contact


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            # Universel
            'product_type', 'name', 'unit', 'price_eur_u', 'vat_rate', 'is_active', 'stockable',
            'source_mode',
            # Spécifiques type
            'volume_l', 'container', 'ean',
            'family', 'net_content', 'dluo', 'allergens',
            'service_category', 'duration', 'capacity',
            # Présentation
            'image', 'description',
            # Champs legacy (cachés par le template)
            'type_code', 'brand', 'slug', 'cuvee', 'tax_class', 'attrs',
        ]
        widgets = {
            'attrs': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
            # Hide legacy fields from the universal form UI
            'type_code': forms.HiddenInput(),
            'brand': forms.HiddenInput(),
            'slug': forms.HiddenInput(),
            'cuvee': forms.HiddenInput(),
            'tax_class': forms.HiddenInput(),
            'attrs': forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        # Map universel → legacy type_code pour compat
        pt = cleaned.get('product_type')
        if pt == ProductType.VIN:
            cleaned['type_code'] = 'wine'
        elif pt == ProductType.SERVICE:
            cleaned['type_code'] = 'other'
        else:
            cleaned['type_code'] = 'merch'
        return cleaned


class PurchaseArticleForm(forms.ModelForm):
    """
    Formulaire étape 1 : Création depuis le menu ACHATS.
    Champs : Nom, Unité (achat), Tags, Stockable?, Consommable?
    """
    purchase_unit = forms.ModelChoiceField(queryset=Unite.objects.all(), label="Unité d'achat", required=True)
    tags_input = forms.CharField(label="Tags", required=False, help_text="Séparés par des virgules")

    class Meta:
        model = Product
        fields = ['name', 'stockable', 'is_consumable']
        labels = {
            'name': 'Nom de l\'article',
            'stockable': 'Stockable ?',
            'is_consumable': 'Consommable ? (usage interne)'
        }

    def save(self, commit=True):
        product = super().save(commit=False)
        product.is_buyable = True
        # Par défaut, on met type "Autre" ou "Produit" si ce n'est pas spécifié, 
        # mais ici on reste générique. On peut mettre 'produit' par défaut.
        if not product.product_type:
            product.product_type = ProductType.PRODUIT
        
        # Tags processing
        tags_str = self.cleaned_data.get('tags_input', '')
        if tags_str:
            product.tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        if commit:
            product.save()
            # Créer le profil Achat
            PurchaseProfile.objects.create(
                organization=product.organization,
                product=product,
                purchase_unit=self.cleaned_data['purchase_unit']
            )
        return product


class SalesArticleForm(forms.ModelForm):
    """
    Formulaire étape 1 : Création depuis le menu VENTES.
    Champs : Nom commercial, Unité de vente, Prix, Tags.
    """
    sales_unit = forms.ModelChoiceField(queryset=Unite.objects.all(), label="Unité de vente", required=True)
    sales_price = forms.DecimalField(label="Prix de vente HT", max_digits=10, decimal_places=2, required=True)
    vat_rate = forms.DecimalField(label="TVA (%)", max_digits=5, decimal_places=2, initial=20.0)
    tags_input = forms.CharField(label="Tags", required=False, help_text="Séparés par des virgules")
    
    # Source du produit (pour la logique "Produit par vous" vs "Achat/Revente")
    SOURCE_CHOICES = [
        ('produce', 'Produit par vous (Production interne)'),
        ('buy_resell', 'Acheté puis revendu (Négoce)'),
        ('service', 'Service (Pas de stock)'),
    ]
    origin_type = forms.ChoiceField(choices=SOURCE_CHOICES, label="D'où vient ce que vous vendez ?", widget=forms.RadioSelect)

    class Meta:
        model = Product
        fields = ['name'] # On utilise 'name' comme nom commercial initialement
        labels = {'name': 'Nom commercial'}

    def save(self, commit=True):
        product = super().save(commit=False)
        product.is_sellable = True
        
        origin = self.cleaned_data.get('origin_type')
        if origin == 'service':
            product.product_type = ProductType.SERVICE
            product.stockable = False
        elif origin == 'produce':
            product.product_type = ProductType.VIN # Hypothèse par défaut, ou PRODUIT
            product.source_mode = 'domaine'
        else: # buy_resell
            product.product_type = ProductType.PRODUIT
            product.source_mode = 'negoce_bout' # ou vrac, mais bouton défaut

        # Tags
        tags_str = self.cleaned_data.get('tags_input', '')
        if tags_str:
            product.tags = [t.strip() for t in tags_str.split(',') if t.strip()]

        if commit:
            product.save()
            # Créer le profil Vente
            SalesProfile.objects.create(
                organization=product.organization,
                product=product,
                commercial_name=product.name,
                sales_unit=self.cleaned_data['sales_unit'],
                sales_price=self.cleaned_data['sales_price'],
                vat_rate=self.cleaned_data['vat_rate']
            )
        return product


class BridgePurchaseToSalesForm(forms.ModelForm):
    """
    Passerelle : Achat -> Vente (Cas C : J'achète et je revends)
    """
    tags_input = forms.CharField(label="Tags commerciaux", required=False)

    class Meta:
        model = SalesProfile
        fields = ['commercial_name', 'sales_unit', 'sales_price', 'vat_rate']
        labels = {
            'commercial_name': 'Nom commercial',
            'sales_unit': 'Unité de vente',
            'sales_price': 'Prix de vente',
            'vat_rate': 'TVA (%)'
        }

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            # Pré-remplissage intelligent
            self.fields['commercial_name'].initial = product.name
            # Tenter de récupérer l'unité d'achat si compatible
            if hasattr(product, 'purchaseprofile'):
                self.fields['sales_unit'].initial = product.purchaseprofile.purchase_unit
            self.fields['tags_input'].initial = ", ".join(product.tags)

    def save(self, product, commit=True):
        profile = super().save(commit=False)
        profile.product = product
        profile.organization = product.organization
        product.is_sellable = True
        
        # Tags update
        tags_str = self.cleaned_data.get('tags_input', '')
        if tags_str:
            new_tags = [t.strip() for t in tags_str.split(',') if t.strip()]
            # Merge tags uniquely
            current_tags = set(product.tags)
            current_tags.update(new_tags)
            product.tags = list(current_tags)
            
        if commit:
            product.save() # save is_sellable and tags
            profile.save()
        return profile


class BridgeSalesToPurchaseForm(forms.ModelForm):
    """
    Passerelle : Vente -> Achat (Cas C depuis Vente)
    """
    stockable = forms.BooleanField(label="Gérer en stock ?", required=False, initial=True)

    class Meta:
        model = PurchaseProfile
        fields = ['purchase_unit', 'main_supplier']
        labels = {
            'purchase_unit': 'Unité d\'achat',
            'main_supplier': 'Fournisseur principal'
        }

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            if hasattr(product, 'salesprofile'):
                self.fields['purchase_unit'].initial = product.salesprofile.sales_unit

    def save(self, product, commit=True):
        profile = super().save(commit=False)
        profile.product = product
        profile.organization = product.organization
        product.is_buyable = True
        product.stockable = self.cleaned_data['stockable']
        
        if commit:
            product.save()
            profile.save()
        return profile


class SKUForm(forms.ModelForm):
    class Meta:
        model = SKU
        fields = [
            'name', 'unite', 'pack_of', 'barcode', 'internal_ref',
            'default_price_ht', 'is_active'
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Order units by type then name
        self.fields['unite'].queryset = Unite.objects.order_by('type_unite', 'nom')
