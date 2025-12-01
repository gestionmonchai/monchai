"""
Modèles pour le système d'import/export générique
Roadmaps CSV 1-5 : Pipeline complet upload → mapping → dry-run → execute
"""

import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.accounts.models import Organization

User = get_user_model()


class ImportJob(models.Model):
    """
    Job d'import avec pipeline complet
    CSV_1: Upload & Preview
    CSV_4: Exécution & Métriques
    """
    
    STATUS_CHOICES = [
        ('uploaded', 'Fichier uploadé'),
        ('previewed', 'Aperçu généré'),
        ('mapped', 'Mapping configuré'),
        ('dry_run', 'Validation effectuée'),
        ('running', 'Import en cours'),
        ('done', 'Import terminé'),
        ('failed', 'Import échoué'),
        ('cancelled', 'Import annulé'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='import_jobs')
    entity = models.CharField(max_length=50, help_text="Type d'entité: grape_variety, parcelle, unite, etc.")
    
    # Fichier
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, unique=True)
    file_path = models.CharField(max_length=500, help_text="Chemin stockage temporaire")
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    total_rows = models.PositiveIntegerField(null=True, blank=True)
    
    # Détection format
    detected_encoding = models.CharField(max_length=50, blank=True)
    detected_delimiter = models.CharField(max_length=5, blank=True)
    detected_decimal = models.CharField(max_length=5, blank=True)
    has_header = models.BooleanField(default=True)
    
    # Métriques exécution
    inserted_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_jobs')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    options = models.JSONField(default=dict, help_text="Options spécifiques: sheet XLSX, etc.")
    
    class Meta:
        db_table = 'import_job'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['organization', 'entity', 'status']),
            models.Index(fields=['organization', 'created_by', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"Import {self.entity} - {self.filename} ({self.status})"
    
    @property
    def progress_pct(self):
        """Calcul pourcentage progression"""
        if not self.total_rows:
            return 0
        processed = self.inserted_count + self.updated_count + self.skipped_count + self.error_count
        return min(100, int((processed / self.total_rows) * 100))
    
    @property
    def success_rate(self):
        """Taux de succès (inserted + updated) / total"""
        if not self.total_rows:
            return 0
        success = self.inserted_count + self.updated_count
        return int((success / self.total_rows) * 100)
    
    @property
    def duration_seconds(self):
        """Durée en secondes"""
        if not self.ended_at:
            return None
        return (self.ended_at - self.started_at).total_seconds()
    
    def clean_temp_file(self):
        """Supprime le fichier temporaire"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.unlink(self.file_path)
            except OSError:
                pass


class ImportJobRow(models.Model):
    """
    Ligne de job avec erreurs/warnings
    CSV_3: Dry-run validation
    CSV_5: Rapports détaillés
    """
    
    STATUS_CHOICES = [
        ('ok', 'Ligne valide'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur bloquante'),
    ]
    
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='rows')
    row_index = models.PositiveIntegerField(help_text="Numéro ligne dans fichier (1-based)")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    # Détail erreur/warning
    field = models.CharField(max_length=100, blank=True, help_text="Champ concerné")
    message = models.TextField(help_text="Message d'erreur/warning")
    suggestion = models.TextField(blank=True, help_text="Suggestion d'amélioration")
    
    # Données
    raw_data = models.JSONField(help_text="Données ligne originale")
    processed_data = models.JSONField(null=True, blank=True, help_text="Après transformations")
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'import_job_row'
        ordering = ['row_index']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['job', 'row_index']),
        ]
        unique_together = ['job', 'row_index']
    
    def __str__(self):
        return f"Ligne {self.row_index} - {self.status}: {self.message[:50]}"


class ImportMapping(models.Model):
    """
    Configuration mapping colonnes CSV → champs entité
    CSV_2: Mapping & Transformations
    """
    
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='mappings')
    csv_column = models.CharField(max_length=100, help_text="Nom colonne CSV")
    csv_index = models.PositiveIntegerField(help_text="Index colonne (0-based)")
    
    # Mapping
    entity_field = models.CharField(max_length=100, help_text="Champ entité cible")
    is_required = models.BooleanField(default=False)
    is_unique_key = models.BooleanField(default=False)
    
    # Transformations
    transforms = models.JSONField(default=list, help_text="Liste transformations: ['trim', 'unaccent']")
    options = models.JSONField(default=dict, help_text="Options transformation")
    
    # Métadonnées
    confidence = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], 
                                 help_text="Confiance auto-mapping (0-1)")
    
    class Meta:
        db_table = 'import_mapping'
        indexes = [
            models.Index(fields=['job', 'entity_field']),
        ]
        unique_together = [
            ['job', 'csv_column'],
            ['job', 'entity_field'],  # Un champ entité ne peut être mappé qu'une fois
        ]
    
    def __str__(self):
        return f"{self.csv_column} → {self.entity_field}"


class ImportTemplate(models.Model):
    """
    Templates de mapping réutilisables
    CSV_2: Persistance mapping par utilisateur
    """
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='import_templates')
    entity = models.CharField(max_length=50)
    name = models.CharField(max_length=100, help_text="Nom template")
    description = models.TextField(blank=True)
    
    # Configuration
    mapping_config = models.JSONField(help_text="Configuration mapping complète")
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistiques usage
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'import_template'
        ordering = ['-last_used_at', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'entity']),
            models.Index(fields=['created_by', '-created_at']),
        ]
        unique_together = ['organization', 'entity', 'name']
    
    def __str__(self):
        return f"Template {self.entity}: {self.name}"
    
    def increment_usage(self):
        """Incrémente compteur usage"""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])
