"""
Interface d'administration pour les ventes
DB Roadmap 03 - Ventes, Clients & Pricing
"""

from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    TaxCode, PriceList, PriceItem, CustomerPriceList,
    Quote, QuoteLine, Order, OrderLine, StockReservation
)
# Note: Customer est maintenant importé depuis partners.models (Contact)
# L'admin est géré dans partners/admin.py


class TaxCodeAdmin(admin.ModelAdmin):
    """Admin pour sales.TaxCode - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['code', 'name', 'rate_pct', 'country', 'is_active', 'organization']
    list_filter = ['is_active', 'country', 'organization']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['code', 'name', 'rate_pct', 'country', 'is_active']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


# CustomerAdmin supprimé - Customer/Contact est maintenant géré dans partners/admin.py


class PriceItemInline(admin.TabularInline):
    model = PriceItem
    extra = 1
    fields = ['sku', 'unit_price', 'min_qty', 'discount_pct']
    readonly_fields = ['id', 'organization']


class PriceListAdmin(admin.ModelAdmin):
    """Admin pour sales.PriceList - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['name', 'currency', 'valid_from', 'valid_to', 'is_active', 'items_count', 'organization']
    list_filter = ['currency', 'is_active', 'organization', 'valid_from']
    search_fields = ['name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    inlines = [PriceItemInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['name', 'currency', 'is_active']
        }),
        ('Validité', {
            'fields': ['valid_from', 'valid_to']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Nb éléments'


class PriceItemAdmin(admin.ModelAdmin):
    """Admin pour sales.PriceItem - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['price_list', 'sku', 'unit_price', 'min_qty', 'discount_pct', 'effective_price']
    list_filter = ['price_list', 'organization']
    search_fields = ['sku__label', 'price_list__name']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at', 'effective_price']
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['price_list', 'sku', 'unit_price', 'min_qty', 'discount_pct', 'effective_price']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


class CustomerPriceListAdmin(admin.ModelAdmin):
    """Admin pour sales.CustomerPriceList - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['customer', 'price_list', 'priority', 'created_at']
    list_filter = ['priority', 'created_at']
    search_fields = ['customer__legal_name', 'price_list__name']


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0
    fields = ['sku', 'description', 'qty', 'unit_price', 'discount_pct', 'tax_code', 'total_ttc']
    readonly_fields = ['id', 'organization', 'total_ht', 'total_tax', 'total_ttc']


class QuoteAdmin(admin.ModelAdmin):
    """Admin pour sales.Quote - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['quote_number', 'customer', 'status', 'total_ttc', 'currency', 'valid_until', 'created_at']
    list_filter = ['status', 'currency', 'organization', 'created_at']
    search_fields = ['customer__legal_name', 'id']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tax', 'total_ttc']
    inlines = [QuoteLineInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['customer', 'currency', 'status', 'valid_until']
        }),
        ('Totaux', {
            'fields': ['total_ht', 'total_tax', 'total_ttc']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def quote_number(self, obj):
        return f"DEV-{obj.id.hex[:8].upper()}"
    quote_number.short_description = 'Numéro'


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    fields = ['sku', 'description', 'qty', 'unit_price', 'discount_pct', 'tax_code', 'total_ttc']
    readonly_fields = ['id', 'organization', 'total_ht', 'total_tax', 'total_ttc']


class StockReservationInline(admin.TabularInline):
    model = StockReservation
    extra = 0
    fields = ['sku', 'warehouse', 'qty_units']
    readonly_fields = ['id', 'organization', 'created_at']


class OrderAdmin(admin.ModelAdmin):
    """Admin pour sales.Order - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['order_number', 'customer', 'status', 'payment_status', 'total_ttc', 'currency', 'created_at']
    list_filter = ['status', 'payment_status', 'currency', 'organization', 'created_at']
    search_fields = ['customer__legal_name', 'id']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tax', 'total_ttc']
    inlines = [OrderLineInline, StockReservationInline]
    
    fieldsets = [
        ('Informations générales', {
            'fields': ['customer', 'quote', 'currency', 'status', 'payment_status']
        }),
        ('Totaux', {
            'fields': ['total_ht', 'total_tax', 'total_ttc']
        }),
        ('Métadonnées', {
            'fields': ['id', 'organization', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def order_number(self, obj):
        return f"CMD-{obj.id.hex[:8].upper()}"
    order_number.short_description = 'Numéro'


class QuoteLineAdmin(admin.ModelAdmin):
    """Admin pour sales.QuoteLine - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['quote', 'sku', 'qty', 'unit_price', 'discount_pct', 'total_ttc']
    list_filter = ['quote__status', 'organization']
    search_fields = ['quote__customer__legal_name', 'sku__label']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tax', 'total_ttc']


class OrderLineAdmin(admin.ModelAdmin):
    """Admin pour sales.OrderLine - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['order', 'sku', 'qty', 'unit_price', 'discount_pct', 'total_ttc']
    list_filter = ['order__status', 'organization']
    search_fields = ['order__customer__legal_name', 'sku__label']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at', 'total_ht', 'total_tax', 'total_ttc']


class StockReservationAdmin(admin.ModelAdmin):
    """Admin pour sales.StockReservation - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['order', 'sku', 'warehouse', 'qty_units', 'created_at']
    list_filter = ['warehouse', 'organization', 'created_at']
    search_fields = ['order__customer__legal_name', 'sku__label']
    readonly_fields = ['id', 'organization', 'row_version', 'created_at', 'updated_at']


# Ajouter les méthodes de permissions pour tous les modèles sales
def add_superuser_permissions_sales(admin_class):
    """Ajoute les méthodes de permissions pour bloquer l'accès aux utilisateurs normaux"""
    admin_class.has_module_permission = lambda self, request: request.user.is_superuser
    admin_class.has_view_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_add_permission = lambda self, request: request.user.is_superuser
    admin_class.has_change_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_delete_permission = lambda self, request, obj=None: request.user.is_superuser

# Appliquer les permissions à toutes les classes admin sales
add_superuser_permissions_sales(TaxCodeAdmin)
add_superuser_permissions_sales(PriceListAdmin)
add_superuser_permissions_sales(PriceItemAdmin)
add_superuser_permissions_sales(CustomerPriceListAdmin)
add_superuser_permissions_sales(QuoteAdmin)
add_superuser_permissions_sales(OrderAdmin)
add_superuser_permissions_sales(QuoteLineAdmin)
add_superuser_permissions_sales(OrderLineAdmin)
add_superuser_permissions_sales(StockReservationAdmin)

# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Clients : /clients/
# - Devis : /sales/devis/
# - Commandes : /sales/commandes/
# - Tarifs : /sales/tarifs/
# - Configuration TVA : /sales/configuration/

# Enregistrement conditionnel pour debug technique uniquement
if getattr(settings, 'ADMIN_ENABLE_SALES_DEBUG', False):
    admin.site.register(TaxCode, TaxCodeAdmin)
    admin.site.register(PriceList, PriceListAdmin)
    admin.site.register(PriceItem, PriceItemAdmin)
    admin.site.register(CustomerPriceList, CustomerPriceListAdmin)
    admin.site.register(Quote, QuoteAdmin)
    admin.site.register(Order, OrderAdmin)
    admin.site.register(QuoteLine, QuoteLineAdmin)
    admin.site.register(OrderLine, OrderLineAdmin)
    admin.site.register(StockReservation, StockReservationAdmin)
