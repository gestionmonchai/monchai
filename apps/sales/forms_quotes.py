from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from apps.sales.models import Quote, QuoteLine, TaxCode
from apps.stock.models import SKU
from apps.sales.models import Customer as SalesCustomer


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = [
            'customer',
            'currency',
            'valid_until',
            'status',
        ]
        widgets = {
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields['customer'].queryset = SalesCustomer.objects.filter(organization=organization, is_active=True)
        self.fields['currency'].initial = self.fields['currency'].initial or 'EUR'
        self.fields['status'].initial = self.fields['status'].initial or 'draft'


class QuoteLineForm(forms.ModelForm):
    class Meta:
        model = QuoteLine
        fields = [
            'sku',
            'description',
            'qty',
            'unit_price',
            'discount_pct',
            'tax_code',
        ]

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields['sku'].queryset = SKU.objects.filter(organization=organization, is_active=True)
            self.fields['tax_code'].queryset = TaxCode.objects.filter(organization=organization, is_active=True)
            # Default tax code = TVA20 if exists, else first active
            try:
                default_tc = TaxCode.objects.filter(organization=organization, code='TVA20', is_active=True).first() or \
                             TaxCode.objects.filter(organization=organization, is_active=True).order_by('-rate_pct').first()
                if default_tc and not getattr(self.instance, 'tax_code_id', None):
                    self.fields['tax_code'].initial = default_tc.id
            except Exception:
                pass

    def clean(self):
        cleaned = super().clean()
        sku = cleaned.get('sku')
        description = cleaned.get('description')
        if not sku and not description:
            raise ValidationError('Spécifiez un produit (SKU) ou une description pour un service.')
        return cleaned


QuoteLineFormSet = inlineformset_factory(
    parent_model=Quote,
    model=QuoteLine,
    form=QuoteLineForm,
    extra=5,
    can_delete=True,
    fields=['sku', 'description', 'qty', 'unit_price', 'discount_pct', 'tax_code'],
)
