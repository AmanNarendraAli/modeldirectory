from django.conf import settings
from django.db import models


class Conversation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        BLOCKED = "blocked", "Blocked"

    participant_one = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_one"
    )
    participant_two = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_two"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="initiated_conversations"
    )
    is_agency_initiated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["participant_one", "participant_two"],
                name="unique_conversation_pair",
            )
        ]

    def __str__(self):
        return f"{self.participant_one} ↔ {self.participant_two} [{self.status}]"

    def get_other_participant(self, user):
        return self.participant_two if self.participant_one == user else self.participant_one

    def is_participant(self, user):
        return user in (self.participant_one, self.participant_two)

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"


class MessageBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_users"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("blocker", "blocked")]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"
