"""
Admin pour la gestion des contacts (tiers)
"""

from django.contrib import admin
from .models import (
    Contact, ContactRole, Address, ContactPerson,
    ClientProfile, SupplierProfile, ContactTag, ContactTagLink, ContactEvent
)


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ['label', 'address_type', 'street', 'postal_code', 'city', 'country', 'is_default']


class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0
    fields = ['first_name', 'last_name', 'job_title', 'email', 'phone', 'role', 'is_primary']


class ContactTagLinkInline(admin.TabularInline):
    model = ContactTagLink
    extra = 0
    autocomplete_fields = ['tag']


@admin.register(ContactRole)
class ContactRoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'icon', 'color', 'sort_order']
    ordering = ['sort_order']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'partner_type', 'email', 'phone', 'is_active', 'roles_list']
    list_filter = ['partner_type', 'segment', 'is_active', 'is_archived', 'roles', 'organization']
    search_fields = ['name', 'email', 'phone', 'vat_number', 'siret', 'code']
    readonly_fields = ['code', 'display_id', 'name_normalized', 'created_at', 'updated_at']
    filter_horizontal = ['roles']
    inlines = [AddressInline, ContactPersonInline, ContactTagLinkInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'display_id', 'organization', 'partner_type', 'name', 'name_normalized')
        }),
        ('Personne physique', {
            'fields': ('first_name', 'last_name'),
            'classes': ('collapse',)
        }),
        ('Rôles & Segment', {
            'fields': ('roles', 'segment')
        }),
        ('Coordonnées', {
            'fields': ('email', 'phone', 'mobile', 'website')
        }),
        ('Identification légale', {
            'fields': ('siret', 'siren', 'vat_number', 'naf_code'),
            'classes': ('collapse',)
        }),
        ('Localisation', {
            'fields': ('country_code', 'language', 'timezone', 'currency'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_active', 'is_archived', 'source', 'internal_ref')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'row_version'),
            'classes': ('collapse',)
        }),
    )
    
    def roles_list(self, obj):
        return ', '.join(r.label for r in obj.roles.all())
    roles_list.short_description = 'Rôles'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['partner', 'label', 'address_type', 'city', 'country', 'is_default']
    list_filter = ['address_type', 'country', 'is_default']
    search_fields = ['partner__name', 'street', 'city', 'postal_code']
    autocomplete_fields = ['partner']


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'partner', 'job_title', 'email', 'phone', 'role', 'is_primary']
    list_filter = ['role', 'is_primary', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'partner__name']
    autocomplete_fields = ['partner']


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['partner', 'payment_terms', 'price_category', 'credit_limit', 'current_balance']
    list_filter = ['payment_terms', 'price_category']
    search_fields = ['partner__name']
    autocomplete_fields = ['partner']


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ['partner', 'payment_terms', 'incoterm', 'lead_time_days', 'is_approved']
    list_filter = ['payment_terms', 'incoterm', 'is_approved']
    search_fields = ['partner__name']
    autocomplete_fields = ['partner']


@admin.register(ContactTag)
class ContactTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'organization']
    list_filter = ['organization']
    search_fields = ['name']


@admin.register(ContactEvent)
class ContactEventAdmin(admin.ModelAdmin):
    list_display = ['partner', 'event_type', 'title', 'event_date', 'created_by']
    list_filter = ['event_type', 'event_date']
    search_fields = ['partner__name', 'title', 'description']
    autocomplete_fields = ['partner']
    date_hierarchy = 'event_date'
