"""
Admin pour les templates de documents
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.sales.models_documents import DocumentTemplate, DocumentPreset


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type_display', 'organization', 'is_default_badge', 'is_active', 'updated_at']
    list_filter = ['document_type', 'is_default', 'is_active', 'paper_size', 'orientation']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = [
        ('Identification', {
            'fields': ['id', 'organization', 'name', 'document_type', 'description']
        }),
        ('Configuration', {
            'fields': ['is_default', 'is_active', 'paper_size', 'orientation']
        }),
        ('Marges (mm)', {
            'fields': ['margin_top', 'margin_bottom', 'margin_left', 'margin_right'],
            'classes': ['collapse']
        }),
        ('Contenu HTML', {
            'fields': ['html_header', 'html_body', 'html_footer']
        }),
        ('Styles', {
            'fields': ['custom_css'],
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ['created_at', 'updated_at', 'created_by'],
            'classes': ['collapse']
        }),
    ]
    
    def document_type_display(self, obj):
        return obj.get_document_type_display()
    document_type_display.short_description = 'Type'
    
    def is_default_badge(self, obj):
        if obj.is_default:
            return format_html('<span style="color: green;">★ Défaut</span>')
        return '-'
    is_default_badge.short_description = 'Défaut'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentPreset)
class DocumentPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'primary_color_swatch', 'secondary_color_swatch', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'generated_css', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Identification', {
            'fields': ['id', 'organization', 'name', 'description']
        }),
        ('Couleurs', {
            'fields': ['primary_color', 'secondary_color', 'text_color']
        }),
        ('Polices', {
            'fields': ['font_family', 'font_size_base']
        }),
        ('Logo', {
            'fields': ['logo_width', 'logo_position'],
            'classes': ['collapse']
        }),
        ('CSS Généré', {
            'fields': ['generated_css'],
            'classes': ['collapse']
        }),
        ('Statut', {
            'fields': ['is_active', 'created_at', 'updated_at']
        }),
    ]
    
    def primary_color_swatch(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background: {}; border: 1px solid #ccc; border-radius: 3px;"></span> {}',
            obj.primary_color,
            obj.primary_color
        )
    primary_color_swatch.short_description = 'Couleur primaire'
    
    def secondary_color_swatch(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background: {}; border: 1px solid #ccc; border-radius: 3px;"></span> {}',
            obj.secondary_color,
            obj.secondary_color
        )
    secondary_color_swatch.short_description = 'Couleur secondaire'
