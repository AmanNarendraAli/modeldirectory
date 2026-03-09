from django.contrib import admin
from .models import PortfolioPost, PortfolioAsset


class PortfolioAssetInline(admin.TabularInline):
    model = PortfolioAsset
    extra = 1


@admin.register(PortfolioPost)
class PortfolioPostAdmin(admin.ModelAdmin):
    list_display = ("title", "owner_profile", "is_public", "published_at", "created_at")
    list_filter = ("is_public",)
    search_fields = ("title", "owner_profile__user__email", "owner_profile__public_display_name")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [PortfolioAssetInline]


@admin.register(PortfolioAsset)
class PortfolioAssetAdmin(admin.ModelAdmin):
    list_display = ("portfolio_post", "display_order", "alt_text")
    search_fields = ("portfolio_post__title",)
