from django.contrib import admin
from .models import ResourceArticle


@admin.register(ResourceArticle)
class ResourceArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "is_published", "published_at"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "summary"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at"]
