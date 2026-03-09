from django.contrib import admin
from .models import SavedAgency, Follow


@admin.register(SavedAgency)
class SavedAgencyAdmin(admin.ModelAdmin):
    list_display = ("user", "agency", "created_at")
    list_filter = ("agency",)
    search_fields = ("user__email", "agency__name")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed_profile", "created_at")
    search_fields = ("follower__email", "followed_profile__public_display_name")
