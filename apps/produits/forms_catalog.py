from __future__ import annotations
from decimal import Decimal
from typing import Any

from django import forms

from .models_catalog import Product, SKU, ProductType
from apps.viticulture.models import Cuvee
from apps.referentiels.models import Unite


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
