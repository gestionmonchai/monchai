"""
Formulaires pour les analyses œnologiques.
"""

from django import forms
from .models_analyses import Analyse
from .models import LotTechnique


class AnalyseForm(forms.ModelForm):
    """
    Formulaire complet pour créer ou modifier une analyse œnologique.
    """

    class Meta:
        model = Analyse
        fields = [
            # Contexte
            'lot', 'date', 'type_analyse', 'origine', 'labo_externe_nom', 'statut',
            # Structure & Acidité
            'densite', 'tav', 'sucres_residuels', 'ph',
            'acidite_totale', 'acidite_volatile', 'acide_malique', 'acide_lactique',
            # SO₂ & Oxydation
            'so2_libre', 'so2_total', 'potentiel_redox', 'so2_commentaire',
            # Autres paramètres
            'azote_assimilable', 'turbidite',
            'couleur_do420', 'couleur_do520', 'couleur_do620', 'ipt',
            # Appréciation
            'note_globale', 'notes_degustation', 'commentaires_internes',
            # Alertes
            'alerte_declenchee', 'alerte_type', 'alerte_description',
            'alerte_recommandation', 'prochaine_analyse_date',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'lot': forms.Select(attrs={'class': 'form-select'}),
            'type_analyse': forms.Select(attrs={'class': 'form-select'}),
            'origine': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'labo_externe_nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du laboratoire'
            }),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            # Structure & Acidité
            'densite': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.0001', 'placeholder': 'ex: 0.9920'
            }),
            'tav': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': '% vol'
            }),
            'sucres_residuels': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'g/L'
            }),
            'ph': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': 'ex: 3.45'
            }),
            'acidite_totale': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': 'g/L H₂SO₄'
            }),
            'acidite_volatile': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': 'g/L H₂SO₄'
            }),
            'acide_malique': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': 'g/L'
            }),
            'acide_lactique': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': 'g/L'
            }),
            # SO₂
            'so2_libre': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'mg/L'
            }),
            'so2_total': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'mg/L'
            }),
            'potentiel_redox': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'mV'
            }),
            'so2_commentaire': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Commentaires sur le SO₂...'
            }),
            # Autres
            'azote_assimilable': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '1', 'placeholder': 'mg/L'
            }),
            'turbidite': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'NTU'
            }),
            'couleur_do420': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.001', 'placeholder': 'DO'
            }),
            'couleur_do520': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.001', 'placeholder': 'DO'
            }),
            'couleur_do620': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.001', 'placeholder': 'DO'
            }),
            'ipt': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'placeholder': 'IPT'
            }),
            # Appréciation
            'note_globale': forms.Select(
                choices=[('', '—')] + [(i, f"{i}/5") for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'notes_degustation': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Nez, bouche, équilibre...'
            }),
            'commentaires_internes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Observations techniques...'
            }),
            # Alertes
            'alerte_declenchee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alerte_type': forms.Select(attrs={'class': 'form-select'}),
            'alerte_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Détails de l\'alerte...'
            }),
            'alerte_recommandation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: Corriger SO₂ dans 48h'
            }),
            'prochaine_analyse_date': forms.DateInput(attrs={
                'type': 'date', 'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.lot_prefill = kwargs.pop('lot_prefill', None)
        super().__init__(*args, **kwargs)

        # Filtrer les lots par organisation
        if self.organization:
            self.fields['lot'].queryset = LotTechnique.objects.filter(
                cuvee__organization=self.organization
            ).exclude(
                statut='epuise'
            ).select_related('cuvee').order_by('-created_at')
        else:
            self.fields['lot'].queryset = LotTechnique.objects.none()

        # Format d'affichage du lot
        self.fields['lot'].label_from_instance = lambda obj: f"{obj.code} — {obj.cuvee.nom if obj.cuvee else 'Sans cuvée'} ({obj.volume_l} L)"

        # Pré-remplir le lot si fourni
        if self.lot_prefill:
            self.fields['lot'].initial = self.lot_prefill
            # Rendre le champ disabled en lecture visuelle mais garder la valeur
            self.fields['lot'].widget.attrs['class'] += ' bg-light'

        # Rendre le champ alerte_type non obligatoire
        self.fields['alerte_type'].required = False

        # Ajouter le choix vide pour alerte_type
        self.fields['alerte_type'].choices = [('', '— Sélectionner —')] + list(Analyse.ALERTE_TYPE_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        
        # Si origine externe, le nom du labo est recommandé (warning, pas erreur)
        origine = cleaned_data.get('origine')
        labo_nom = cleaned_data.get('labo_externe_nom')
        if origine == 'externe' and not labo_nom:
            # Pas une erreur bloquante, juste un avertissement
            pass

        # Si alerte déclenchée, le type d'alerte devrait être renseigné
        alerte = cleaned_data.get('alerte_declenchee')
        alerte_type = cleaned_data.get('alerte_type')
        if alerte and not alerte_type:
            self.add_error('alerte_type', "Veuillez préciser le type d'alerte.")

        return cleaned_data


class AnalyseFilterForm(forms.Form):
    """
    Formulaire de filtrage pour la liste des analyses.
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Recherche (lot, cuvée, notes...)',
            'autocomplete': 'off'
        })
    )
    campagne = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    type_analyse = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + list(Analyse.TYPE_ANALYSE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Analyse.STATUT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    niveau_alerte = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les alertes')] + list(Analyse.NIVEAU_ALERTE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    alerte_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        campagnes = kwargs.pop('campagnes', [])
        super().__init__(*args, **kwargs)
        
        # Construire les choix de campagnes dynamiquement
        campagne_choices = [('', 'Toutes les campagnes')]
        for c in campagnes:
            if c:
                campagne_choices.append((c, c))
        self.fields['campagne'].choices = campagne_choices
