from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "notification_type", "actor", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
    raw_id_fields = ["user", "actor"]
