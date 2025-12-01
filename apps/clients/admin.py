"""
Interface d'administration pour la gestion des clients - Roadmap 36
"""

from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import Customer, CustomerTag, CustomerTagLink, CustomerActivity


# @admin.register(Customer)  # DÉSENREGISTRÉ - Utiliser /clients/
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'segment', 'email', 'phone', 'country_code', 
        'vat_number', 'is_active', 'tag_count', 'updated_at'
    ]
    list_filter = ['segment', 'is_active', 'country_code', 'created_at']
    search_fields = ['name', 'name_norm', 'email', 'phone', 'vat_number']
    readonly_fields = ['id', 'name_norm', 'created_at', 'updated_at', 'row_version']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'segment', 'is_active')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'country_code')
        }),
        ('Informations légales', {
            'fields': ('vat_number',)
        }),
        ('Technique', {
            'fields': ('id', 'name_norm', 'organization', 'created_at', 'updated_at', 'row_version'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')
    
    def tag_count(self, obj):
        count = obj.tag_links.count()
        if count > 0:
            return format_html('<span class="badge badge-info">{}</span>', count)
        return '-'
    tag_count.short_description = 'Tags'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau client
            obj.organization = request.current_org
        super().save_model(request, obj, form, change)
    
    def has_module_permission(self, request):
        """Seuls les superadmins peuvent voir ce modèle dans l'admin"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Seuls les superadmins peuvent voir ce modèle"""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Seuls les superadmins peuvent ajouter"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Seuls les superadmins peuvent modifier"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Seuls les superadmins peuvent supprimer"""
        return request.user.is_superuser


# @admin.register(CustomerTag)  # DÉSENREGISTRÉ
class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'customer_count', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'row_version']
    
    fieldsets = (
        ('Tag', {
            'fields': ('name', 'color', 'description')
        }),
        ('Technique', {
            'fields': ('id', 'organization', 'created_at', 'updated_at', 'row_version'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color, obj.name
        )
    color_display.short_description = 'Couleur'
    
    def customer_count(self, obj):
        count = obj.customer_links.count()
        return format_html('<span class="badge badge-secondary">{}</span>', count)
    customer_count.short_description = 'Clients'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau tag
            obj.organization = request.current_org
        super().save_model(request, obj, form, change)


# @admin.register(CustomerTagLink)  # DÉSENREGISTRÉ
class CustomerTagLinkAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tag', 'created_at']
    list_filter = ['tag', 'created_at']
    search_fields = ['customer__name', 'tag__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'row_version']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'tag')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau lien
            obj.organization = request.current_org
        super().save_model(request, obj, form, change)


# @admin.register(CustomerActivity)  # DÉSENREGISTRÉ
class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ['customer', 'activity_type', 'title', 'activity_date', 'ref_type']
    list_filter = ['activity_type', 'activity_date', 'ref_type']
    search_fields = ['customer__name', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'row_version']
    date_hierarchy = 'activity_date'
    
    fieldsets = (
        ('Activité', {
            'fields': ('customer', 'activity_type', 'title', 'description', 'activity_date')
        }),
        ('Référence', {
            'fields': ('ref_type', 'ref_id')
        }),
        ('Technique', {
            'fields': ('id', 'organization', 'created_at', 'updated_at', 'row_version'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle activité
            obj.organization = request.current_org
        super().save_model(request, obj, form, change)


# Ajouter les méthodes de permissions pour tous les modèles clients
def add_superuser_permissions_clients(admin_class):
    """Ajoute les méthodes de permissions pour bloquer l'accès aux utilisateurs normaux"""
    admin_class.has_module_permission = lambda self, request: request.user.is_superuser
    admin_class.has_view_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_add_permission = lambda self, request: request.user.is_superuser
    admin_class.has_change_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_delete_permission = lambda self, request, obj=None: request.user.is_superuser

# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Clients : /clients/
# - Tags clients : Géré via interface clients
# - Activités : Géré via CRM

# Enregistrement conditionnel pour debug technique uniquement
from django.conf import settings
if getattr(settings, 'ADMIN_ENABLE_CLIENTS_DEBUG', False):
    # Appliquer les permissions aux classes admin clients
    add_superuser_permissions_clients(CustomerTagAdmin)
    add_superuser_permissions_clients(CustomerTagLinkAdmin)
    add_superuser_permissions_clients(CustomerActivityAdmin)
    
    admin.site.register(CustomerTag, CustomerTagAdmin)
    admin.site.register(CustomerTagLink, CustomerTagLinkAdmin)
    admin.site.register(CustomerActivity, CustomerActivityAdmin)
