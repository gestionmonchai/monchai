from django import forms
from .models import CommercialDocument, CommercialLine, Payment
from apps.clients.models import Customer
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
            # Filtrer les clients selon le side
            qs = Customer.objects.filter(organization=self.organization)
            if self.side == 'sale':
                # Tous sauf ceux marqués uniquement fournisseurs (si logique exclusive, ici on prend tout pour simplifier ou exclure supplier pur ?)
                # Le modèle Customer a un segment. 
                # segment='supplier' -> Fournisseur. 
                # segment='business'/'individual' -> Client.
                qs = qs.exclude(segment='supplier')
            else:
                qs = qs.filter(segment='supplier')
                
            self.fields['client'].queryset = qs

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

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date', 'amount', 'method', 'reference', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
