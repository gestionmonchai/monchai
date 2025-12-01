"""
Interface d'administration pour la facturation
DB Roadmap 04 - Facturation & Comptabilité
"""

from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Invoice, InvoiceLine, CreditNote, Payment, Reconciliation,
    AccountMap, GLEntry
)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    fields = ['sku', 'description', 'qty', 'unit_price', 'discount_pct', 'tax_code', 'total_ttc']
    readonly_fields = ['id', 'organization', 'total_ht', 'total_tva', 'total_ttc']


class ReconciliationInline(admin.TabularInline):
    model = Reconciliation
    extra = 0
    fields = ['payment', 'amount_allocated']
    readonly_fields = ['id', 'organization', 'created_at']


class InvoiceAdmin(admin.ModelAdmin):
    """Admin pour billing.Invoice - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['number', 'customer', 'date_issue', 'due_date', 'status', 'total_ttc', 'amount_due', 'is_overdue']
    list_filter = ['status', 'date_issue', 'organization']
    search_fields = ['number', 'customer__legal_name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tva', 'total_ttc', 'amount_paid', 'amount_due']
    inlines = [InvoiceLineInline, ReconciliationInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['customer', 'order', 'number', 'date_issue', 'due_date', 'currency', 'status']
        }),
        ('Totaux', {
            'fields': ['total_ht', 'total_tva', 'total_ttc', 'amount_paid', 'amount_due']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">En retard</span>')
        return 'Non'
    is_overdue.short_description = 'En retard'
    is_overdue.admin_order_field = 'due_date'
    
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


class InvoiceLineAdmin(admin.ModelAdmin):
    """Admin pour billing.InvoiceLine - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['invoice', 'sku', 'description', 'qty', 'unit_price', 'total_ttc']
    list_filter = ['tax_code', 'organization']
    search_fields = ['invoice__number', 'sku__label', 'description']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tva', 'total_ttc']
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class CreditNoteAdmin(admin.ModelAdmin):
    """Admin pour billing.CreditNote - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['number', 'invoice', 'date_issue', 'reason', 'total_ttc']
    list_filter = ['date_issue', 'organization']
    search_fields = ['number', 'invoice__number', 'reason']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['invoice', 'number', 'date_issue', 'reason']
        }),
        ('Totaux', {
            'fields': ['total_ht', 'total_tva', 'total_ttc']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class PaymentAdmin(admin.ModelAdmin):
    """Admin pour billing.Payment - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['customer', 'method', 'amount', 'currency', 'date_received', 'amount_unallocated', 'reference']
    list_filter = ['method', 'currency', 'date_received', 'organization']
    search_fields = ['customer__legal_name', 'reference']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at', 'amount_allocated', 'amount_unallocated']
    inlines = [ReconciliationInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['customer', 'method', 'amount', 'currency', 'date_received', 'reference']
        }),
        ('Allocation', {
            'fields': ['amount_allocated', 'amount_unallocated']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class ReconciliationAdmin(admin.ModelAdmin):
    """Admin pour billing.Reconciliation - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['payment', 'invoice', 'amount_allocated', 'created_at']
    list_filter = ['created_at', 'organization']
    search_fields = ['payment__customer__legal_name', 'invoice__number']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at']
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class AccountMapAdmin(admin.ModelAdmin):
    """Admin pour billing.AccountMap - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['mapping_type', 'key', 'account_code', 'account_name', 'organization']
    list_filter = ['mapping_type', 'organization']
    search_fields = ['key', 'account_code', 'account_name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Mapping', {
            'fields': ['mapping_type', 'key', 'account_code', 'account_name']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class GLEntryAdmin(admin.ModelAdmin):
    """Admin pour billing.GLEntry - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['date', 'journal', 'doc_number', 'account_code', 'label', 'debit', 'credit']
    list_filter = ['journal', 'doc_type', 'date', 'organization']
    search_fields = ['doc_number', 'account_code', 'label']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Écriture', {
            'fields': ['journal', 'date', 'doc_type', 'doc_id', 'doc_number', 'account_code', 'label']
        }),
        ('Montants', {
            'fields': ['debit', 'credit']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_add_permission(self, request):
        # Les écritures sont générées automatiquement
        return False
    
    def has_change_permission(self, request, obj=None):
        # Les écritures ne peuvent pas être modifiées
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Les écritures ne peuvent pas être supprimées
        return False
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return False  # Écritures générées automatiquement
    def has_change_permission(self, request, obj=None):
        return False  # Écritures ne peuvent pas être modifiées


# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Factures : /billing/factures/
# - Paiements : /billing/paiements/  
# - Avoirs : /billing/avoirs/
# - Comptabilité : /billing/comptabilite/

# Enregistrement conditionnel pour debug technique uniquement
if getattr(settings, 'ADMIN_ENABLE_BILLING_DEBUG', False):
    admin.site.register(Invoice, InvoiceAdmin)
    admin.site.register(InvoiceLine, InvoiceLineAdmin)
    admin.site.register(CreditNote, CreditNoteAdmin)
    admin.site.register(Payment, PaymentAdmin)
    admin.site.register(Reconciliation, ReconciliationAdmin)
    admin.site.register(AccountMap, AccountMapAdmin)
    admin.site.register(GLEntry, GLEntryAdmin)
