"""
Interface d'administration ergonomique pour les référentiels
Inspirée de l'excellente UX de sales/billing avec filtres latéraux
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Cepage, Parcelle, ParcelleEncepagement, Unite, Cuvee, Entrepot


# @admin.register(Cepage)  # DÉSENREGISTRÉ
class CepageAdmin(admin.ModelAdmin):
    list_display = ['nom', 'couleur_badge', 'code', 'is_active', 'cuvees_count', 'organization']
    list_filter = ['couleur', 'is_active', 'organization', 'created_at']
    search_fields = ['nom', 'code', 'notes']
    readonly_fields = ['name_norm', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom', 'code', 'couleur', 'is_active']
        }),
        ('Description', {
            'fields': ['notes']
        }),
        ('Métadonnées', {
            'fields': ['name_norm', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def couleur_badge(self, obj):
        colors = {
            'rouge': '#dc3545',
            'blanc': '#f8f9fa',
            'rose': '#e83e8c'
        }
        color = colors.get(obj.couleur, '#6c757d')
        text_color = 'white' if obj.couleur != 'blanc' else 'black'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, text_color, obj.get_couleur_display()
        )
    couleur_badge.short_description = 'Couleur'
    couleur_badge.admin_order_field = 'couleur'
    
    def cuvees_count(self, obj):
        count = obj.cuvees.count()
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    cuvees_count.short_description = 'Nb cuvées'


class ParcelleEncepagementInline(admin.TabularInline):
    model = ParcelleEncepagement
    extra = 1
    fields = ['cepage', 'pourcentage', 'rang_debut', 'rang_fin', 'annee_plantation', 'porte_greffe', 'densite_pieds_ha']
    verbose_name = "Encépagement"
    verbose_name_plural = "Encépagement (rangs/blocs)"
    autocomplete_fields = ['cepage']


# @admin.register(Parcelle)  # DÉSENREGISTRÉ
class ParcelleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'surface', 'encepagement_count', 'commune', 'appellation', 'lieu_dit', 'organization']
    list_filter = ['commune', 'appellation', 'organization', 'created_at']
    search_fields = ['nom', 'lieu_dit', 'commune', 'appellation', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ParcelleEncepagementInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom', 'surface']
        }),
        ('Localisation', {
            'fields': ['lieu_dit', 'commune', 'appellation']
        }),
        ('Description', {
            'fields': ['notes']
        }),
        ('Métadonnées', {
            'fields': ['organization', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def encepagement_count(self, obj):
        count = obj.encepagements.count()
        if count > 0:
            return format_html('<strong>{}</strong> bloc(s)', count)
        return '—'
    encepagement_count.short_description = 'Encépagement'


# @admin.register(Unite)  # DÉSENREGISTRÉ
class UniteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'symbole', 'type_unite_badge', 'facteur_conversion', 'organization']
    list_filter = ['type_unite', 'organization', 'created_at']
    search_fields = ['nom', 'symbole']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom', 'symbole', 'type_unite']
        }),
        ('Conversion', {
            'fields': ['facteur_conversion']
        }),
        ('Métadonnées', {
            'fields': ['organization', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def type_unite_badge(self, obj):
        colors = {
            'volume': '#007bff',
            'poids': '#28a745',
            'surface': '#ffc107',
            'quantite': '#6c757d'
        }
        color = colors.get(obj.type_unite, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_type_unite_display()
        )
    type_unite_badge.short_description = 'Type'
    type_unite_badge.admin_order_field = 'type_unite'


class CuveeInline(admin.TabularInline):
    model = Cuvee.cepages.through
    extra = 0
    verbose_name = "Cépage utilisé"
    verbose_name_plural = "Cépages utilisés dans cette cuvée"


# @admin.register(Cuvee)  # DÉSENREGISTRÉ
class CuveeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'couleur_badge', 'classification_badge', 'appellation', 'degre_alcool', 'lots_count', 'organization']
    list_filter = ['couleur', 'classification', 'appellation', 'organization', 'created_at']
    search_fields = ['nom', 'appellation', 'description', 'notes_degustation']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['cepages']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom', 'couleur', 'classification', 'appellation', 'degre_alcool']
        }),
        ('Composition', {
            'fields': ['cepages']
        }),
        ('Description', {
            'fields': ['description', 'notes_degustation']
        }),
        ('Métadonnées', {
            'fields': ['organization', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def couleur_badge(self, obj):
        colors = {
            'rouge': '#dc3545',
            'blanc': '#f8f9fa',
            'rose': '#e83e8c',
            'effervescent': '#17a2b8'
        }
        color = colors.get(obj.couleur, '#6c757d')
        text_color = 'white' if obj.couleur != 'blanc' else 'black'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, text_color, obj.get_couleur_display()
        )
    couleur_badge.short_description = 'Couleur'
    couleur_badge.admin_order_field = 'couleur'
    
    def classification_badge(self, obj):
        colors = {
            'aoc': '#28a745',
            'igp': '#007bff',
            'vsig': '#ffc107',
            'vdf': '#6c757d'
        }
        color = colors.get(obj.classification, '#6c757d')
        text_color = 'white' if obj.classification != 'vsig' else 'black'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, text_color, obj.get_classification_display()
        )
    classification_badge.short_description = 'Classification'
    classification_badge.admin_order_field = 'classification'
    
    def lots_count(self, obj):
        count = obj.lots.count()
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    lots_count.short_description = 'Nb lots'


# @admin.register(Entrepot)  # DÉSENREGISTRÉ
class EntrepotAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_entrepot_badge', 'capacite', 'temperature_range', 'organization']
    list_filter = ['type_entrepot', 'organization', 'created_at']
    search_fields = ['nom', 'adresse', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['nom', 'type_entrepot', 'adresse']
        }),
        ('Caractéristiques', {
            'fields': ['capacite', 'temperature_min', 'temperature_max']
        }),
        ('Description', {
            'fields': ['notes']
        }),
        ('Métadonnées', {
            'fields': ['organization', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def type_entrepot_badge(self, obj):
        colors = {
            'chai': '#28a745',
            'depot': '#007bff',
            'boutique': '#ffc107',
            'cave': '#6f42c1',
            'autre': '#6c757d'
        }
        color = colors.get(obj.type_entrepot, '#6c757d')
        text_color = 'white' if obj.type_entrepot != 'boutique' else 'black'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, text_color, obj.get_type_entrepot_display()
        )
    type_entrepot_badge.short_description = 'Type'
    type_entrepot_badge.admin_order_field = 'type_entrepot'


# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Cépages : /referentiels/cepages/
# - Parcelles : /referentiels/parcelles/
# - Unités : /referentiels/unites/
# - Cuvées : /catalogue/cuvees/
# - Entrepôts : /referentiels/entrepots/

# Enregistrement conditionnel pour debug technique uniquement
from django.conf import settings
if getattr(settings, 'ADMIN_ENABLE_REFERENTIELS_DEBUG', False):
    admin.site.register(Cepage, CepageAdmin)
    admin.site.register(Parcelle, ParcelleAdmin)
    admin.site.register(Unite, UniteAdmin)
    admin.site.register(Cuvee, CuveeAdmin)
    admin.site.register(Entrepot, EntrepotAdmin)
