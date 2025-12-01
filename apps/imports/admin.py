from django.contrib import admin
from .models import ImportJob, ImportJobRow, ImportMapping, ImportTemplate


# @admin.register(ImportJob)  # DÉSENREGISTRÉ
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity', 'status', 'organization', 'created_by', 'total_rows', 'started_at')
    list_filter = ('entity', 'status', 'organization', 'started_at')
    search_fields = ('id', 'filename', 'created_by__email')
    readonly_fields = ('id', 'started_at', 'sha256')
    
    fieldsets = (
        (None, {
            'fields': ('entity', 'status', 'organization', 'created_by')
        }),
        ('Fichier', {
            'fields': ('filename', 'original_filename', 'file_path', 'size_bytes', 'sha256'),
        }),
        ('Détection format', {
            'fields': ('detected_encoding', 'detected_delimiter', 'has_header'),
        }),
        ('Résultats', {
            'fields': ('total_rows', 'inserted_count', 'updated_count', 'skipped_count', 'error_count'),
        }),
        ('Métadonnées', {
            'fields': ('id', 'started_at'),
            'classes': ('collapse',)
        })
    )


# @admin.register(ImportJobRow)  # DÉSENREGISTRÉ
class ImportJobRowAdmin(admin.ModelAdmin):
    list_display = ('job', 'row_index', 'status', 'message_short', 'created_at')
    list_filter = ('status', 'job__entity', 'job__organization')
    search_fields = ('job__id', 'message')
    readonly_fields = ('created_at',)
    
    def message_short(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'


# @admin.register(ImportMapping)  # DÉSENREGISTRÉ
class ImportMappingAdmin(admin.ModelAdmin):
    list_display = ('job', 'csv_column', 'entity_field', 'is_required', 'confidence')
    list_filter = ('job__entity', 'job__organization', 'is_required')
    search_fields = ('csv_column', 'entity_field')


# @admin.register(ImportTemplate)  # DÉSENREGISTRÉ
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'entity', 'organization', 'created_by', 'usage_count', 'created_at')
    list_filter = ('entity', 'organization', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'usage_count', 'last_used_at')


# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Imports : /imports/
# - Templates : /imports/templates/

# Enregistrement conditionnel pour debug technique uniquement
from django.conf import settings
if getattr(settings, 'ADMIN_ENABLE_IMPORTS_DEBUG', False):
    admin.site.register(ImportJob, ImportJobAdmin)
    admin.site.register(ImportJobRow, ImportJobRowAdmin)
    admin.site.register(ImportMapping, ImportMappingAdmin)
    admin.site.register(ImportTemplate, ImportTemplateAdmin)
