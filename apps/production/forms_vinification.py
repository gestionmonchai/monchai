from django import forms
from django.utils import timezone
from apps.production.models import LotTechnique
from apps.viticulture.models_extended import LotIntervention, LotMeasurement

class VinificationOperationForm(forms.Form):
    # Champs communs
    lot_id = forms.ModelChoiceField(
        queryset=LotTechnique.objects.none(),
        label="Lot technique",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    date = forms.DateField(
        initial=timezone.now,
        label="Date",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    TYPE_CHOICES = [
        ('', '--- Sélectionner ---'),
        ('debourbage', 'Débourbage'),
        ('inoculation_levures', 'Inoculation levures'),
        ('inoculation_bacteries', 'Inoculation bactéries malo'),
        ('so2', 'Ajout SO₂'),
        ('chaptalisation', 'Chaptalisation / Enrichissement'),
        ('correction_acidite', 'Correction acidité'),
        ('remontage', 'Remontage / Pigeage / Délestage'),
        ('controle_densite_temp', 'Contrôle Densité / T°'),
        ('debut_fa', 'Début FA'),
        ('fin_fa', 'Fin FA'),
        ('debut_fml', 'Début FML'),
        ('fin_fml', 'Fin FML'),
    ]
    
    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        label="Type d'opération",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    volume_concerne = forms.DecimalField(
        label="Volume concerné (L)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    comment = forms.CharField(
        label="Commentaire / Notes",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    # Champs conditionnels
    # Débourbage
    duree_heures = forms.DecimalField(label="Durée (h)", required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Température (Débourbage, Contrôle T°)
    temperature = forms.DecimalField(label="Température (°C)", required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    
    # Inoculation / Ajout / Correction
    produit = forms.CharField(label="Produit", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    dose = forms.CharField(label="Dose / Quantité", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Chaptalisation
    quantite_sucre = forms.DecimalField(label="Quantité sucre (kg)", required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Correction acidité
    CORRECTION_TYPE_CHOICES = [('acidification', 'Acidification'), ('desacidification', 'Désacidification')]
    correction_type = forms.ChoiceField(label="Type correction", choices=CORRECTION_TYPE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    
    # Remontage/Pigeage
    ACTION_MECANIQUE_CHOICES = [('remontage', 'Remontage'), ('pigeage', 'Pigeage'), ('delestage', 'Délestage')]
    action_mecanique = forms.ChoiceField(label="Action", choices=ACTION_MECANIQUE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    nb_cycles = forms.IntegerField(label="Nb cycles / Durée", required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Contrôle densité
    densite = forms.DecimalField(label="Densité", required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}))

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            # Filtrer les lots techniques de l'organisation (ou source)
            # On ne prend que les lots pertinents pour la vinif (statuts)
            statuts_vinif = [
                'MOUT_ENCUVE', 'MOUT_PRESSE', 'MOUT_DEBOURBE', 
                'VIN_EN_FA', 'VIN_POST_FA', 'VIN_EN_FML', 'VIN_POST_FML', 
                'VIN_ELEVAGE', 'en_cours'
            ]
            # On peut inclure aussi les lots de l'organisation
            self.fields['lot_id'].queryset = LotTechnique.objects.filter(
                cuvee__organization=organization,
                statut__in=statuts_vinif
            ).order_by('-created_at')

    def clean(self):
        cleaned_data = super().clean()
        type_op = cleaned_data.get('type')
        
        # Validation conditionnelle si nécessaire
        if type_op == 'controle_densite_temp':
            if not cleaned_data.get('densite') and not cleaned_data.get('temperature'):
                raise forms.ValidationError("Saisissez au moins une densité ou une température.")
        
        return cleaned_data
