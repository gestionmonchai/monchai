from django.contrib import admin
from .models import Mise, LotCommercial, MiseLigne


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
