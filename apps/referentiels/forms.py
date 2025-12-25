"""
Formulaires pour les référentiels viticoles
Roadmap Cut #3 : Référentiels (starter pack)
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Cepage, Parcelle, ParcelleEncepagement, Unite, Cuvee, Entrepot


class CepageSearchForm(forms.Form):
    """Formulaire de recherche avancée pour les cépages"""
    
    nom = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom du cépage...'
        }),
        label='Nom'
    )
    
    code = forms.CharField(
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code...'
        }),
        label='Code'
    )
    
    couleur = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les couleurs')] + Cepage._meta.get_field('couleur').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Couleur'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans les notes...'
        }),
        label='Notes'
    )
    
    # Recherche globale pour compatibilité
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Recherche globale...'
        }),
        label='Recherche globale'
    )
    
    # Tri
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('nom', 'Nom'),
            ('code', 'Code'),
            ('couleur', 'Couleur'),
            ('created_at', 'Date de création'),
            ('updated_at', 'Dernière modification'),
        ],
        initial='nom',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Trier par'
    )
    
    order = forms.ChoiceField(
        required=False,
        choices=[
            ('asc', 'Croissant'),
            ('desc', 'Décroissant'),
        ],
        initial='asc',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ordre'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter des classes CSS pour le styling
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class CepageForm(forms.ModelForm):
    """Formulaire pour les cépages"""
    
    class Meta:
        model = Cepage
        fields = ['nom', 'code', 'couleur', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'couleur': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Aide contextuelle
        self.fields['nom'].help_text = "Nom du cépage (ex: Cabernet Sauvignon)"
        self.fields['code'].help_text = "Code optionnel (ex: CS)"
        self.fields['notes'].help_text = "Notes libres sur ce cépage"
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom and self.organization:
            # Vérifier unicité dans l'organisation (sauf pour l'instance courante)
            queryset = Cepage.objects.filter(organization=self.organization, nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Un cépage avec ce nom existe déjà.")
        return nom


class ParcelleForm(forms.ModelForm):
    """Formulaire pour les parcelles"""
    geojson = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Parcelle
        fields = ['nom', 'surface', 'lieu_dit', 'commune', 'latitude', 'longitude', 'cepages', 'notes', 'conseils', 'geojson']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'surface': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'lieu_dit': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Ex: 47.218371'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Ex: -1.553621'}),
            'cepages': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conseils': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Aide contextuelle
        self.fields['nom'].help_text = "Nom de la parcelle"
        self.fields['surface'].help_text = "Surface en hectares"
        self.fields['lieu_dit'].help_text = "Lieu-dit (optionnel)"
        self.fields['commune'].help_text = "Commune (optionnel)"
        self.fields['latitude'].help_text = "Latitude GPS (ex: 47.218371)"
        self.fields['longitude'].help_text = "Longitude GPS (ex: -1.553621)"
        self.fields['cepages'].help_text = "Sélectionnez un ou plusieurs cépages"
        # Filtrer les cépages par organisation
        if self.organization and 'cepages' in self.fields:
            self.fields['cepages'].queryset = Cepage.objects.filter(organization=self.organization)
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom and self.organization:
            queryset = Parcelle.objects.filter(organization=self.organization, nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Une parcelle avec ce nom existe déjà.")
        return nom


class UniteForm(forms.ModelForm):
    """Formulaire pour les unités"""
    
    class Meta:
        model = Unite
        fields = ['nom', 'symbole', 'type_unite', 'facteur_conversion']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'symbole': forms.TextInput(attrs={'class': 'form-control'}),
            'type_unite': forms.Select(attrs={'class': 'form-select'}),
            'facteur_conversion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Aide contextuelle
        self.fields['nom'].help_text = "Nom de l'unité (ex: Bouteille)"
        self.fields['symbole'].help_text = "Symbole (ex: btl)"
        self.fields['facteur_conversion'].help_text = "Facteur de conversion (ex: 0.75 pour bouteille = 0.75L)"
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom and self.organization:
            queryset = Unite.objects.filter(organization=self.organization, nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Une unité avec ce nom existe déjà.")
        return nom


class CuveeForm(forms.ModelForm):
    """Formulaire pour les cuvées"""
    
    class Meta:
        model = Cuvee
        fields = ['nom', 'couleur', 'classification', 'appellation', 'degre_alcool', 'cepages', 'description', 'notes_degustation']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'couleur': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
            'appellation': forms.TextInput(attrs={'class': 'form-control'}),
            'degre_alcool': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '20'}),
            'cepages': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes_degustation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les cépages par organisation
        if self.organization:
            self.fields['cepages'].queryset = Cepage.objects.filter(organization=self.organization)
        
        # Aide contextuelle
        self.fields['nom'].help_text = "Nom de la cuvée"
        self.fields['degre_alcool'].help_text = "Degré d'alcool en % (optionnel)"
        self.fields['description'].help_text = "Description de la cuvée"
        self.fields['notes_degustation'].help_text = "Notes de dégustation"
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom and self.organization:
            queryset = Cuvee.objects.filter(organization=self.organization, nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Une cuvée avec ce nom existe déjà.")
        return nom


class EntrepotForm(forms.ModelForm):
    """Formulaire pour les entrepôts"""
    
    class Meta:
        model = Entrepot
        fields = ['nom', 'type_entrepot', 'adresse', 'capacite', 'temperature_min', 'temperature_max', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_entrepot': forms.Select(attrs={'class': 'form-select'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'capacite': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'temperature_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'temperature_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Aide contextuelle
        self.fields['nom'].help_text = "Nom de l'entrepôt"
        self.fields['capacite'].help_text = "Capacité en nombre de bouteilles (optionnel)"
        self.fields['temperature_min'].help_text = "Température minimale en °C (optionnel)"
        self.fields['temperature_max'].help_text = "Température maximale en °C (optionnel)"
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom and self.organization:
            queryset = Entrepot.objects.filter(organization=self.organization, nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Un entrepôt avec ce nom existe déjà.")
        return nom
    
    def clean(self):
        cleaned_data = super().clean()
        temp_min = cleaned_data.get('temperature_min')
        temp_max = cleaned_data.get('temperature_max')
        
        if temp_min is not None and temp_max is not None:
            if temp_min >= temp_max:
                raise ValidationError("La température minimale doit être inférieure à la température maximale.")
        
        return cleaned_data


class ParcelleEncepagementForm(forms.ModelForm):
    """Formulaire pour l'encépagement d'une parcelle (rangs/blocs)"""
    
    class Meta:
        model = ParcelleEncepagement
        fields = ['cepage', 'pourcentage', 'rang_debut', 'rang_fin', 'annee_plantation', 'porte_greffe', 'densite_pieds_ha', 'notes']
        widgets = {
            'cepage': forms.Select(attrs={'class': 'form-select'}),
            'pourcentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'max': '100'}),
            'rang_debut': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ex: 1'}),
            'rang_fin': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ex: 50'}),
            'annee_plantation': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2100', 'placeholder': 'Ex: 2010'}),
            'porte_greffe': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: SO4, 3309C...'}),
            'densite_pieds_ha': forms.NumberInput(attrs={'class': 'form-control', 'min': '1000', 'placeholder': 'Ex: 5000'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.parcelle = kwargs.pop('parcelle', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les cépages par organisation
        if self.organization:
            self.fields['cepage'].queryset = Cepage.objects.filter(organization=self.organization).order_by('nom')
        
        # Aide contextuelle
        self.fields['pourcentage'].help_text = "Pourcentage de la parcelle occupé par ce cépage"
        self.fields['rang_debut'].help_text = "Numéro du premier rang (optionnel)"
        self.fields['rang_fin'].help_text = "Numéro du dernier rang (optionnel)"
        self.fields['annee_plantation'].help_text = "Année de plantation des vignes"
        self.fields['porte_greffe'].help_text = "Type de porte-greffe utilisé"
        self.fields['densite_pieds_ha'].help_text = "Nombre de pieds par hectare"
    
    def clean(self):
        cleaned_data = super().clean()
        rang_debut = cleaned_data.get('rang_debut')
        rang_fin = cleaned_data.get('rang_fin')
        
        if rang_debut and rang_fin and rang_debut > rang_fin:
            raise ValidationError("Le rang de début doit être inférieur ou égal au rang de fin.")
        
        return cleaned_data
