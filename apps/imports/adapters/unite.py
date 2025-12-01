"""
Adapter import pour les unités de mesure
Configuration spécifique unités selon roadmap CSV_2
"""

from typing import Dict, List, Any
from apps.referentiels.models import Unite
from .base import BaseImportAdapter


class UniteImportAdapter(BaseImportAdapter):
    """Adapter import pour unités de mesure"""
    
    @property
    def entity_name(self) -> str:
        return 'unite'
    
    @property
    def display_name(self) -> str:
        return 'Unités de mesure'
    
    @property
    def model_class(self):
        return Unite
    
    def get_schema(self) -> Dict[str, Any]:
        """Configuration complète unités"""
        return {
            'required_fields': ['nom', 'symbole'],
            'optional_fields': ['notes'],
            'unique_key': 'symbole',  # Clé pour upsert (symbole unique)
            'synonyms': {
                'nom': ['nom', 'name', 'libelle', 'label', 'unite', 'unit', 'mesure'],
                'symbole': ['symbole', 'code', 'abbr', 'abbreviation', 'sigle', 'symbol'],
                'notes': ['notes', 'note', 'commentaire', 'commentaires', 'description', 'desc']
            },
            'transforms_defaults': {
                'nom': ['trim', 'collapse_spaces', 'title_case'],
                'symbole': ['trim', 'upper'],
                'notes': ['trim', 'collapse_spaces']
            },
            'fk_lookups': {},  # Pas de FK pour unités
            'validators': {
                'nom': self._validate_nom_length,
                'symbole': self._validate_symbole_format
            },
            'choices': {},
            'examples': {
                'nom': 'Litre',
                'symbole': 'L',
                'notes': 'Unité de volume standard'
            }
        }
    
    def _validate_nom_length(self, value: str) -> tuple[bool, str]:
        """Validation longueur nom"""
        if not value or len(value.strip()) < 2:
            return False, "Le nom doit contenir au moins 2 caractères"
        if len(value) > 50:
            return False, "Le nom ne peut pas dépasser 50 caractères"
        return True, ""
    
    def _validate_symbole_format(self, value: str) -> tuple[bool, str]:
        """Validation format symbole"""
        if not value or len(value.strip()) < 1:
            return False, "Le symbole est requis"
        
        symbole = value.strip().upper()
        if len(symbole) > 10:
            return False, "Le symbole ne peut pas dépasser 10 caractères"
        
        # Vérifier caractères autorisés (lettres, chiffres, quelques symboles)
        import re
        if not re.match(r'^[A-Z0-9°%/\-_]+$', symbole):
            return False, "Symbole invalide (lettres, chiffres, °, %, /, -, _ autorisés)"
        
        return True, ""
    
    def transform_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformations spécifiques unités"""
        transformed = row_data.copy()
        
        # Normalisation du symbole
        if 'symbole' in transformed and transformed['symbole']:
            transformed['symbole'] = str(transformed['symbole']).strip().upper()
        
        return transformed
    
    def get_lookup_key(self, row_data: Dict[str, Any]) -> str:
        """Clé de lookup pour upsert (par symbole)"""
        return row_data.get('symbole', '').strip().upper()
    
    def create_instance(self, organization, validated_data: Dict[str, Any]):
        """Création instance unité"""
        return Unite.objects.create(
            organization=organization,
            **validated_data
        )
    
    def update_instance(self, instance, validated_data: Dict[str, Any]):
        """Mise à jour instance unité"""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
