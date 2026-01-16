"""
Formulaires pour le catalogue et la gestion des lots
Roadmap Cut #4 : Catalogue & lots
"""

from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from apps.referentiels.models import Cuvee, Entrepot, Unite
from .models import Lot, MouvementLot


class LotForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un lot
    Roadmap item 22: /lots/new – Création lot (source, volume, degré)
    """
    
    class Meta:
        model = Lot
        fields = [
            'cuvee', 'entrepot', 'numero_lot', 'millesime',
            'volume_initial', 'unite_volume', 'degre_alcool', 'densite',
            'statut', 'date_creation', 'date_fin_prevue', 'notes'
        ]
        widgets = {
            'date_creation': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'numero_lot': forms.TextInput(attrs={'placeholder': 'Ex: LOT-2024-001'}),
            'volume_initial': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'degre_alcool': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '20'}),
            'densite': forms.NumberInput(attrs={'step': '0.0001', 'min': '0.8', 'max': '1.2'}),
        }
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if organization:
            # Filtrer les choix par organisation
            self.fields['cuvee'].queryset = Cuvee.objects.filter(organization=organization)
            self.fields['entrepot'].queryset = Entrepot.objects.filter(organization=organization)
            self.fields['unite_volume'].queryset = Unite.objects.filter(
                organization=organization, 
                type_unite='volume'
            )
        
        # Valeurs par défaut
        if not self.instance.pk:
            self.fields['date_creation'].initial = date.today()
            self.fields['millesime'].initial = date.today().year
            self.fields['statut'].initial = 'production'
            
            # Unité par défaut : Litre
            if organization:
                try:
                    litre = Unite.objects.get(organization=organization, nom='Litre')
                    self.fields['unite_volume'].initial = litre
                except Unite.DoesNotExist:
                    pass
        
        # Aide contextuelle
        self.fields['numero_lot'].help_text = "Identifiant unique du lot (ex: LOT-2024-001)"
        self.fields['millesime'].help_text = "Année de récolte du raisin"
        self.fields['volume_initial'].help_text = "Volume initial du lot à la création"
        self.fields['degre_alcool'].help_text = "Titre alcoométrique en % vol. (optionnel)"
        self.fields['densite'].help_text = "Densité du vin (optionnel)"
        self.fields['date_fin_prevue'].help_text = "Date prévue de fin de production (optionnel)"
        
        # Classes CSS Bootstrap
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_numero_lot(self):
        """Validation du numéro de lot"""
        numero_lot = self.cleaned_data.get('numero_lot')
        if not numero_lot:
            return numero_lot
        
        # Vérifier l'unicité du numéro de lot pour l'organisation et le millésime
        millesime = self.cleaned_data.get('millesime')
        if millesime and hasattr(self, 'organization'):
            existing = Lot.objects.filter(
                organization=self.organization,
                numero_lot=numero_lot,
                millesime=millesime
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f"Un lot avec le numéro '{numero_lot}' existe déjà pour le millésime {millesime}."
                )
        
        return numero_lot
    
    def clean_millesime(self):
        """Validation du millésime"""
        millesime = self.cleaned_data.get('millesime')
        if millesime:
            current_year = date.today().year
            if millesime < 1900 or millesime > current_year + 1:
                raise ValidationError(
                    f"Le millésime doit être entre 1900 et {current_year + 1}."
                )
        return millesime
    
    def clean_date_fin_prevue(self):
        """Validation de la date de fin prévue"""
        date_creation = self.cleaned_data.get('date_creation')
        date_fin_prevue = self.cleaned_data.get('date_fin_prevue')
        
        if date_creation and date_fin_prevue:
            if date_fin_prevue <= date_creation:
                raise ValidationError(
                    "La date de fin prévue doit être postérieure à la date de création."
                )
        
        return date_fin_prevue
    
    def clean(self):
        """Validation croisée"""
        cleaned_data = super().clean()
        
        # Vérifier que la cuvée et l'entrepôt appartiennent à la même organisation
        cuvee = cleaned_data.get('cuvee')
        entrepot = cleaned_data.get('entrepot')
        
        if cuvee and entrepot and hasattr(self, 'organization'):
            if cuvee.organization != self.organization:
                raise ValidationError("La cuvée sélectionnée n'appartient pas à votre organisation.")
            if entrepot.organization != self.organization:
                raise ValidationError("L'entrepôt sélectionné n'appartient pas à votre organisation.")
        
        return cleaned_data


class MouvementLotForm(forms.ModelForm):
    """
    Formulaire pour créer un mouvement de lot
    Roadmap item 23: /lots/:id – Détail lot (historique mouvements)
    """
    
    class Meta:
        model = MouvementLot
        fields = [
            'type_mouvement', 'description', 'volume_mouvement',
            'entrepot_source', 'entrepot_destination', 'date_mouvement', 'notes'
        ]
        widgets = {
            'date_mouvement': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'volume_mouvement': forms.NumberInput(attrs={'step': '0.01'}),
            'description': forms.TextInput(attrs={'placeholder': 'Description du mouvement'}),
        }
    
    def __init__(self, *args, lot=None, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.lot = lot
        self.organization = organization
        
        if organization:
            # Filtrer les entrepôts par organisation
            self.fields['entrepot_source'].queryset = Entrepot.objects.filter(organization=organization)
            self.fields['entrepot_destination'].queryset = Entrepot.objects.filter(organization=organization)
        
        # Valeurs par défaut
        if not self.instance.pk and lot:
            from django.utils import timezone
            self.fields['date_mouvement'].initial = timezone.now()
            self.fields['entrepot_source'].initial = lot.entrepot
        
        # Aide contextuelle
        self.fields['type_mouvement'].help_text = "Type d'opération effectuée sur le lot"
        self.fields['description'].help_text = "Description détaillée du mouvement"
        self.fields['volume_mouvement'].help_text = "Volume concerné par le mouvement (positif = entrée, négatif = sortie)"
        self.fields['entrepot_source'].help_text = "Entrepôt source (pour les transferts)"
        self.fields['entrepot_destination'].help_text = "Entrepôt destination (pour les transferts)"
        
        # Classes CSS Bootstrap
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_volume_mouvement(self):
        """Validation du volume de mouvement"""
        volume_mouvement = self.cleaned_data.get('volume_mouvement')
        
        if volume_mouvement == 0:
            raise ValidationError("Le volume du mouvement ne peut pas être nul.")
        
        # Vérifier que le volume négatif ne dépasse pas le volume actuel
        if volume_mouvement < 0 and self.lot:
            volume_apres = self.lot.volume_actuel + volume_mouvement
            if volume_apres < 0:
                raise ValidationError(
                    f"Volume insuffisant. Volume actuel: {self.lot.volume_actuel} {self.lot.unite_volume.symbole}"
                )
        
        return volume_mouvement
    
    def clean(self):
        """Validation croisée"""
        cleaned_data = super().clean()
        
        type_mouvement = cleaned_data.get('type_mouvement')
        entrepot_source = cleaned_data.get('entrepot_source')
        entrepot_destination = cleaned_data.get('entrepot_destination')
        
        # Pour les transferts, les deux entrepôts sont requis
        if type_mouvement == 'transfert_entrepot':
            if not entrepot_source:
                raise ValidationError("L'entrepôt source est requis pour un transfert.")
            if not entrepot_destination:
                raise ValidationError("L'entrepôt destination est requis pour un transfert.")
            if entrepot_source == entrepot_destination:
                raise ValidationError("L'entrepôt source et destination doivent être différents.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sauvegarde avec mise à jour automatique du lot"""
        mouvement = super().save(commit=False)
        
        if self.lot:
            mouvement.lot = self.lot
            mouvement.volume_avant = self.lot.volume_actuel
            mouvement.volume_apres = self.lot.volume_actuel + mouvement.volume_mouvement
        
        if commit:
            mouvement.save()
            
            # Mettre à jour le volume actuel du lot
            if self.lot:
                self.lot.volume_actuel = mouvement.volume_apres
                
                # Mettre à jour l'entrepôt si c'est un transfert
                if mouvement.type_mouvement == 'transfert_entrepot' and mouvement.entrepot_destination:
                    self.lot.entrepot = mouvement.entrepot_destination
                
                self.lot.save()
        
        return mouvement


# --- FORMS CATALOGUE GÉNÉRIQUE (ARTICLES) ---

from .models import Article, ArticleCategory
from apps.produits.models_catalog import Product

class ArticleForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un Article/Product commercial
    NOTE: Article est maintenant un alias de Product
    """
    class Meta:
        model = Product
        fields = [
            'product_type', 'name', 'brand', 'description', 
            'price_eur_u', 'vat_rate', 'unit', 'stockable', 
            'is_buyable', 'is_sellable', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style Bootstrap générique
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

