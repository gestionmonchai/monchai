"""
ADMIN VITICULTURE - RECRÉÉ COMPLÈTEMENT
Interface d'administration pour tous les modèles viticoles
"""

from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    GrapeVariety, Appellation, Vintage, UnitOfMeasure,
    VineyardPlot, Cuvee, Warehouse, Lot, LotGrapeRatio, LotAssemblage
)


class BaseViticultureAdmin(admin.ModelAdmin):
    """Admin de base pour tous les modèles viticulture"""
    
    def get_readonly_fields(self, request, obj=None):
        """Champs readonly par défaut"""
        return ('id', 'row_version', 'created_at', 'updated_at')
    
    def get_list_filter(self, request):
        """Filtres par défaut"""
        return ('is_active', 'organization', 'created_at')
    
    def has_module_permission(self, request):
        """Seuls les superadmins peuvent voir les modèles viticulture dans l'admin"""
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
    
    def has_view_permission(self, request, obj=None):
        """Seuls les superadmins peuvent voir"""
        return request.user.is_superuser


# @admin.register(GrapeVariety)  # DÉSENREGISTRÉ
class GrapeVarietyAdmin(BaseViticultureAdmin):
    """Administration des cépages"""
    
    list_display = ('name', 'color_badge', 'organization', 'is_active_badge', 'created_at')
    list_filter = ('color', 'is_active', 'organization')
    search_fields = ('name', 'name_norm')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'color', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def color_badge(self, obj):
        """Badge coloré pour le type"""
        colors = {
            'red': '#dc3545',
            'white': '#6c757d', 
            'rosé': '#e83e8c'
        }
        color = colors.get(obj.color, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_color_display()
        )
    color_badge.short_description = 'Couleur'
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(Appellation)  # DÉSENREGISTRÉ
class AppellationAdmin(BaseViticultureAdmin):
    """Administration des appellations"""
    
    list_display = ('name', 'type_badge', 'organization', 'is_active_badge', 'created_at')
    list_filter = ('type', 'is_active', 'organization')
    search_fields = ('name', 'name_norm')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'type', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def type_badge(self, obj):
        """Badge pour le type d'appellation"""
        colors = {
            'aoc': '#28a745',
            'igp': '#17a2b8',
            'vin_de_france': '#6c757d'
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(Vintage)  # DÉSENREGISTRÉ
class VintageAdmin(BaseViticultureAdmin):
    """Administration des millésimes"""
    
    list_display = ('year', 'organization', 'is_active_badge', 'created_at')
    list_filter = ('year', 'is_active', 'organization')
    search_fields = ('year',)
    ordering = ('-year',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('year', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(UnitOfMeasure)  # DÉSENREGISTRÉ
class UnitOfMeasureAdmin(BaseViticultureAdmin):
    """Administration des unités de mesure"""
    
    list_display = ('name', 'code', 'base_ratio_display', 'organization', 'is_active_badge')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'code')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'code', 'base_ratio_to_l', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def base_ratio_display(self, obj):
        """Affichage formaté du ratio"""
        return f"{obj.base_ratio_to_l} L"
    base_ratio_display.short_description = 'Ratio vers L'
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(VineyardPlot)  # DÉSENREGISTRÉ
class VineyardPlotAdmin(BaseViticultureAdmin):
    """Administration des parcelles"""
    
    list_display = ('name', 'area_display', 'grape_variety', 'appellation', 'organization', 'is_active_badge')
    list_filter = ('grape_variety', 'appellation', 'is_active', 'organization')
    search_fields = ('name',)
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'area_ha', 'grape_variety', 'appellation', 'planting_year', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def area_display(self, obj):
        """Affichage formaté de la surface"""
        return f"{obj.area_ha} ha"
    area_display.short_description = 'Surface'
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(Cuvee)  # DÉSENREGISTRÉ
class CuveeAdmin(BaseViticultureAdmin):
    """Administration des cuvées - PRINCIPAL"""
    
    list_display = ('name', 'code', 'appellation', 'vintage', 'default_uom', 'organization', 'is_active_badge')
    list_filter = ('appellation', 'vintage', 'is_active', 'organization')
    search_fields = ('name', 'code')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'code', 'appellation', 'vintage', 'default_uom', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'
    
    def has_add_permission(self, request):
        """Permission d'ajout si l'utilisateur a le droit add_cuvee"""
        return request.user.is_superuser or request.user.has_perm('viticulture.add_cuvee')
    
    def has_change_permission(self, request, obj=None):
        """Permission de modification si l'utilisateur a le droit change_cuvee"""
        return request.user.is_superuser or request.user.has_perm('viticulture.change_cuvee')

    def has_view_permission(self, request, obj=None):
        """Permission de vue si l'utilisateur a le droit view_cuvee (ou change/add)"""
        return (
            request.user.is_superuser
            or request.user.has_perm('viticulture.view_cuvee')
            or request.user.has_perm('viticulture.change_cuvee')
            or request.user.has_perm('viticulture.add_cuvee')
        )

    def has_module_permission(self, request):
        """Affiche le module aux utilisateurs staff avec au moins 1 permission pertinente"""
        return (
            request.user.is_superuser
            or (
                request.user.is_staff and (
                    request.user.has_perm('viticulture.view_cuvee')
                    or request.user.has_perm('viticulture.change_cuvee')
                    or request.user.has_perm('viticulture.add_cuvee')
                )
            )
        )


# @admin.register(Warehouse)  # DÉSENREGISTRÉ
class WarehouseAdmin(BaseViticultureAdmin):
    """Administration des entrepôts"""
    
    list_display = ('name', 'location', 'organization', 'is_active_badge', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'location')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'location', 'organization', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_badge.short_description = 'Statut'


# @admin.register(Lot)  # DÉSENREGISTRÉ
class LotAdmin(BaseViticultureAdmin):
    """Administration des lots"""
    
    list_display = ('code', 'cuvee', 'volume_display', 'warehouse', 'organization', 'is_active_badge')
    list_filter = ('cuvee', 'warehouse', 'is_active', 'organization', 'created_at')
    search_fields = ('code', 'cuvee__name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('code', 'cuvee', 'volume_l', 'warehouse', 'organization', 'is_active')
        }),
        ('Informations détaillées', {
            'fields': ('alcohol_pct', 'status'),
        }),
        ('Métadonnées', {
            'fields': ('id', 'row_version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def volume_display(self, obj):
        """Affichage formaté du volume"""
        return f"{obj.volume_l} L"
    volume_display.short_description = 'Volume'


# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Cépages : /referentiels/cepages/
# - Appellations : /referentiels/appellations/
# - Millésimes : /referentiels/millesimes/
# - Unités : /referentiels/unites/
# - Entrepôts : /referentiels/entrepots/
# - Parcelles : /referentiels/parcelles/
# - Cuvées : /catalogue/cuvees/
# - Lots : /catalogue/lots/

# Enregistrement conditionnel pour debug technique uniquement
if getattr(settings, 'ADMIN_ENABLE_VITICULTURE_DEBUG', False):
    admin.site.register(GrapeVariety, GrapeVarietyAdmin)
    admin.site.register(Appellation, AppellationAdmin)
    admin.site.register(Vintage, VintageAdmin)
    admin.site.register(UnitOfMeasure, UnitOfMeasureAdmin)
    admin.site.register(VineyardPlot, VineyardPlotAdmin)
    admin.site.register(Warehouse, WarehouseAdmin)
    admin.site.register(Lot, LotAdmin)
    admin.site.register(LotGrapeRatio, LotGrapeRatioAdmin)
    admin.site.register(LotAssemblage, LotAssemblageAdmin)

# Note: Cuvee n'est pas enregistré par défaut pour éviter l'accès via l'admin
