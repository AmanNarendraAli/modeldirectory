from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.agencies.models import AgencyStaff
from apps.models_app.models import ModelProfile

from .models import User


class ModelProfileInline(admin.StackedInline):
    model = ModelProfile
    can_delete = False
    extra = 0
    classes = ("collapse",)


class AgencyStaffInline(admin.TabularInline):
    model = AgencyStaff
    extra = 0
    classes = ("collapse",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "role", "is_active", "is_verified_email", "created_at")
    list_filter = ("role", "is_active", "is_staff", "is_verified_email")
    search_fields = ("email", "full_name", "phone_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ModelProfileInline, AgencyStaffInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone_number")}),
        ("Role & Status", {"fields": ("role", "is_active", "is_staff", "is_superuser", "is_verified_email", "onboarding_completed")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )
