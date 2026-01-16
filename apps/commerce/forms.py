from django import forms
from .models import CommercialDocument, CommercialLine, Payment
from apps.partners.models import Partner as Customer
from apps.produits.models_catalog import SKU

class CommercialDocumentForm(forms.ModelForm):
    class Meta:
        model = CommercialDocument
        fields = [
            'type', 'date_issue', 'date_due', 'client', 'reference',
            'sale_mode', 'delivery_date_expected', 'shipping_address',
            'notes', 'internal_notes'
        ]
        widgets = {
            'date_issue': forms.DateInput(attrs={'type': 'date'}),
            'date_due': forms.DateInput(attrs={'type': 'date'}),
            'delivery_date_expected': forms.DateInput(attrs={'type': 'date'}),
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.side = kwargs.pop('side', 'sale')
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Filtrer les partenaires selon leur rôle
            qs = Customer.objects.filter(organization=self.organization, is_active=True)
            if self.side == 'sale':
                # Clients = partenaires avec rôle 'client'
                qs = qs.filter(roles__code='client')
            else:
                # Fournisseurs = partenaires avec rôle 'supplier'
                qs = qs.filter(roles__code='supplier')
                
            self.fields['client'].queryset = qs.distinct()

class InvoiceForm(CommercialDocumentForm):
    """Formulaire dédié à la création de facture"""
    class Meta(CommercialDocumentForm.Meta):
        exclude = ['type'] # On exclut le type car il est fixé
        widgets = {
            'date_issue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_due': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'delivery_date_expected': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shipping_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Adresse de livraison...'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Notes visibles sur la facture...'}),
            'internal_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Notes internes...'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'sale_mode': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence client...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        self.fields['client'].label = "Client"
        self.fields['date_issue'].label = "Date de facture"
        self.fields['sale_mode'].label = "Conditions"
        


class CommercialLineForm(forms.ModelForm):
    class Meta:
        model = CommercialLine
        fields = [
            'sku', 'description', 'quantity', 'unit_price', 
            'discount_pct', 'tax_rate', 'lot_number'
        ]
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Description ou libellé'}),
            'quantity': forms.NumberInput(attrs={'step': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.0001'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['sku'].queryset = SKU.objects.filter(organization=self.organization, is_active=True)

# Formset pour les lignes
InvoiceLineFormSet = forms.inlineformset_factory(
    CommercialDocument,
    CommercialLine,
    form=CommercialLineForm,
    extra=1,
    can_delete=True,
    fields=['sku', 'description', 'quantity', 'unit_price', 'tax_rate']
)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date', 'amount', 'method', 'reference', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
