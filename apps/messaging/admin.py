from django.contrib import admin

from .models import Conversation, Message, MessageBlock


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["participant_one", "participant_two", "status", "is_agency_initiated", "created_at"]
    list_filter = ["status", "is_agency_initiated"]
    raw_id_fields = ["participant_one", "participant_two", "initiated_by"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "content_preview", "is_read", "created_at"]
    list_filter = ["is_read"]
    raw_id_fields = ["conversation", "sender"]

    def content_preview(self, obj):
        return obj.content[:80]


@admin.register(MessageBlock)
class MessageBlockAdmin(admin.ModelAdmin):
    list_display = ["blocker", "blocked", "created_at"]
    raw_id_fields = ["blocker", "blocked"]
