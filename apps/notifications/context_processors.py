from django.db.models import Q

from apps.messaging.models import Conversation, Message


def unread_notification_count(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {"unread_notification_count": count}
    return {"unread_notification_count": 0}


def unread_message_indicator(request):
    if request.user.is_authenticated:
        user = request.user
        # Single query: EXISTS subquery is fast and avoids loading conversation objects
        has_unread = Message.objects.filter(
            Q(conversation__participant_one=user) | Q(conversation__participant_two=user),
            conversation__status=Conversation.Status.ACCEPTED,
            is_read=False,
        ).exclude(sender=user).exists()
        return {"has_unread_messages": has_unread}
    return {"has_unread_messages": False}
