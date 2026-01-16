from django.contrib import admin
from .models import Mise, LotCommercial, MiseLigne
from .models_supplies import Supply, SupplyCategory, SupplyStock, SupplyMovement


@admin.register(Mise)
class MiseAdmin(admin.ModelAdmin):
    list_display = ("code_of", "date", "campagne", "state")
    search_fields = ("code_of", "campagne")
    list_filter = ("state", "campagne")


@admin.register(LotCommercial)
class LotCommercialAdmin(admin.ModelAdmin):
    list_display = (
        "code_lot", "date_mise", "format_ml", "quantite_unites", "stock_disponible",
        "inao_code", "nc_code", "emb_code", "capsule_crd", "capsule_crd_color",
    )
    search_fields = ("code_lot", "cuvee__name", "inao_code", "nc_code", "emb_code")
    list_filter = ("format_ml", "date_mise", "capsule_crd")
    fieldsets = (
        (None, {
            "fields": ("mise", "code_lot", "cuvee", "format_ml", "date_mise", "quantite_unites", "stock_disponible"),
        }),
        ("Réglementation", {
            "fields": ("inao_code", "nc_code", "emb_code", "capsule_crd", "capsule_crd_color", "capsule_marking"),
        }),
    )


@admin.register(MiseLigne)
class MiseLigneAdmin(admin.ModelAdmin):
    list_display = ("mise", "lot_tech_source", "format_ml", "quantite_unites", "volume_l")
    search_fields = ("mise__code_of", "lot_tech_source__code")


# =============================================================================
# ADMIN FOURNITURES (SUPPLIES)
# =============================================================================

@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent', 'organization', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('sort_order', 'name')


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('reference', 'name', 'supply_type', 'category', 'unit', 'purchase_price', 'main_supplier', 'is_active')
    list_filter = ('supply_type', 'category', 'is_active', 'is_stockable', 'organization')
    search_fields = ('name', 'reference', 'supplier_ref', 'description')
    ordering = ('name',)
    autocomplete_fields = ['main_supplier', 'category']
    readonly_fields = ('created_at', 'updated_at', 'last_purchase_date', 'last_purchase_price')
    fieldsets = (
        ('Identification', {
            'fields': ('organization', 'category', 'supply_type', 'name', 'reference', 'supplier_ref', 'description')
        }),
        ('Unités & Prix', {
            'fields': ('unit', 'packaging_qty', 'min_order_qty', 'purchase_price', 'vat_rate')
        }),
        ('Fournisseur', {
            'fields': ('main_supplier', 'last_purchase_price', 'last_purchase_date')
        }),
        ('Gestion de stock', {
            'fields': ('is_stockable', 'stock_min', 'stock_max', 'lead_time_days')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_discontinued', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SupplyStock)
class SupplyStockAdmin(admin.ModelAdmin):
    list_display = ('supply', 'location', 'batch_number', 'quantity', 'reserved_qty', 'expiry_date')
    list_filter = ('location', 'organization')
    search_fields = ('supply__name', 'batch_number')


@admin.register(SupplyMovement)
class SupplyMovementAdmin(admin.ModelAdmin):
    list_display = ('date', 'movement_type', 'reason', 'supply', 'quantity', 'location', 'reference')
    list_filter = ('movement_type', 'reason', 'location', 'organization')
    search_fields = ('supply__name', 'reference', 'notes')
    readonly_fields = ('created_at', 'created_by')
