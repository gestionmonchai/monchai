"""
Adapter import pour les entrepôts
Configuration spécifique entrepôts selon roadmap CSV_2
"""

from typing import Dict, List, Any
from apps.referentiels.models import Entrepot
from .base import BaseImportAdapter


class EntrepotImportAdapter(BaseImportAdapter):
    """Adapter import pour entrepôts"""
    
    @property
    def entity_name(self) -> str:
        return 'entrepot'
    
    @property
    def display_name(self) -> str:
        return 'Entrepôts'
    
    @property
    def model_class(self):
        return Entrepot
    
    def get_schema(self) -> Dict[str, Any]:
        """Configuration complète entrepôts"""
        return {
            'required_fields': ['nom'],
            'optional_fields': ['notes'],
            'unique_key': 'nom',  # Clé pour upsert
            'synonyms': {
                'nom': ['nom', 'name', 'libelle', 'label', 'entrepot', 'entrepôt', 'warehouse', 'depot'],
                'notes': ['notes', 'note', 'commentaire', 'commentaires', 'description', 'desc']
            },
            'transforms_defaults': {
                'nom': ['trim', 'collapse_spaces', 'title_case'],
                'notes': ['trim', 'collapse_spaces']
            },
            'fk_lookups': {},  # Pas de FK pour entrepôts
            'validators': {
                'nom': self._validate_nom_length
            },
            'choices': {},
            'examples': {
                'nom': 'Entrepôt Principal',
                'notes': 'Stockage principal des bouteilles finies'
            }
        }
    
    def _validate_nom_length(self, value: str) -> tuple[bool, str]:
        """Validation longueur nom"""
        if not value or len(value.strip()) < 2:
            return False, "Le nom doit contenir au moins 2 caractères"
        if len(value) > 100:
            return False, "Le nom ne peut pas dépasser 100 caractères"
        return True, ""
    
    def transform_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformations spécifiques entrepôts"""
        transformed = super().transform_row(row_data)
        return transformed
    
    def get_lookup_key(self, row_data: Dict[str, Any]) -> str:
        """Clé de lookup pour upsert"""
        return row_data.get('nom', '').strip().lower()
    
    def create_instance(self, organization, validated_data: Dict[str, Any]):
        """Création instance entrepôt"""
        return Entrepot.objects.create(
            organization=organization,
            **validated_data
        )
    
    def update_instance(self, instance, validated_data: Dict[str, Any]):
        """Mise à jour instance entrepôt"""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
