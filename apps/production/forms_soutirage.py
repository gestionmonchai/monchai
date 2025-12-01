from django import forms
from django.utils import timezone
from apps.production.models import LotTechnique, Operation

class SoutirageForm(forms.Form):
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
    
    contenant_depart = forms.CharField(
        label="Contenant de départ",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    contenant_arrivee = forms.CharField(
        label="Contenant d'arrivée",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    volume_soutire = forms.DecimalField(
        label="Volume soutiré (L)",
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    perte_estimee = forms.DecimalField(
        label="Perte estimée (L)",
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    MOTIF_CHOICES = [
        ('fin_fa', 'Fin de Fermentation Alcoolique'),
        ('fin_fml', 'Fin de Malolactique'),
        ('separation_lies', 'Séparation des lies'),
        ('clarification', 'Clarification'),
        ('elevage', 'Soutirage d\'élevage'),
        ('prepa_mise', 'Préparation mise'),
        ('autre', 'Autre'),
    ]
    
    motif = forms.ChoiceField(
        choices=MOTIF_CHOICES,
        label="Motif",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    comment = forms.CharField(
        label="Commentaire / Notes",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['lot_id'].queryset = LotTechnique.objects.filter(
                cuvee__organization=organization
            ).exclude(statut='epuise').order_by('-created_at')
