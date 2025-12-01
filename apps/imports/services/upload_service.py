"""
Service d'upload et prévisualisation
CSV_1: Ingestion sécurisée & Prévisualisation
"""

import os
import csv
import hashlib
import tempfile
import mimetypes
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal
import chardet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from ..models import ImportJob


class UploadService:
    """
    Service d'upload sécurisé et prévisualisation
    Roadmap CSV_1: Ingestion sécurisée & Prévisualisation
    """
    
    # Configuration sécurité
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo
    ALLOWED_EXTENSIONS = ['.csv', '.xlsx']
    ALLOWED_MIMETYPES = [
        'text/csv',
        'text/plain',
        'application/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    # Configuration détection
    SAMPLE_SIZE = 128 * 1024  # 128 KB pour détection encodage
    SNIFFER_SIZE = 5 * 1024   # 5 KB pour détection séparateur
    PREVIEW_ROWS = 10         # Lignes prévisualisation par défaut
    
    def __init__(self, organization, user):
        self.organization = organization
        self.user = user
    
    def upload_file(self, file: UploadedFile, entity: str) -> ImportJob:
        """
        Upload sécurisé avec validation complète
        
        Args:
            file: Fichier uploadé Django
            entity: Type d'entité (grape_variety, parcelle, etc.)
            
        Returns:
            ImportJob créé
            
        Raises:
            ValidationError: Si fichier invalide
        """
        # Validation sécurité
        self._validate_file_security(file)
        
        # Stockage temporaire sécurisé
        temp_path, sha256_hash = self._store_temporary_file(file)
        
        # Création job
        job = ImportJob.objects.create(
            organization=self.organization,
            entity=entity,
            filename=self._sanitize_filename(file.name),
            original_filename=file.name,
            size_bytes=file.size,
            sha256=sha256_hash,
            file_path=temp_path,
            created_by=self.user,
            status='uploaded'
        )
        
        return job
    
    def preview_file(self, job: ImportJob, rows: int = None, sheet: int = 0) -> Dict[str, Any]:
        """
        Génère aperçu avec détection format
        
        Args:
            job: Job d'import
            rows: Nombre lignes aperçu (défaut: PREVIEW_ROWS)
            sheet: Feuille XLSX (défaut: 0)
            
        Returns:
            Dict avec header, sample, detected, warnings
        """
        if rows is None:
            rows = self.PREVIEW_ROWS
            
        # Validation
        if not os.path.exists(job.file_path):
            raise ValidationError("Fichier temporaire introuvable")
        
        # Détection format
        detected = self._detect_file_format(job.file_path)
        
        # Lecture échantillon
        sample_data = self._read_sample_data(job.file_path, rows, detected, sheet)
        
        # Anti-injection CSV
        sample_data = self._neutralize_csv_injection(sample_data)
        
        # Mise à jour job
        job.detected_encoding = detected['encoding']
        job.detected_delimiter = detected['delimiter']
        job.detected_decimal = detected['decimal']
        job.has_header = detected['has_header']
        job.status = 'previewed'
        job.save()
        
        return {
            'header': sample_data[0] if detected['has_header'] and sample_data else [],
            'sample': sample_data[1:] if detected['has_header'] and sample_data else sample_data,
            'detected': detected,
            'warnings': self._generate_warnings(detected, sample_data)
        }
    
    def _validate_file_security(self, file: UploadedFile) -> None:
        """Validation sécurité complète"""
        
        # Taille
        if file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"Fichier trop volumineux: {file.size} bytes > {self.MAX_FILE_SIZE} bytes"
            )
        
        # Extension
        _, ext = os.path.splitext(file.name.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Extension non autorisée: {ext}. Extensions autorisées: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # MIME type
        mime_type, _ = mimetypes.guess_type(file.name)
        if mime_type not in self.ALLOWED_MIMETYPES:
            raise ValidationError(
                f"Type MIME non autorisé: {mime_type}"
            )
        
        # Magic bytes (basique)
        file.seek(0)
        first_bytes = file.read(512)
        file.seek(0)
        
        if ext == '.xlsx':
            # XLSX = ZIP avec signature
            if not first_bytes.startswith(b'PK'):
                raise ValidationError("Fichier XLSX invalide (magic bytes)")
        elif ext == '.csv':
            # CSV = texte lisible
            try:
                first_bytes.decode('utf-8', errors='ignore')
            except:
                raise ValidationError("Fichier CSV invalide (non-texte)")
    
    def _store_temporary_file(self, file: UploadedFile) -> Tuple[str, str]:
        """
        Stockage temporaire sécurisé avec hash SHA-256
        
        Returns:
            Tuple (file_path, sha256_hash)
        """
        # Dossier temporaire sécurisé
        temp_dir = os.path.join(
            tempfile.gettempdir(),
            'monchai_imports',
            str(self.organization.id)
        )
        os.makedirs(temp_dir, mode=0o700, exist_ok=True)
        
        # Fichier temporaire
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=os.path.splitext(file.name)[1],
            dir=temp_dir
        )
        
        # Écriture streaming avec hash
        hasher = hashlib.sha256()
        total_size = 0
        
        try:
            with os.fdopen(temp_fd, 'wb') as temp_file:
                file.seek(0)
                for chunk in file.chunks(chunk_size=64 * 1024):
                    temp_file.write(chunk)
                    hasher.update(chunk)
                    total_size += len(chunk)
                    
                    # Protection taille
                    if total_size > self.MAX_FILE_SIZE:
                        raise ValidationError("Fichier trop volumineux")
        except:
            # Nettoyage si erreur
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
        
        return temp_path, hasher.hexdigest()
    
    def _detect_file_format(self, file_path: str) -> Dict[str, Any]:
        """
        Détection encodage, séparateur, décimal, header
        
        Returns:
            Dict avec encoding, delimiter, decimal, has_header
        """
        detected = {
            'encoding': 'utf-8',
            'delimiter': ',',
            'decimal': '.',
            'has_header': True,
            'confidence': 1.0
        }
        
        # Lecture échantillon
        with open(file_path, 'rb') as f:
            sample = f.read(self.SAMPLE_SIZE)
        
        # 1. Détection encodage
        try:
            sample.decode('utf-8')
            detected['encoding'] = 'utf-8'
            detected['confidence'] = 1.0
        except UnicodeDecodeError:
            # Utiliser chardet
            result = chardet.detect(sample)
            if result['confidence'] > 0.4:
                detected['encoding'] = result['encoding']
                detected['confidence'] = result['confidence']
            else:
                detected['encoding'] = 'iso-8859-1'  # Fallback
                detected['confidence'] = 0.3
        
        # 2. Détection séparateur (CSV seulement)
        if file_path.lower().endswith('.csv'):
            try:
                # Décoder échantillon
                text_sample = sample.decode(detected['encoding'], errors='ignore')
                sniffer_sample = text_sample[:self.SNIFFER_SIZE]
                
                # csv.Sniffer
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sniffer_sample, delimiters=',;\t')
                    detected['delimiter'] = dialect.delimiter
                except:
                    # Fallback: compter occurrences
                    delimiters = [',', ';', '\t']
                    counts = {d: sniffer_sample.count(d) for d in delimiters}
                    detected['delimiter'] = max(counts, key=counts.get)
            except:
                detected['delimiter'] = ','  # Fallback
        
        # 3. Détection décimal
        # Heuristique simple: si beaucoup de "," dans nombres → décimal français
        try:
            text_sample = sample.decode(detected['encoding'], errors='ignore')[:self.SNIFFER_SIZE]
            comma_in_numbers = 0
            dot_in_numbers = 0
            
            # Regex simple pour détecter nombres
            import re
            numbers = re.findall(r'\b\d+[,.]\d+\b', text_sample)
            for num in numbers:
                if ',' in num:
                    comma_in_numbers += 1
                if '.' in num:
                    dot_in_numbers += 1
            
            if comma_in_numbers > dot_in_numbers and comma_in_numbers > 2:
                detected['decimal'] = ','
            else:
                detected['decimal'] = '.'
        except:
            detected['decimal'] = '.'
        
        # 4. Détection header
        try:
            # Lire premières lignes
            with open(file_path, 'r', encoding=detected['encoding']) as f:
                if file_path.lower().endswith('.csv'):
                    reader = csv.reader(f, delimiter=detected['delimiter'])
                    lines = [next(reader, None) for _ in range(3)]
                    lines = [line for line in lines if line]
                    
                    if len(lines) >= 2:
                        # Première ligne vs autres: diversité vs homogénéité types
                        first_line = lines[0]
                        second_line = lines[1]
                        
                        # Compter non-numériques dans première ligne
                        non_numeric_first = sum(1 for cell in first_line if not self._is_numeric(cell))
                        non_numeric_second = sum(1 for cell in second_line if not self._is_numeric(cell))
                        
                        # Si première ligne majoritairement non-numérique → header
                        detected['has_header'] = non_numeric_first > len(first_line) / 2
                    else:
                        detected['has_header'] = True  # Défaut
                else:
                    detected['has_header'] = True  # XLSX assume header
        except:
            detected['has_header'] = True
        
        return detected
    
    def _read_sample_data(self, file_path: str, rows: int, detected: Dict, sheet: int = 0) -> List[List[str]]:
        """
        Lecture échantillon données
        
        Returns:
            Liste de lignes (liste de cellules)
        """
        sample_data = []
        
        try:
            if file_path.lower().endswith('.xlsx'):
                # XLSX avec openpyxl
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(file_path, read_only=True)
                    worksheet = workbook.worksheets[sheet] if sheet < len(workbook.worksheets) else workbook.active
                    
                    for i, row in enumerate(worksheet.iter_rows(values_only=True)):
                        if i >= rows:
                            break
                        sample_data.append([str(cell) if cell is not None else '' for cell in row])
                    
                    workbook.close()
                except ImportError:
                    raise ValidationError("openpyxl requis pour fichiers XLSX")
                except Exception as e:
                    raise ValidationError(f"Erreur lecture XLSX: {str(e)}")
            
            else:
                # CSV
                with open(file_path, 'r', encoding=detected['encoding']) as f:
                    reader = csv.reader(f, delimiter=detected['delimiter'])
                    for i, row in enumerate(reader):
                        if i >= rows:
                            break
                        sample_data.append(row)
        
        except Exception as e:
            raise ValidationError(f"Erreur lecture fichier: {str(e)}")
        
        return sample_data
    
    def _neutralize_csv_injection(self, data: List[List[str]]) -> List[List[str]]:
        """
        Neutralise injection CSV (cellules commençant par = + - @ \t)
        """
        neutralized = []
        for row in data:
            neutralized_row = []
            for cell in row:
                if isinstance(cell, str) and cell.startswith(('=', '+', '-', '@', '\t')):
                    neutralized_row.append(f"'{cell}")
                else:
                    neutralized_row.append(cell)
            neutralized.append(neutralized_row)
        return neutralized
    
    def _generate_warnings(self, detected: Dict, sample_data: List[List[str]]) -> List[str]:
        """Génère warnings basés sur détection"""
        warnings = []
        
        # Encodage incertain
        if detected.get('confidence', 1.0) < 0.6:
            warnings.append(f"Encodage incertain ({detected['encoding']}, confiance: {detected['confidence']:.1%})")
        
        # Lignes longueurs variables
        if sample_data:
            lengths = [len(row) for row in sample_data]
            if len(set(lengths)) > 1:
                warnings.append(f"Lignes de longueurs variables: {min(lengths)}-{max(lengths)} colonnes")
        
        # Peu de données
        if len(sample_data) < 3:
            warnings.append("Très peu de données dans le fichier")
        
        return warnings
    
    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie nom de fichier"""
        # Supprimer path, caractères dangereux
        filename = os.path.basename(filename)
        filename = filename.replace(' ', '_')
        # Garder seulement alphanumériques, points, tirets, underscores
        import re
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        return filename[:255]  # Limite longueur
    
    def _is_numeric(self, value: str) -> bool:
        """Test si valeur est numérique"""
        if not isinstance(value, str):
            return False
        try:
            float(value.replace(',', '.'))
            return True
        except (ValueError, AttributeError):
            return False
