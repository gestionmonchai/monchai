from __future__ import annotations
from django import forms
from django.forms import formset_factory
from apps.production.models import LotTechnique
from apps.viticulture.models import Cuvee


class MiseSourceForm(forms.Form):
    lot_tech_source = forms.ModelChoiceField(queryset=LotTechnique.objects.all(), label="Lot technique")
    volume_l = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, label="Volume (L)")


MiseStep1FormSet = formset_factory(MiseSourceForm, extra=2, can_delete=True)


class MiseFormatForm(forms.Form):
    format_ml = forms.IntegerField(min_value=100, initial=750, label="Format (mL)")
    quantite_unites = forms.IntegerField(min_value=1, initial=1, label="Quantité (u)")
    pertes_pct = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, initial=0, label="Pertes (%)")


MiseStep2FormSet = formset_factory(MiseFormatForm, extra=1, can_delete=True)


class MiseStep2MetaForm(forms.Form):
    cuvee = forms.ModelChoiceField(queryset=Cuvee.objects.all(), required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class MiseStep3Form(forms.Form):
    confirmer = forms.BooleanField(label="Je confirme la création de la mise et des lots commerciaux")
