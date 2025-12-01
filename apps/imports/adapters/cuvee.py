"""
Adapter import pour les cuvées
Configuration spécifique cuvées selon roadmap CSV_2
"""

from typing import Dict, List, Any
from apps.viticulture.models import Cuvee
from apps.viticulture.models import UnitOfMeasure, Appellation, Vintage
from .base import BaseImportAdapter


class CuveeImportAdapter(BaseImportAdapter):
    """Adapter import pour cuvées"""
    
    @property
    def entity_name(self) -> str:
        return 'cuvee'
    
    @property
    def display_name(self) -> str:
        return 'Cuvées'
    
    @property
    def model_class(self):
        return Cuvee
    
    def get_schema(self) -> Dict[str, Any]:
        """Configuration complète cuvées"""
        return {
            'required_fields': ['name', 'default_uom'],
            'optional_fields': ['code', 'appellation', 'vintage'],
            'unique_key': 'name',  # Clé pour upsert
            'synonyms': {
                'name': ['name', 'nom', 'libelle', 'label', 'cuvee', 'cuvée'],
                'code': ['code', 'reference', 'ref', 'sku'],
                'default_uom': ['default_uom', 'unite', 'unit', 'uom', 'mesure'],
                'appellation': ['appellation', 'aoc', 'aop', 'region'],
                'vintage': ['vintage', 'millesime', 'millésime', 'annee', 'année', 'year']
            },
            'transforms_defaults': {
                'name': ['trim', 'collapse_spaces', 'title_case'],
                'code': ['trim', 'upper'],
                'default_uom': ['trim', 'upper'],
                'appellation': ['trim', 'title_case'],
                'vintage': ['trim']
            },
            'fk_lookups': {
                'default_uom': {
                    'model': UnitOfMeasure,
                    'lookup_field': 'code',
                    'display_field': 'name'
                },
                'appellation': {
                    'model': Appellation,
                    'lookup_field': 'name',
                    'display_field': 'name'
                },
                'vintage': {
                    'model': Vintage,
                    'lookup_field': 'year',
                    'display_field': 'year'
                }
            },
            'validators': {
                'name': self._validate_name_length,
                'code': self._validate_code_format,
                'vintage': self._validate_vintage_year
            },
            'choices': {},
            'examples': {
                'name': 'Cuvée Prestige',
                'code': 'PRES2023',
                'default_uom': 'BTL',
                'appellation': 'Côtes du Rhône',
                'vintage': '2023'
            }
        }
    
    def _validate_name_length(self, value: str) -> tuple[bool, str]:
        """Validation longueur nom"""
        if not value or len(value.strip()) < 2:
            return False, "Le nom doit contenir au moins 2 caractères"
        if len(value) > 100:
            return False, "Le nom ne peut pas dépasser 100 caractères"
        return True, ""
    
    def _validate_code_format(self, value: str) -> tuple[bool, str]:
        """Validation format code (optionnel)"""
        if not value:
            return True, ""  # Code optionnel
        
        code = value.strip()
        if len(code) > 20:
            return False, "Le code ne peut pas dépasser 20 caractères"
        
        return True, ""
    
    def _validate_vintage_year(self, value: str) -> tuple[bool, str]:
        """Validation année millésime"""
        if not value:
            return True, ""  # Millésime optionnel
        
        try:
            year = int(value)
            if year < 1900 or year > 2050:
                return False, "Année de millésime invalide (1900-2050)"
            return True, ""
        except (ValueError, TypeError):
            return False, "Format d'année invalide"
    
    def transform_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformations spécifiques cuvées"""
        transformed = super().transform_row(row_data)
        
        # Conversion millésime en entier
        if 'vintage' in transformed and transformed['vintage']:
            try:
                transformed['vintage'] = int(transformed['vintage'])
            except (ValueError, TypeError):
                transformed['vintage'] = None
        
        return transformed
    
    def get_lookup_key(self, row_data: Dict[str, Any]) -> str:
        """Clé de lookup pour upsert"""
        return row_data.get('name', '').strip().lower()
    
    def resolve_foreign_keys(self, organization, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Résolution des clés étrangères"""
        resolved = row_data.copy()
        
        # Résoudre default_uom (requis)
        if 'default_uom' in row_data and row_data['default_uom']:
            try:
                uom = UnitOfMeasure.objects.get(
                    organization=organization,
                    code__iexact=row_data['default_uom']
                )
                resolved['default_uom'] = uom
            except UnitOfMeasure.DoesNotExist:
                resolved['_errors'] = resolved.get('_errors', [])
                resolved['_errors'].append(f"Unité de mesure '{row_data['default_uom']}' non trouvée")
                resolved['default_uom'] = None
        
        # Résoudre appellation (optionnel)
        if 'appellation' in row_data and row_data['appellation']:
            try:
                appellation = Appellation.objects.get(
                    organization=organization,
                    name__iexact=row_data['appellation']
                )
                resolved['appellation'] = appellation
            except Appellation.DoesNotExist:
                resolved['_warnings'] = resolved.get('_warnings', [])
                resolved['_warnings'].append(f"Appellation '{row_data['appellation']}' non trouvée, sera ignorée")
                resolved['appellation'] = None
        
        # Résoudre vintage (optionnel)
        if 'vintage' in row_data and row_data['vintage']:
            try:
                vintage = Vintage.objects.get(
                    organization=organization,
                    year=row_data['vintage']
                )
                resolved['vintage'] = vintage
            except Vintage.DoesNotExist:
                resolved['_warnings'] = resolved.get('_warnings', [])
                resolved['_warnings'].append(f"Millésime '{row_data['vintage']}' non trouvé, sera ignoré")
                resolved['vintage'] = None
        
        return resolved
    
    def create_instance(self, organization, validated_data: Dict[str, Any]):
        """Création instance cuvée"""
        return Cuvee.objects.create(
            organization=organization,
            **validated_data
        )
    
    def update_instance(self, instance, validated_data: Dict[str, Any]):
        """Mise à jour instance cuvée"""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
