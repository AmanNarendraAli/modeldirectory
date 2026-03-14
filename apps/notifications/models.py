from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        FOLLOW = "follow", "New Follower"
        MESSAGE_REQUEST = "message_request", "Message Request"
        NEW_MESSAGE = "new_message", "New Message"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="triggered_notifications"
    )
    target_profile = models.ForeignKey(
        "models_app.ModelProfile", on_delete=models.CASCADE, null=True, blank=True
    )
    target_conversation = models.ForeignKey(
        "messaging.Conversation", on_delete=models.CASCADE, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor} → {self.user}: {self.get_notification_type_display()}"

    @property
    def display_text(self):
        actor_name = getattr(self.actor, "full_name", str(self.actor))
        if self.notification_type == self.Type.FOLLOW:
            return f"{actor_name} started following you"
        elif self.notification_type == self.Type.MESSAGE_REQUEST:
            return f"{actor_name} wants to message you"
        elif self.notification_type == self.Type.NEW_MESSAGE:
            return f"New message from {actor_name}"
        return f"Notification from {actor_name}"
