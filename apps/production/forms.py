from __future__ import annotations
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import VendangeReception, VendangeLigne, Assemblage, AssemblageLigne, LotTechnique
from apps.viticulture.models_extended import LotContainer, LotIntervention, LotMeasurement
from apps.viticulture.models import Lot as VitiLot


class VendangeForm(forms.ModelForm):
    """Formulaire principal de vendange (infos générales de la parcelle)."""
    auto_create_lot = forms.BooleanField(label="Créer automatiquement un lot technique", required=False, initial=False)
    type_recolte = forms.CharField(label='Type récolte', required=False, widget=forms.TextInput(attrs={
        'list': 'type_recolte_options',
        'placeholder': 'Choisir ou saisir…',
    }))
    
    class Meta:
        model = VendangeReception
        fields = [
            'parcelle', 'cuvee', 'date', 'type_vendange', 'type_recolte', 'statut',
            'degre_potentiel', 'temperature_c',
            'tri', 'tri_notes', 'bennes_palox',
            'etat_sanitaire', 'etat_sanitaire_notes',
            'prix_raisin_eur_kg', 'volume_mesure_l', 'rendement_pct',
            'notes', 'auto_create_lot'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'tri_notes': forms.Textarea(attrs={'rows': 2}),
            'etat_sanitaire_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            from apps.referentiels.models import Parcelle, Cuvee
            self.fields['parcelle'].queryset = Parcelle.objects.filter(organization=self.organization).order_by('nom')
            self.fields['cuvee'].queryset = Cuvee.objects.filter(organization=self.organization).order_by('nom')
            self.fields['cuvee'].required = False
        # Styling
        self.fields['type_recolte'].widget.attrs.setdefault('autocomplete', 'off')
        self.fields['cuvee'].widget.attrs.update({'class': 'form-select'})
        self.fields['statut'].widget.attrs.update({'class': 'form-select'})
        self.fields['type_vendange'].widget.attrs.update({'class': 'form-select'})

    def clean_type_recolte(self):
        val = (self.cleaned_data.get('type_recolte') or '').strip()
        if not val:
            return self.instance.type_recolte or 'blanc'
        v = val.lower().strip()
        mapping = {
            'blanc': 'blanc', 'rouge': 'rouge', 'rose': 'rose',
            'rosé': 'rose', 'base effervescente': 'base_effervescente',
        }
        return mapping.get(v, val)


class VendangeLigneForm(forms.ModelForm):
    """Formulaire pour une ligne de vendange (détail par cépage)."""
    class Meta:
        model = VendangeLigne
        fields = ['cepage', 'quantite_kg', 'rang_debut', 'rang_fin', 'rangs_texte', 'degre_potentiel', 'etat_sanitaire', 'notes']
        widgets = {
            'quantite_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kg', 'min': '0', 'step': '0.1'}),
            'rang_debut': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Début', 'min': '1'}),
            'rang_fin': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fin', 'min': '1'}),
            'rangs_texte': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1-5, 10-12'}),
            'degre_potentiel': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°', 'step': '0.1'}),
            'etat_sanitaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'État'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            from apps.referentiels.models import Cepage
            self.fields['cepage'].queryset = Cepage.objects.filter(organization=self.organization).order_by('nom')
        self.fields['cepage'].widget.attrs.update({'class': 'form-select'})


class BaseVendangeLigneFormSet(BaseInlineFormSet):
    """Formset personnalisé pour valider qu'au moins une ligne est renseignée."""
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        # Vérifier qu'au moins une ligne a une quantité
        has_data = False
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('quantite_kg'):
                    has_data = True
                    break
        if not has_data:
            raise forms.ValidationError("Veuillez saisir au moins une ligne avec une quantité.")


# Formset pour les lignes de vendange
VendangeLigneFormSet = inlineformset_factory(
    VendangeReception,
    VendangeLigne,
    form=VendangeLigneForm,
    formset=BaseVendangeLigneFormSet,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class LotTechniqueForm(forms.ModelForm):
    class Meta:
        model = LotTechnique
        fields = ['code', 'campagne', 'contenant', 'volume_l', 'statut']
        widgets = {}


class LotContainerForm(forms.ModelForm):
    class Meta:
        model = LotContainer
        fields = ['lot', 'type', 'capacite_l', 'volume_occupe_l', 'identifiant']
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        # Filter lots by organization if provided
        lots_qs = VitiLot.objects.all()
        if self.organization:
            lots_qs = lots_qs.filter(organization=self.organization)
        self.fields['lot'].queryset = lots_qs.order_by('-created_at')
        # basic styling
        self.fields['lot'].widget.attrs.setdefault('class', 'form-select')
        self.fields['type'].widget.attrs.setdefault('class', 'form-select')
        self.fields['capacite_l'].widget.attrs.setdefault('class', 'form-control')
        self.fields['volume_occupe_l'].widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned = super().clean()
        cap = cleaned.get('capacite_l')
        occ = cleaned.get('volume_occupe_l')
        if cap is not None and occ is not None and occ > cap:
            self.add_error('volume_occupe_l', "Le volume occupé ne peut pas dépasser la capacité")
        return cleaned


from django.utils import timezone

class LotInterventionForm(forms.Form):
    type = forms.ChoiceField(choices=[], label="Type d'intervention")
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date", required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Notes / Observations")
    
    # Intrants (simplifié)
    produit_intrant = forms.CharField(required=False, label="Produit / Intrant", widget=forms.TextInput(attrs={'placeholder': 'Ex: SO2, Colle...'}))
    quantite = forms.DecimalField(required=False, max_digits=10, decimal_places=3, label="Quantité")
    unite = forms.CharField(required=False, label="Unité", widget=forms.TextInput(attrs={'placeholder': 'g/hL, L, kg...'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].choices = LotIntervention.INTERVENTION_CHOICES

    def clean_date(self):
        d = self.cleaned_data.get('date')
        if not d:
            return timezone.now().date()
        return d


class LotMeasurementForm(forms.ModelForm):
    class Meta:
        model = LotMeasurement
        fields = ['type', 'value', 'date', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].required = False

    def clean_date(self):
        d = self.cleaned_data.get('date')
        if not d:
            return timezone.now()
        return d


class AssemblageForm(forms.ModelForm):
    class Meta:
        model = Assemblage
        fields = ['code', 'date', 'campagne', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class AssemblageLigneForm(forms.ModelForm):
    class Meta:
        model = AssemblageLigne
        fields = ['lot_source', 'volume_l']

    def clean(self):
        cleaned = super().clean()
        lot: LotTechnique | None = cleaned.get('lot_source')
        vol = cleaned.get('volume_l')
        if lot and vol and vol > lot.volume_l:
            raise forms.ValidationError("Volume demandé supérieur au stock du lot source")
        return cleaned


AssemblageLigneFormSet = inlineformset_factory(
    parent_model=Assemblage,
    model=AssemblageLigne,
    form=AssemblageLigneForm,
    extra=2,
    can_delete=True,
)
