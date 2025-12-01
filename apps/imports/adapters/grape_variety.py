"""
Adapter import pour les cépages
Configuration spécifique cépages selon roadmap CSV_2
"""

from typing import Dict, List, Any
from apps.referentiels.models import Cepage
from .base import BaseImportAdapter


class GrapeVarietyImportAdapter(BaseImportAdapter):
    """Adapter import pour cépages"""
    
    @property
    def entity_name(self) -> str:
        return 'grape_variety'
    
    @property
    def display_name(self) -> str:
        return 'Cépages'
    
    @property
    def model_class(self):
        return Cepage
    
    def get_schema(self) -> Dict[str, Any]:
        """Configuration complète cépages"""
        return {
            'required_fields': ['nom'],
            'optional_fields': ['code', 'couleur', 'notes'],
            'unique_key': 'nom',  # Clé pour upsert
            'synonyms': {
                'nom': ['nom', 'name', 'libelle', 'label', 'cépage', 'grape', 'variety'],
                'code': ['code', 'abbr', 'abbreviation', 'sigle'],
                'couleur': ['couleur', 'color', 'colour', 'type'],
                'notes': ['notes', 'note', 'commentaire', 'commentaires', 'description', 'desc']
            },
            'transforms_defaults': {
                'nom': ['trim', 'collapse_spaces', 'title_case'],
                'code': ['trim', 'upper'],
                'couleur': ['trim', 'lower'],
                'notes': ['trim', 'collapse_spaces']
            },
            'fk_lookups': {},  # Pas de FK pour cépages
            'validators': {
                'couleur': self._validate_couleur,
                'nom': self._validate_nom_length,
                'code': self._validate_code_format
            },
            'choices': {
                'couleur': ['blanc', 'rouge', 'rose']
            }
        }
    
    def _validate_couleur(self, value: str) -> bool:
        """Valide couleur cépage"""
        if not value:
            return True  # Optionnel
        
        valid_colors = ['blanc', 'rouge', 'rose', 'white', 'red', 'rosé', 'pink']
        return value.lower().strip() in valid_colors
    
    def _validate_nom_length(self, value: str) -> bool:
        """Valide longueur nom"""
        if not value:
            return False  # Obligatoire
        
        return 2 <= len(value.strip()) <= 100
    
    def _validate_code_format(self, value: str) -> bool:
        """Valide format code"""
        if not value:
            return True  # Optionnel
        
        # Code: 2-10 caractères alphanumériques
        import re
        return bool(re.match(r'^[A-Z0-9]{2,10}$', value.strip().upper()))
    
    def get_field_help_text(self, field: str) -> str:
        """Textes d'aide spécifiques cépages"""
        help_texts = {
            'nom': "Nom du cépage (ex: Cabernet Sauvignon, Chardonnay)",
            'code': "Code court du cépage (ex: CS, CHARD) - optionnel",
            'couleur': "Couleur: blanc, rouge ou rose",
            'notes': "Notes et commentaires sur le cépage"
        }
        return help_texts.get(field, super().get_field_help_text(field))
    
    def get_example_values(self, field: str) -> List[str]:
        """Exemples valeurs cépages"""
        examples = {
            'nom': ['Cabernet Sauvignon', 'Chardonnay', 'Pinot Noir', 'Sauvignon Blanc'],
            'code': ['CS', 'CHARD', 'PN', 'SB'],
            'couleur': ['rouge', 'blanc', 'rose'],
            'notes': ['Cépage noble de Bordeaux', 'Arômes fruités', 'Tanins présents']
        }
        return examples.get(field, [])
    
    def normalize_couleur(self, value: str) -> str:
        """Normalise couleur vers valeurs standard"""
        if not value:
            return 'rouge'  # Défaut
        
        value_lower = value.lower().strip()
        
        # Mapping vers valeurs standard
        color_mapping = {
            'white': 'blanc',
            'red': 'rouge', 
            'pink': 'rose',
            'rosé': 'rose',
            'rose': 'rose'
        }
        
        return color_mapping.get(value_lower, value_lower)
    
    def get_transform_functions(self) -> Dict[str, callable]:
        """Fonctions transformation spécifiques"""
        base_transforms = {
            'trim': lambda x: x.strip() if isinstance(x, str) else x,
            'upper': lambda x: x.upper() if isinstance(x, str) else x,
            'lower': lambda x: x.lower() if isinstance(x, str) else x,
            'title_case': lambda x: x.title() if isinstance(x, str) else x,
            'collapse_spaces': lambda x: ' '.join(x.split()) if isinstance(x, str) else x,
        }
        
        # Transformations spécifiques cépages
        grape_transforms = {
            'normalize_couleur': self.normalize_couleur,
        }
        
        return {**base_transforms, **grape_transforms}
