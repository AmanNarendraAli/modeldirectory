from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.discovery.models import Follow
from apps.notifications.models import Notification


@receiver(post_save, sender=Follow)
def notify_on_follow(sender, instance, created, **kwargs):
    """Create a notification when someone follows a model."""
    if not created:
        return
    Notification.objects.create(
        user=instance.followed_profile.user,
        notification_type=Notification.Type.FOLLOW,
        actor=instance.follower,
        target_profile=instance.followed_profile,
    )
