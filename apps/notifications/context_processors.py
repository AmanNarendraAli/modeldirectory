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
        user_conversations = Conversation.objects.filter(
            Q(participant_one=user) | Q(participant_two=user),
            status=Conversation.Status.ACCEPTED,
        )
        has_unread = Message.objects.filter(
            conversation__in=user_conversations,
            is_read=False,
        ).exclude(sender=user).exists()
        return {"has_unread_messages": has_unread}
    return {"has_unread_messages": False}
