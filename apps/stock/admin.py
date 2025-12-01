"""
Administration des modèles de stock
"""

from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    SKU, StockVracBalance, StockSKUBalance,
    StockVracMove, StockSKUMove, StockTransfer
)




class SKUAdmin(admin.ModelAdmin):
    """Admin pour stock.SKU - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['label', 'cuvee', 'uom', 'volume_by_uom_to_l', 'is_active', 'organization']
    list_filter = ['is_active', 'organization', 'uom', 'created_at']
    search_fields = ['label', 'code_barres', 'cuvee__nom']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    fieldsets = [
        (None, {
            'fields': ['organization', 'cuvee', 'uom', 'volume_by_uom_to_l']
        }),
        ('Produit', {
            'fields': ['label', 'code_barres', 'is_active']
        }),
        ('Métadonnées', {
            'fields': ['id', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


class StockVracBalanceAdmin(admin.ModelAdmin):
    """Admin pour stock.StockVracBalance - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['lot', 'warehouse', 'qty_l', 'organization', 'updated_at']
    list_filter = ['organization', 'warehouse', 'updated_at']
    search_fields = ['lot__nom', 'warehouse__name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lot', 'warehouse', 'organization')


class StockSKUBalanceAdmin(admin.ModelAdmin):
    """Admin pour stock.StockSKUBalance - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['sku', 'warehouse', 'qty_units', 'organization', 'updated_at']
    list_filter = ['organization', 'warehouse', 'updated_at']
    search_fields = ['sku__label', 'warehouse__name']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sku', 'warehouse', 'organization')


class StockVracMoveAdmin(admin.ModelAdmin):
    """Admin pour stock.StockVracMove - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['created_at', 'move_type', 'lot', 'qty_l', 'src_warehouse', 'dst_warehouse', 'user']
    list_filter = ['move_type', 'organization', 'created_at', 'src_warehouse', 'dst_warehouse']
    search_fields = ['lot__nom', 'user__email', 'notes']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        (None, {
            'fields': ['organization', 'lot', 'move_type', 'qty_l']
        }),
        ('Entrepôts', {
            'fields': ['src_warehouse', 'dst_warehouse']
        }),
        ('Référence', {
            'fields': ['ref_type', 'ref_id', 'user', 'notes']
        }),
        ('Métadonnées', {
            'fields': ['id', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lot', 'src_warehouse', 'dst_warehouse', 'user', 'organization'
        )


class StockSKUMoveAdmin(admin.ModelAdmin):
    """Admin pour stock.StockSKUMove - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['created_at', 'move_type', 'sku', 'qty_units', 'src_warehouse', 'dst_warehouse', 'user']
    list_filter = ['move_type', 'organization', 'created_at', 'src_warehouse', 'dst_warehouse']
    search_fields = ['sku__label', 'user__email', 'notes']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        (None, {
            'fields': ['organization', 'sku', 'move_type', 'qty_units']
        }),
        ('Entrepôts', {
            'fields': ['src_warehouse', 'dst_warehouse']
        }),
        ('Référence', {
            'fields': ['ref_type', 'ref_id', 'user', 'notes']
        }),
        ('Métadonnées', {
            'fields': ['id', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sku', 'src_warehouse', 'dst_warehouse', 'user', 'organization'
        )


class StockTransferAdmin(admin.ModelAdmin):
    """Admin pour stock.StockTransfer - DÉSACTIVÉ pour utilisateurs normaux"""
    list_display = ['created_at', 'lot', 'volume_l', 'from_warehouse', 'to_warehouse', 'created_by', 'organization']
    list_filter = ['organization', 'created_at', 'from_warehouse', 'to_warehouse']
    search_fields = ['lot__code', 'notes', 'created_by__email']
    readonly_fields = ['id', 'row_version', 'created_at', 'updated_at', 'client_token']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        (None, {
            'fields': ['organization', 'lot', 'volume_l']
        }),
        ('Transfert', {
            'fields': ['from_warehouse', 'to_warehouse']
        }),
        ('Informations', {
            'fields': ['created_by', 'notes']
        }),
        ('Technique', {
            'fields': ['client_token', 'id', 'row_version', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lot', 'from_warehouse', 'to_warehouse', 'created_by', 'organization'
        )


# Ajouter les méthodes de permissions pour tous les modèles stock
def add_superuser_permissions(admin_class):
    """Ajoute les méthodes de permissions pour bloquer l'accès aux utilisateurs normaux"""
    admin_class.has_module_permission = lambda self, request: request.user.is_superuser
    admin_class.has_view_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_add_permission = lambda self, request: request.user.is_superuser
    admin_class.has_change_permission = lambda self, request, obj=None: request.user.is_superuser
    admin_class.has_delete_permission = lambda self, request, obj=None: request.user.is_superuser

# Appliquer les permissions à toutes les classes admin
add_superuser_permissions(SKUAdmin)
add_superuser_permissions(StockVracBalanceAdmin)
add_superuser_permissions(StockSKUBalanceAdmin)
add_superuser_permissions(StockVracMoveAdmin)
add_superuser_permissions(StockSKUMoveAdmin)
add_superuser_permissions(StockTransferAdmin)

# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Produits (SKU) : /catalogue/produits/
# - Stock vrac : /stock/vrac/
# - Stock produits : /stock/produits/
# - Mouvements : /stock/mouvements/
# - Transferts : /stock/transferts/

# Enregistrement conditionnel pour debug technique uniquement
if getattr(settings, 'ADMIN_ENABLE_STOCK_DEBUG', False):
    admin.site.register(SKU, SKUAdmin)
    admin.site.register(StockVracBalance, StockVracBalanceAdmin)
    admin.site.register(StockSKUBalance, StockSKUBalanceAdmin)
    admin.site.register(StockVracMove, StockVracMoveAdmin)
    admin.site.register(StockSKUMove, StockSKUMoveAdmin)
    admin.site.register(StockTransfer, StockTransferAdmin)
