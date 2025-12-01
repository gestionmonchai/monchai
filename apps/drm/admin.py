from django.contrib import admin
from .models import DRMLine, INAOCode


@admin.register(DRMLine)
class DRMLineAdmin(admin.ModelAdmin):
    list_display = ("date", "organization", "type", "volume_l", "campagne", "ref_kind")
    list_filter = ("type", "campagne", "organization")
    search_fields = ("ref_kind", "ref_id")
    ordering = ("-date", "-created_at")


@admin.register(INAOCode)
class INAOCodeAdmin(admin.ModelAdmin):
    list_display = ("code_inao", "code_nc", "appellation_label", "color", "packaging_min_l", "packaging_max_l", "abv_min_pct", "abv_max_pct", "active")
    list_filter = ("color", "active")
    search_fields = ("code_inao", "code_nc", "appellation_label", "condition_text")
    ordering = ("code_inao", "code_nc")
