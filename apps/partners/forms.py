"""
Formulaires pour la gestion des partenaires
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Partner, PartnerRole, Address, ContactPerson,
    ClientProfile, SupplierProfile, PartnerTag
)


class PartnerForm(forms.ModelForm):
    """Formulaire principal de création/édition d'un partenaire"""
    
    roles = forms.ModelMultipleChoiceField(
        queryset=PartnerRole.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Rôles"
    )
    
    class Meta:
        model = Partner
        fields = [
            'partner_type', 'name', 'first_name', 'last_name',
            'segment', 'roles',
            'email', 'phone', 'mobile', 'website',
            'siret', 'vat_number', 'naf_code',
            'country_code', 'language', 'currency',
            'is_active', 'notes', 'internal_ref', 'source'
        ]
        widgets = {
            'partner_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Raison sociale ou Nom'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'segment': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+33 1 23 45 67 89'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+33 6 12 34 56 78'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901234'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FR12345678901'}),
            'naf_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1102A'}),
            'country_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'language': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('fr', 'Français'),
                ('en', 'English'),
                ('de', 'Deutsch'),
                ('es', 'Español'),
                ('it', 'Italiano'),
            ]),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('EUR', 'Euro (€)'),
                ('USD', 'US Dollar ($)'),
                ('GBP', 'British Pound (£)'),
                ('CHF', 'Swiss Franc (CHF)'),
            ]),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Salon, Site web, Import...'}),
        }
    
    def clean_siret(self):
        siret = self.cleaned_data.get('siret', '').replace(' ', '')
        if siret and len(siret) != 14:
            raise ValidationError("Le SIRET doit contenir 14 chiffres")
        if siret and not siret.isdigit():
            raise ValidationError("Le SIRET ne doit contenir que des chiffres")
        return siret
    
    def clean_vat_number(self):
        vat = self.cleaned_data.get('vat_number', '').upper().replace(' ', '')
        if vat and len(vat) < 4:
            raise ValidationError("Numéro de TVA trop court")
        return vat


class PartnerQuickCreateForm(forms.ModelForm):
    """Formulaire rapide de création (modale)"""
    
    role = forms.ChoiceField(
        choices=[
            ('client', 'Client'),
            ('supplier', 'Fournisseur'),
            ('prospect', 'Prospect'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Type de tiers"
    )
    
    class Meta:
        model = Partner
        fields = ['name', 'email', 'phone', 'segment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom *', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'segment': forms.Select(attrs={'class': 'form-select'}),
        }


class AddressForm(forms.ModelForm):
    """Formulaire d'adresse"""
    
    class Meta:
        model = Address
        fields = [
            'label', 'address_type', 'is_default',
            'street', 'street2', 'postal_code', 'city', 'state', 'country',
            'contact_name', 'contact_phone',
            'delivery_instructions', 'delivery_hours'
        ]
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Siège Paris'}),
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rue et numéro'}),
            'street2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complément'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Région'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'value': 'FR'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du contact'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '8h-12h, 14h-18h'}),
        }


class ContactPersonForm(forms.ModelForm):
    """Formulaire d'interlocuteur"""
    
    class Meta:
        model = ContactPerson
        fields = [
            'first_name', 'last_name', 'job_title', 'department',
            'email', 'phone', 'mobile',
            'role', 'is_primary', 'is_active', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom *'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom *'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fonction'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ClientProfileForm(forms.ModelForm):
    """Formulaire profil client"""
    
    class Meta:
        model = ClientProfile
        fields = [
            'payment_terms', 'payment_terms_custom',
            'price_category', 'default_discount_pct',
            'credit_limit', 'accounting_code',
            'preferred_shipping_method', 'preferred_carrier',
            'cgv_accepted'
        ]
        widgets = {
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms_custom': forms.TextInput(attrs={'class': 'form-control'}),
            'price_category': forms.Select(attrs={'class': 'form-select'}),
            'default_discount_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'accounting_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '411000'}),
            'preferred_shipping_method': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_carrier': forms.TextInput(attrs={'class': 'form-control'}),
            'cgv_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierProfileForm(forms.ModelForm):
    """Formulaire profil fournisseur"""
    
    class Meta:
        model = SupplierProfile
        fields = [
            'payment_terms', 'payment_terms_custom',
            'incoterm', 'lead_time_days', 'min_order_amount',
            'accounting_code', 'quality_rating', 'is_approved'
        ]
        widgets = {
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms_custom': forms.TextInput(attrs={'class': 'form-control'}),
            'incoterm': forms.Select(attrs={'class': 'form-select'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'accounting_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '401000'}),
            'quality_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PartnerTagForm(forms.ModelForm):
    """Formulaire de tag"""
    
    class Meta:
        model = PartnerTag
        fields = ['name', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PartnerFilterForm(forms.Form):
    """Formulaire de filtrage des partenaires"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...',
            'autocomplete': 'off'
        })
    )
    
    roles = forms.MultipleChoiceField(
        required=False,
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    segment = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les segments')] + list(Partner.SEGMENT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous'), ('true', 'Actifs'), ('false', 'Inactifs')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FR'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['roles'].choices = [
            (r.code, r.label) for r in PartnerRole.objects.all()
        ]
