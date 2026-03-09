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
    fieldsets = (
        ("Identity", {"fields": ("user", "public_display_name", "slug", "gender", "date_of_birth", "city", "country", "bio")}),
        ("Measurements", {"fields": ("height_cm", "bust_cm", "waist_cm", "hips_cm", "inseam_cm", "shoe_size", "hair_color", "eye_color")}),
        ("Photos", {"fields": ("profile_image", "cover_image")}),
        ("Links", {"fields": ("instagram_url", "website_url", "contact_email")}),
        ("Availability", {"fields": ("available_for_editorial", "available_for_runway", "available_for_commercial", "available_for_fittings")}),
        ("Status", {"fields": ("is_public", "is_discoverable", "verification_status", "represented_by_agency")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
