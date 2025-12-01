"""
Adapter import pour les parcelles
Configuration spécifique parcelles selon roadmap CSV_2
"""

from typing import Dict, List, Any
from apps.referentiels.models import Parcelle
from .base import BaseImportAdapter


class ParcelleImportAdapter(BaseImportAdapter):
    """Adapter import pour parcelles"""
    
    @property
    def entity_name(self) -> str:
        return 'parcelle'
    
    @property
    def display_name(self) -> str:
        return 'Parcelles'
    
    @property
    def model_class(self):
        return Parcelle
    
    def get_schema(self) -> Dict[str, Any]:
        """Configuration complète parcelles"""
        return {
            'required_fields': ['nom'],
            'optional_fields': ['surface_ha', 'notes'],
            'unique_key': 'nom',  # Clé pour upsert
            'synonyms': {
                'nom': ['nom', 'name', 'libelle', 'label', 'parcelle', 'plot', 'field'],
                'surface_ha': ['surface_ha', 'surface', 'superficie', 'area', 'hectares', 'ha'],
                'notes': ['notes', 'note', 'commentaire', 'commentaires', 'description', 'desc']
            },
            'transforms_defaults': {
                'nom': ['trim', 'collapse_spaces', 'title_case'],
                'surface_ha': ['trim', 'decimal'],
                'notes': ['trim', 'collapse_spaces']
            },
            'fk_lookups': {},  # Pas de FK pour parcelles
            'validators': {
                'nom': self._validate_nom_length,
                'surface_ha': self._validate_surface_positive
            },
            'choices': {},
            'examples': {
                'nom': 'Les Vignes du Haut',
                'surface_ha': '2.5',
                'notes': 'Parcelle exposée sud, sol calcaire'
            }
        }
    
    def _validate_nom_length(self, value: str) -> tuple[bool, str]:
        """Validation longueur nom"""
        if not value or len(value.strip()) < 2:
            return False, "Le nom doit contenir au moins 2 caractères"
        if len(value) > 100:
            return False, "Le nom ne peut pas dépasser 100 caractères"
        return True, ""
    
    def _validate_surface_positive(self, value: str) -> tuple[bool, str]:
        """Validation surface positive"""
        if not value:
            return True, ""  # Optionnel
        
        try:
            surface = float(value.replace(',', '.'))
            if surface <= 0:
                return False, "La surface doit être positive"
            if surface > 1000:  # Limite raisonnable
                return False, "Surface trop importante (max 1000 ha)"
            return True, ""
        except (ValueError, TypeError):
            return False, "Format de surface invalide (ex: 2.5)"
    
    def transform_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformations spécifiques parcelles"""
        transformed = row_data.copy()
        
        # Conversion surface avec gestion virgule/point
        if 'surface_ha' in transformed and transformed['surface_ha']:
            try:
                surface_str = str(transformed['surface_ha']).replace(',', '.')
                transformed['surface_ha'] = float(surface_str)
            except (ValueError, TypeError):
                transformed['surface_ha'] = None
        
        return transformed
    
    def get_lookup_key(self, row_data: Dict[str, Any]) -> str:
        """Clé de lookup pour upsert"""
        return row_data.get('nom', '').strip().lower()
    
    def create_instance(self, organization, validated_data: Dict[str, Any]):
        """Création instance parcelle"""
        return Parcelle.objects.create(
            organization=organization,
            **validated_data
        )
    
    def update_instance(self, instance, validated_data: Dict[str, Any]):
        """Mise à jour instance parcelle"""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
