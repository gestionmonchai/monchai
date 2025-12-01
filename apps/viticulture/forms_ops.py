from __future__ import annotations
from django import forms
from .models_ops import ParcelleOperation


class ParcelleOperationForm(forms.ModelForm):
    class Meta:
        model = ParcelleOperation
        fields = [
            'operation_type',
            'date',
            'label',
            'produit',
            'dose',
            'duree_h',
            'cout_eur',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Basic styling hooks
        self.fields['parcelle'].widget.attrs.setdefault('class', 'form-select')
        self.fields['operation_type'].widget.attrs.setdefault('class', 'form-select')
        for name in ['label', 'produit', 'dose', 'duree_h', 'cout_eur']:
            self.fields[name].widget.attrs.setdefault('class', 'form-control')
        self.fields['date'].widget.attrs.setdefault('class', 'form-control')
        self.fields['notes'].widget.attrs.setdefault('class', 'form-control')
