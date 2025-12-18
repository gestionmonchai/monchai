"""
Formulaires pour les grilles tarifaires
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import PriceList, PriceItem


class PriceListForm(forms.ModelForm):
    """Formulaire de création/édition d'une grille tarifaire"""
    
    class Meta:
        model = PriceList
        fields = ['name', 'currency', 'valid_from', 'valid_to', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tarif Public 2025',
                'autofocus': True,
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'valid_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'valid_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Nom de la grille',
            'currency': 'Devise',
            'valid_from': 'Valide à partir du',
            'valid_to': 'Valide jusqu\'au (optionnel)',
            'is_active': 'Grille active',
        }
        help_texts = {
            'name': 'Nom descriptif de la grille tarifaire',
            'currency': 'Devise utilisée pour les prix',
            'valid_from': 'Date de début de validité',
            'valid_to': 'Laisser vide si la grille n\'a pas de date de fin',
            'is_active': 'Décocher pour désactiver temporairement la grille',
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Choix de devises courantes
        self.fields['currency'].widget.choices = [
            ('EUR', 'EUR - Euro'),
            ('USD', 'USD - Dollar américain'),
            ('GBP', 'GBP - Livre sterling'),
            ('CHF', 'CHF - Franc suisse'),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        # Validation dates
        if valid_from and valid_to and valid_to <= valid_from:
            raise ValidationError({
                'valid_to': 'La date de fin doit être postérieure à la date de début.'
            })
        
        return cleaned_data


class PriceItemForm(forms.ModelForm):
    """Formulaire pour un élément de prix individuel"""
    
    class Meta:
        model = PriceItem
        fields = ['article', 'unit_price', 'min_qty', 'discount_pct']
        widgets = {
            'article': forms.Select(attrs={
                'class': 'form-select',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
            'min_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Optionnel',
            }),
            'discount_pct': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0.00',
            }),
        }
        labels = {
            'article': 'Article',
            'unit_price': 'Prix unitaire (€)',
            'min_qty': 'Quantité minimum',
            'discount_pct': 'Remise (%)',
        }
        help_texts = {
            'article': 'Sélectionnez l\'article',
            'unit_price': 'Prix unitaire en euros',
            'min_qty': 'Quantité minimum pour appliquer ce prix (laisser vide pour prix par défaut)',
            'discount_pct': 'Remise en pourcentage (0 = pas de remise)',
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.price_list = kwargs.pop('price_list', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les Articles par organisation
        if self.organization:
            from apps.catalogue.models import Article
            self.fields['article'].queryset = Article.objects.filter(
                organization=self.organization,
                is_active=True,
                is_sellable=True
            ).order_by('name')


class PriceListImportForm(forms.Form):
    """
    Formulaire d'import CSV/Excel pour grille tarifaire
    """
    file = forms.FileField(
        label='Fichier CSV',
        help_text='Format CSV avec colonnes : code_sku, prix_unitaire, qte_min (optionnel), remise_pct (optionnel)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt',
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        # Vérifier l'extension
        if not file.name.endswith(('.csv', '.txt')):
            raise ValidationError('Le fichier doit être au format CSV (.csv ou .txt)')
        
        # Vérifier la taille (max 5 MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('Le fichier ne doit pas dépasser 5 MB')
        
        return file
