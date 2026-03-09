from django.contrib import admin
from .models import Application, ApplicationSnapshot


class ApplicationSnapshotInline(admin.StackedInline):
    model = ApplicationSnapshot
    can_delete = False
    readonly_fields = ("created_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_profile", "agency", "status", "submitted_at", "reviewed_at")
    list_filter = ("status", "agency")
    search_fields = ("applicant_profile__user__email", "applicant_profile__public_display_name", "agency__name")
    readonly_fields = ("updated_at",)
    inlines = [ApplicationSnapshotInline]


@admin.register(ApplicationSnapshot)
class ApplicationSnapshotAdmin(admin.ModelAdmin):
    list_display = ("application", "applicant_name", "city", "height_cm", "created_at")
    search_fields = ("applicant_name", "application__agency__name")
    readonly_fields = ("created_at",)
