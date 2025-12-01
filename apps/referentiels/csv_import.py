"""
Service d'import CSV pour les référentiels
Roadmap 18 - Import CSV des référentiels
"""

import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Optional, Any
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Cepage, Parcelle, Unite, Cuvee, Entrepot
from apps.viticulture.models import GrapeVariety, Appellation, Vintage, UnitOfMeasure, VineyardPlot, Warehouse


class CSVImportError(Exception):
    """Exception pour les erreurs d'import CSV"""
    pass


class CSVImportService:
    """Service d'import CSV pour les référentiels"""
    
    # Configuration des types supportés
    SUPPORTED_TYPES = {
        'grape': {
            'model': Cepage,
            'fields': ['nom', 'couleur', 'code', 'notes'],
            'required': ['nom'],
            'unique_key': 'nom',
            'choices': {
                'couleur': ['blanc', 'rouge', 'rose']
            }
        },
        'parcelle': {
            'model': Parcelle,
            'fields': ['nom', 'surface_ha', 'notes'],
            'required': ['nom', 'surface_ha'],
            'unique_key': 'nom',
            'validators': {
                'surface_ha': lambda x: float(x) > 0
            }
        },
        'unite': {
            'model': Unite,
            'fields': ['nom', 'code', 'notes'],
            'required': ['nom', 'code'],
            'unique_key': 'code'
        },
        'cuvee': {
            'model': Cuvee,
            'fields': ['nom', 'notes'],
            'required': ['nom'],
            'unique_key': 'nom'
        },
        'entrepot': {
            'model': Entrepot,
            'fields': ['nom', 'notes'],
            'required': ['nom'],
            'unique_key': 'nom'
        }
    }
    
    def __init__(self, organization):
        self.organization = organization
        self.errors = []
        self.warnings = []
    
    def detect_encoding(self, file_content: bytes) -> str:
        """Détecte l'encodage du fichier"""
        # Essayer UTF-8 d'abord
        try:
            file_content.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # Essayer UTF-8 avec BOM
        try:
            if file_content.startswith(b'\xef\xbb\xbf'):
                file_content[3:].decode('utf-8')
                return 'utf-8-sig'
        except UnicodeDecodeError:
            pass
        
        # Essayer latin-1 comme fallback commun
        try:
            file_content.decode('latin-1')
            return 'latin-1'
        except UnicodeDecodeError:
            pass
        
        # Fallback vers latin-1
        return 'latin-1'
    
    def detect_delimiter(self, content: str) -> str:
        """Détecte le délimiteur CSV"""
        # Tester les délimiteurs courants sur les 5 premières lignes
        sample = '\n'.join(content.split('\n')[:5])
        
        for delimiter in [';', ',', '\t']:
            try:
                reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
                rows = list(reader)
                if len(rows) > 1 and len(rows[0]) > 1:
                    # Vérifier que toutes les lignes ont le même nombre de colonnes
                    col_counts = [len(row) for row in rows]
                    if len(set(col_counts)) == 1:  # Toutes les lignes ont le même nombre de colonnes
                        return delimiter
            except:
                continue
        
        return ','  # Défaut
    
    def parse_csv_file(self, file) -> Tuple[List[str], List[List[str]], str]:
        """Parse un fichier CSV et retourne headers, rows, encoding"""
        # Lire le contenu
        file_content = file.read()
        
        # Détecter l'encodage
        encoding = self.detect_encoding(file_content)
        
        try:
            content = file_content.decode(encoding)
        except UnicodeDecodeError as e:
            raise CSVImportError(f"Impossible de décoder le fichier avec l'encodage {encoding}: {e}")
        
        # Détecter le délimiteur
        delimiter = self.detect_delimiter(content)
        
        # Parser le CSV
        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
        except csv.Error as e:
            raise CSVImportError(f"Erreur de parsing CSV: {e}")
        
        if not rows:
            raise CSVImportError("Le fichier CSV est vide")
        
        # Séparer headers et données
        headers = [h.strip() for h in rows[0]]
        data_rows = []
        
        for i, row in enumerate(rows[1:], 2):  # Commencer à la ligne 2
            if any(cell.strip() for cell in row):  # Ignorer les lignes vides
                data_rows.append([cell.strip() for cell in row])
        
        return headers, data_rows, encoding
    
    def validate_mapping(self, import_type: str, mapping: Dict[str, str]) -> List[str]:
        """Valide le mapping des colonnes"""
        errors = []
        
        if import_type not in self.SUPPORTED_TYPES:
            errors.append(f"Type d'import non supporté: {import_type}")
            return errors
        
        config = self.SUPPORTED_TYPES[import_type]
        
        # Vérifier que tous les champs requis sont mappés
        for required_field in config['required']:
            if required_field not in mapping.values():
                errors.append(f"Champ requis manquant: {required_field}")
        
        # Vérifier que les champs mappés existent
        for field in mapping.values():
            if field and field not in config['fields']:
                errors.append(f"Champ inconnu: {field}")
        
        return errors
    
    def preview_import(self, import_type: str, headers: List[str], rows: List[List[str]], 
                      mapping: Dict[str, str], limit: int = 10) -> Dict[str, Any]:
        """Prévisualise l'import avec validation"""
        preview_data = []
        errors = []
        warnings = []
        
        config = self.SUPPORTED_TYPES[import_type]
        
        for i, row in enumerate(rows[:limit], 1):
            row_data = {}
            row_errors = []
            
            # Mapper les colonnes
            for col_index, header in enumerate(headers):
                if header in mapping and mapping[header]:
                    field_name = mapping[header]
                    value = row[col_index] if col_index < len(row) else ''
                    
                    # Validation basique
                    if field_name in config['required'] and not value:
                        row_errors.append(f"{field_name}: requis")
                    
                    # Validation des choix
                    if field_name in config.get('choices', {}) and value:
                        if value not in config['choices'][field_name]:
                            row_errors.append(f"{field_name}: valeur invalide '{value}'")
                    
                    # Validation custom
                    if field_name in config.get('validators', {}) and value:
                        try:
                            if not config['validators'][field_name](value):
                                row_errors.append(f"{field_name}: valeur invalide '{value}'")
                        except (ValueError, TypeError):
                            row_errors.append(f"{field_name}: format invalide '{value}'")
                    
                    row_data[field_name] = value
            
            preview_data.append({
                'line': i,
                'data': row_data,
                'errors': row_errors
            })
            
            if row_errors:
                errors.extend([f"Ligne {i}: {error}" for error in row_errors])
        
        return {
            'preview': preview_data,
            'errors': errors,
            'warnings': warnings,
            'total_rows': len(rows)
        }
    
    def normalize_value(self, field_name: str, value: str, config: Dict) -> Any:
        """Normalise une valeur selon le type de champ"""
        if not value:
            return None
        
        # Conversions de type
        if field_name == 'surface_ha':
            return Decimal(str(value))
        
        return value.strip()
    
    @transaction.atomic
    def execute_import(self, import_type: str, headers: List[str], rows: List[List[str]], 
                      mapping: Dict[str, str]) -> Dict[str, Any]:
        """Exécute l'import avec upsert"""
        config = self.SUPPORTED_TYPES[import_type]
        model = config['model']
        
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        for i, row in enumerate(rows, 1):
            try:
                # Mapper les données
                data = {}
                for col_index, header in enumerate(headers):
                    if header in mapping and mapping[header]:
                        field_name = mapping[header]
                        value = row[col_index] if col_index < len(row) else ''
                        
                        if value:  # Seulement si la valeur n'est pas vide
                            data[field_name] = self.normalize_value(field_name, value, config)
                
                # Ajouter l'organisation
                data['organization'] = self.organization
                
                # Upsert
                unique_key = config['unique_key']
                if unique_key in data:
                    # Construire le filtre d'unicité
                    filter_kwargs = {
                        'organization': self.organization,
                        unique_key: data[unique_key]
                    }
                    
                    # Chercher l'objet existant
                    try:
                        obj = model.objects.get(**filter_kwargs)
                        # Mettre à jour
                        for key, value in data.items():
                            if key != 'organization':  # Ne pas écraser l'organisation
                                setattr(obj, key, value)
                        obj.is_active = True  # Réactiver si nécessaire
                        obj.save()
                        updated_count += 1
                    except model.DoesNotExist:
                        # Créer nouveau
                        obj = model.objects.create(**data)
                        created_count += 1
                else:
                    errors.append(f"Ligne {i}: clé unique manquante ({unique_key})")
                    error_count += 1
                    
            except Exception as e:
                errors.append(f"Ligne {i}: {str(e)}")
                error_count += 1
        
        return {
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'error_details': errors,
            'total_processed': len(rows)
        }
    
    def generate_error_report(self, errors: List[str]) -> str:
        """Génère un rapport d'erreurs en CSV"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # En-tête
        writer.writerow(['Ligne', 'Erreur'])
        
        # Données
        for error in errors:
            if ':' in error:
                line_part, error_part = error.split(':', 1)
                writer.writerow([line_part.strip(), error_part.strip()])
            else:
                writer.writerow(['', error])
        
        return output.getvalue()
