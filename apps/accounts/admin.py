"""
Interface d'administration Django pour les modèles d'authentification.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Organization, Membership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration des utilisateurs avec email comme USERNAME_FIELD"""
    
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {'fields': ('first_name', 'last_name', 'username')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Administration des organisations"""
    
    list_display = ('name', 'siret', 'currency', 'created_at')
    list_filter = ('currency', 'created_at')
    search_fields = ('name', 'siret')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'siret', 'tva_number', 'currency')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class MembershipInline(admin.TabularInline):
    """Inline pour afficher les memberships dans l'admin Organization"""
    model = Membership
    extra = 0
    readonly_fields = ('joined_at', 'updated_at')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Administration des adhésions (memberships)"""
    
    list_display = ('user', 'organization', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    readonly_fields = ('joined_at', 'updated_at')
    
    fieldsets = (
        ('Adhésion', {
            'fields': ('user', 'organization', 'role', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('joined_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Ajout des inlines
OrganizationAdmin.inlines = [MembershipInline]
