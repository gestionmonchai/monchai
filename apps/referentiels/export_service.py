"""
Service d'export générique pour les référentiels
Basé sur export_service_spec.txt
"""

import csv
import io
from typing import Dict, List, Any, Optional
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils import timezone

from .models import Cepage, Parcelle, Unite, Cuvee, Entrepot


class CSVExportService:
    """Service d'export CSV générique avec sécurité anti-injection"""
    
    # Configuration des entités exportables
    EXPORTABLE_ENTITIES = {
        'cepages': {
            'model': Cepage,
            'columns': ['nom', 'code', 'couleur', 'notes', 'created_at'],
            'headers': ['Nom', 'Code', 'Couleur', 'Notes', 'Date création'],
        },
        'parcelles': {
            'model': Parcelle,
            'columns': ['nom', 'surface', 'lieu_dit', 'commune', 'appellation', 'notes'],
            'headers': ['Nom', 'Surface (ha)', 'Lieu-dit', 'Commune', 'Appellation', 'Notes'],
        },
        'unites': {
            'model': Unite,
            'columns': ['nom', 'symbole', 'type_unite', 'facteur_conversion'],
            'headers': ['Nom', 'Symbole', 'Type', 'Facteur conversion'],
        },
        'cuvees': {
            'model': Cuvee,
            'columns': ['nom', 'couleur', 'classification', 'appellation', 'degre_alcool'],
            'headers': ['Nom', 'Couleur', 'Classification', 'Appellation', 'Degré alcool'],
        },
        'entrepots': {
            'model': Entrepot,
            'columns': ['nom', 'type_entrepot', 'adresse', 'capacite'],
            'headers': ['Nom', 'Type', 'Adresse', 'Capacité'],
        }
    }
    
    def __init__(self, organization):
        self.organization = organization
    
    def export_entity(self, entity_type: str, queryset: QuerySet = None, 
                     columns: List[str] = None, encoding: str = 'utf-8',
                     delimiter: str = ';', neutralize_formulas: bool = True) -> HttpResponse:
        """
        Exporte une entité en CSV avec protection anti-injection
        """
        if entity_type not in self.EXPORTABLE_ENTITIES:
            raise ValidationError(f"Type d'entité non supporté: {entity_type}")
        
        config = self.EXPORTABLE_ENTITIES[entity_type]
        model = config['model']
        
        # Utiliser le queryset fourni ou créer un queryset par défaut
        if queryset is None:
            queryset = model.objects.filter(organization=self.organization)
        
        # Colonnes à exporter (par défaut toutes les colonnes configurées)
        export_columns = columns or config['columns']
        export_headers = [config['headers'][config['columns'].index(col)] 
                         for col in export_columns if col in config['columns']]
        
        # Créer la réponse HTTP
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{entity_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Configurer l'encodage
        if encoding == 'utf-8-bom':
            response.write('\ufeff'.encode('utf-8'))
            encoding = 'utf-8'
        
        # Créer le writer CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        
        # Écrire les en-têtes
        writer.writerow(export_headers)
        
        # Écrire les données
        for obj in queryset:
            row = []
            for column in export_columns:
                value = self._get_field_value(obj, column)
                if neutralize_formulas:
                    value = self._neutralize_csv_injection(value)
                row.append(value)
            writer.writerow(row)
        
        # Encoder et écrire dans la réponse
        content = output.getvalue()
        response.write(content.encode(encoding))
        
        return response
    
    def _get_field_value(self, obj: Any, field_name: str) -> str:
        """Récupère la valeur d'un champ d'un objet"""
        try:
            value = getattr(obj, field_name)
            if value is None:
                return ''
            elif hasattr(value, 'strftime'):  # datetime
                return value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, bool):
                return 'Oui' if value else 'Non'
            else:
                return str(value)
        except AttributeError:
            return ''
    
    def _neutralize_csv_injection(self, value: str) -> str:
        """
        Neutralise les formules CSV potentiellement dangereuses
        Préfixe avec ' les cellules commençant par = + - @ \t
        """
        if not isinstance(value, str) or not value:
            return value
        
        dangerous_chars = ['=', '+', '-', '@', '\t']
        if value.strip() and value.strip()[0] in dangerous_chars:
            return "'" + value
        
        return value
    
    def get_exportable_columns(self, entity_type: str) -> Dict[str, List[str]]:
        """Retourne les colonnes exportables pour une entité"""
        if entity_type not in self.EXPORTABLE_ENTITIES:
            return {'columns': [], 'headers': []}
        
        config = self.EXPORTABLE_ENTITIES[entity_type]
        return {
            'columns': config['columns'],
            'headers': config['headers']
        }
