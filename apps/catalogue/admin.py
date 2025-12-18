from django.contrib import admin
from .models import Lot, MouvementLot, Article, ArticleCategory, ArticleStock, StockMovement


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    search_fields = ('name',)
    list_filter = ('organization',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'article_type', 'category', 'price_ht', 'unit', 'is_active')
    list_filter = ('article_type', 'is_active', 'organization', 'category')
    search_fields = ('name', 'sku', 'description')
    ordering = ('name',)
    fieldsets = (
        ('Identification', {
            'fields': ('organization', 'category', 'article_type', 'name', 'sku', 'description')
        }),
        ('Commercial', {
            'fields': ('price_ht', 'vat_rate', 'unit', 'is_active')
        }),
        ('Paramètres', {
            'fields': ('is_stock_managed',)
        })
    )


@admin.register(ArticleStock)
class ArticleStockAdmin(admin.ModelAdmin):
    list_display = ('article', 'location', 'batch_number', 'quantity', 'updated_at')
    list_filter = ('location', 'organization')
    search_fields = ('article__name', 'batch_number')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('date', 'movement_type', 'article', 'quantity', 'location', 'batch_number', 'reference')
    list_filter = ('movement_type', 'location', 'organization', 'date')
    search_fields = ('article__name', 'reference', 'notes')
    readonly_fields = ('date', 'created_by')


# @admin.register(Lot)  # DÉSENREGISTRÉ
class LotAdmin(admin.ModelAdmin):
    list_display = ('numero_lot', 'cuvee', 'volume_initial', 'volume_actuel', 'entrepot', 'organization', 'is_empty')
    list_filter = ('cuvee', 'entrepot', 'organization', 'statut')
    search_fields = ('numero_lot', 'cuvee__nom', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('numero_lot', 'cuvee', 'volume_initial', 'volume_actuel', 'entrepot', 'organization')
        }),
        ('Informations détaillées', {
            'fields': ('statut', 'notes'),
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_empty(self, obj):
        return obj.is_empty()
    is_empty.boolean = True
    is_empty.short_description = 'Vide'


# @admin.register(MouvementLot)  # DÉSENREGISTRÉ
class MouvementLotAdmin(admin.ModelAdmin):
    list_display = ('lot', 'type_mouvement', 'volume_mouvement', 'date_mouvement', 'entrepot_source')
    list_filter = ('type_mouvement', 'date_mouvement', 'lot__organization')
    search_fields = ('lot__numero', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('lot', 'type_mouvement', 'description', 'date_mouvement')
        }),
        ('Volumes', {
            'fields': ('volume_avant', 'volume_mouvement', 'volume_apres'),
        }),
        ('Entrepôts', {
            'fields': ('entrepot_source', 'entrepot_destination'),
        }),
        ('Informations détaillées', {
            'fields': ('notes',),
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


# DÉSENREGISTREMENT COMPLET - Modèles métier interdits dans l'admin
# Utiliser les interfaces back-office dédiées :
# - Lots : /catalogue/lots/
# - Mouvements : /catalogue/mouvements/

# Enregistrement conditionnel pour debug technique uniquement
from django.conf import settings
if getattr(settings, 'ADMIN_ENABLE_CATALOGUE_DEBUG', False):
    admin.site.register(Lot, LotAdmin)
    admin.site.register(MouvementLot, MouvementLotAdmin)
