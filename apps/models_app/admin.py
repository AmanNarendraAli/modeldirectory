from django.contrib import admin
from .models import ModelProfile


@admin.register(ModelProfile)
class ModelProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "public_display_name", "city", "gender", "height_cm", "is_public", "is_discoverable", "verification_status")
    list_filter = ("gender", "is_public", "is_discoverable", "verification_status", "city",
                   "available_for_editorial", "available_for_runway", "available_for_commercial")
    search_fields = ("user__email", "user__full_name", "public_display_name", "slug", "city")
    prepopulated_fields = {"slug": ("public_display_name",)}
    readonly_fields = ("created_at", "updated_at")
