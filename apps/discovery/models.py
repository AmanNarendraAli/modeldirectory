from django.conf import settings
from django.db import models


class SavedAgency(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_agencies")
    agency = models.ForeignKey("agencies.Agency", on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "agency")]
        ordering = ["-created_at"]
        verbose_name_plural = "Saved Agencies"

    def __str__(self):
        return f"{self.user} saved {self.agency}"


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed_profile = models.ForeignKey(
        "models_app.ModelProfile", on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("follower", "followed_profile")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower} follows {self.followed_profile}"
