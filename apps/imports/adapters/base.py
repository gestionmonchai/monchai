"""
Adapter de base pour entités importables
CSV_2: Mapping & Transformations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from django.db import models


class BaseImportAdapter(ABC):
    """
    Adapter de base pour configuration import d'entité
    Chaque entité doit hériter et implémenter les méthodes abstraites
    """
    
    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Nom technique entité (ex: grape_variety)"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nom affiché (ex: Cépages)"""
        pass
    
    @property
    @abstractmethod
    def model_class(self) -> models.Model:
        """Classe modèle Django"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Retourne schéma complet entité
        
        Returns:
            Dict avec:
            - required_fields: List[str]
            - optional_fields: List[str] 
            - unique_key: str
            - synonyms: Dict[str, List[str]]
            - transforms_defaults: Dict[str, List[str]]
            - fk_lookups: Dict[str, Dict]
            - validators: Dict[str, callable]
        """
        pass
    
    def get_required_fields(self) -> List[str]:
        """Champs obligatoires"""
        return self.get_schema()['required_fields']
    
    def get_optional_fields(self) -> List[str]:
        """Champs optionnels"""
        return self.get_schema()['optional_fields']
    
    def get_all_fields(self) -> List[str]:
        """Tous champs (requis + optionnels)"""
        schema = self.get_schema()
        return schema['required_fields'] + schema['optional_fields']
    
    def get_unique_key(self) -> str:
        """Clé unique pour upsert"""
        return self.get_schema()['unique_key']
    
    def get_synonyms(self) -> Dict[str, List[str]]:
        """Dictionnaire synonymes pour auto-mapping"""
        return self.get_schema().get('synonyms', {})
    
    def get_transforms_defaults(self) -> Dict[str, List[str]]:
        """Transformations par défaut par champ"""
        return self.get_schema().get('transforms_defaults', {})
    
    def get_fk_lookups(self) -> Dict[str, Dict]:
        """Configuration lookups FK"""
        return self.get_schema().get('fk_lookups', {})
    
    def get_validators(self) -> Dict[str, callable]:
        """Validateurs personnalisés par champ"""
        return self.get_schema().get('validators', {})
    
    def find_field_by_synonym(self, csv_column: str) -> Optional[str]:
        """
        Trouve champ entité par synonyme
        
        Args:
            csv_column: Nom colonne CSV
            
        Returns:
            Nom champ entité ou None
        """
        csv_lower = csv_column.lower().strip()
        synonyms = self.get_synonyms()
        
        for field, field_synonyms in synonyms.items():
            if csv_lower in [s.lower() for s in field_synonyms]:
                return field
        
        # Recherche exacte sur nom champ
        if csv_lower in [f.lower() for f in self.get_all_fields()]:
            return csv_lower
        
        return None
    
    def calculate_mapping_confidence(self, csv_column: str, entity_field: str) -> float:
        """
        Calcule confiance mapping
        
        Args:
            csv_column: Colonne CSV
            entity_field: Champ entité
            
        Returns:
            Confiance 0.0-1.0
        """
        csv_lower = csv_column.lower().strip()
        field_lower = entity_field.lower()
        
        # Correspondance exacte
        if csv_lower == field_lower:
            return 1.0
        
        # Synonyme exact
        synonyms = self.get_synonyms().get(entity_field, [])
        if csv_lower in [s.lower() for s in synonyms]:
            return 0.9
        
        # Similarité partielle (contient)
        if csv_lower in field_lower or field_lower in csv_lower:
            return 0.7
        
        # Similarité synonymes partielles
        for synonym in synonyms:
            if csv_lower in synonym.lower() or synonym.lower() in csv_lower:
                return 0.6
        
        return 0.0
    
    def validate_field_value(self, field: str, value: Any) -> tuple[bool, str]:
        """
        Valide valeur champ
        
        Args:
            field: Nom champ
            value: Valeur à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        validators = self.get_validators()
        
        if field in validators:
            try:
                is_valid = validators[field](value)
                return is_valid, "" if is_valid else f"Valeur invalide pour {field}: {value}"
            except Exception as e:
                return False, f"Erreur validation {field}: {str(e)}"
        
        return True, ""
    
    def get_field_help_text(self, field: str) -> str:
        """Texte d'aide pour champ"""
        help_texts = {
            'nom': "Nom de l'élément (obligatoire, unique)",
            'code': "Code court (optionnel, unique si fourni)",
            'notes': "Notes et commentaires (optionnel)",
        }
        return help_texts.get(field, f"Champ {field}")
    
    def get_example_values(self, field: str) -> List[str]:
        """Exemples valeurs pour champ"""
        return []  # À surcharger par adapters spécifiques
