from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, Exists, OuterRef
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect

from apps.models_app.models import ModelProfile
from apps.notifications.models import Notification
from .models import Conversation, Message, MessageBlock


def _get_user_conversations(user):
    """Return all conversations where the user is a participant."""
    return Conversation.objects.filter(
        Q(participant_one=user) | Q(participant_two=user)
    ).select_related("participant_one", "participant_two", "initiated_by")


def _get_or_normalize_conversation(user_a, user_b):
    """Find an existing conversation between two users (order-independent)."""
    return Conversation.objects.filter(
        Q(participant_one=user_a, participant_two=user_b)
        | Q(participant_one=user_b, participant_two=user_a)
    ).first()


def _is_blocked(user_a, user_b):
    """Check if either user has blocked the other."""
    return MessageBlock.objects.filter(
        Q(blocker=user_a, blocked=user_b) | Q(blocker=user_b, blocked=user_a)
    ).exists()


def _attach_other_participant(conversations, user):
    """Attach `other_participant` attribute to each conversation for template use."""
    result = list(conversations)
    for conv in result:
        conv.other_participant = conv.get_other_participant(user)
    return result


@login_required
def inbox(request):
    user = request.user
    conversations = _get_user_conversations(user)

    # Accepted conversations with last message info
    accepted = (
        conversations
        .filter(status=Conversation.Status.ACCEPTED)
        .annotate(last_message_at=Max("messages__created_at"))
        .order_by("-last_message_at")
    )

    # Pending requests where this user is the RECIPIENT (not initiator)
    requests_received = conversations.filter(
        status=Conversation.Status.PENDING
    ).exclude(initiated_by=user)

    # Pending requests where this user SENT (waiting for response)
    requests_sent = conversations.filter(
        status=Conversation.Status.PENDING, initiated_by=user
    )

    # Unread message count for messages link
    unread_message_count = Message.objects.filter(
        conversation__in=conversations.filter(status=Conversation.Status.ACCEPTED),
        is_read=False,
    ).exclude(sender=user).count()

    tab = request.GET.get("tab", "messages")

    return render(request, "messaging/inbox.html", {
        "accepted_conversations": _attach_other_participant(accepted, user),
        "requests_received": _attach_other_participant(requests_received, user),
        "requests_sent": _attach_other_participant(requests_sent, user),
        "unread_message_count": unread_message_count,
        "active_tab": tab,
    })


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()

    other_user = conversation.get_other_participant(request.user)
    all_messages = conversation.messages.select_related("sender").all()

    # Mark messages from the other user as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    # Determine if the user can send messages
    can_send = (
        conversation.status == Conversation.Status.ACCEPTED
        or (conversation.status == Conversation.Status.PENDING and conversation.initiated_by == request.user)
    )
    # Even if pending and initiator, they already sent one message — can't send more
    if conversation.status == Conversation.Status.PENDING and conversation.initiated_by == request.user:
        can_send = False

    is_pending_for_me = (
        conversation.status == Conversation.Status.PENDING
        and conversation.initiated_by != request.user
    )

    return render(request, "messaging/conversation_detail.html", {
        "conversation": conversation,
        "other_user": other_user,
        "messages_list": all_messages,
        "can_send": can_send,
        "is_pending_for_me": is_pending_for_me,
    })


@login_required
def start_conversation(request, slug):
    """Start a new conversation with a model. POST with message content."""
    if request.method != "POST":
        return redirect("model-detail", slug=slug)

    target_profile = get_object_or_404(ModelProfile, slug=slug)
    target_user = target_profile.user

    # Can't message yourself
    if target_user == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect("model-detail", slug=slug)

    # Check for blocks
    if _is_blocked(request.user, target_user):
        django_messages.error(request, "You cannot message this user.")
        return redirect("model-detail", slug=slug)

    # Check if conversation already exists
    existing = _get_or_normalize_conversation(request.user, target_user)
    if existing:
        if existing.status == Conversation.Status.BLOCKED:
            django_messages.error(request, "You cannot message this user.")
            return redirect("model-detail", slug=slug)
        if existing.status in (Conversation.Status.ACCEPTED, Conversation.Status.PENDING):
            return redirect("conversation-detail", pk=existing.pk)
        # If declined, allow a new request by resetting status
        if existing.status == Conversation.Status.DECLINED:
            existing.status = Conversation.Status.PENDING
            existing.initiated_by = request.user
            existing.save(update_fields=["status", "initiated_by", "updated_at"])
            conversation = existing
        else:
            conversation = existing
    else:
        # Determine if this is an agency-initiated conversation
        is_agency = request.user.is_agency_staff
        conversation = Conversation.objects.create(
            participant_one=request.user,
            participant_two=target_user,
            initiated_by=request.user,
            is_agency_initiated=is_agency,
            status=Conversation.Status.ACCEPTED if is_agency else Conversation.Status.PENDING,
        )

    # Save the first message
    content = request.POST.get("message", "").strip()
    if content:
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
        )

        # Create notification
        if conversation.status == Conversation.Status.PENDING:
            Notification.objects.create(
                user=target_user,
                notification_type=Notification.Type.MESSAGE_REQUEST,
                actor=request.user,
                target_conversation=conversation,
            )
        else:
            Notification.objects.create(
                user=target_user,
                notification_type=Notification.Type.NEW_MESSAGE,
                actor=request.user,
                target_conversation=conversation,
            )

    return redirect("conversation-detail", pk=conversation.pk)


@login_required
def send_message(request, pk):
    """Send a message in an existing conversation."""
    if request.method != "POST":
        return redirect("conversation-detail", pk=pk)

    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()

    if conversation.status != Conversation.Status.ACCEPTED:
        django_messages.error(request, "This conversation is not active.")
        return redirect("conversation-detail", pk=pk)

    content = request.POST.get("message", "").strip()
    if content:
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
        )
        # Update conversation timestamp
        conversation.save(update_fields=["updated_at"])

        # Notify the other participant
        other_user = conversation.get_other_participant(request.user)
        Notification.objects.create(
            user=other_user,
            notification_type=Notification.Type.NEW_MESSAGE,
            actor=request.user,
            target_conversation=conversation,
        )

    return redirect("conversation-detail", pk=pk)


@login_required
def accept_request(request, pk):
    if request.method != "POST":
        return redirect("conversation-detail", pk=pk)

    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()
    if conversation.initiated_by == request.user:
        return HttpResponseForbidden()
    if conversation.status != Conversation.Status.PENDING:
        return redirect("conversation-detail", pk=pk)

    conversation.status = Conversation.Status.ACCEPTED
    conversation.save(update_fields=["status", "updated_at"])
    django_messages.success(request, "Message request accepted.")
    return redirect("conversation-detail", pk=pk)


@login_required
def decline_request(request, pk):
    if request.method != "POST":
        return redirect("conversation-detail", pk=pk)

    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()
    if conversation.initiated_by == request.user:
        return HttpResponseForbidden()
    if conversation.status != Conversation.Status.PENDING:
        return redirect("conversation-detail", pk=pk)

    conversation.status = Conversation.Status.DECLINED
    conversation.save(update_fields=["status", "updated_at"])
    django_messages.success(request, "Message request declined.")
    return redirect("message-inbox")


@login_required
def block_user(request, pk):
    if request.method != "POST":
        return redirect("conversation-detail", pk=pk)

    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()

    other_user = conversation.get_other_participant(request.user)

    # Create block record
    MessageBlock.objects.get_or_create(blocker=request.user, blocked=other_user)

    conversation.status = Conversation.Status.BLOCKED
    conversation.save(update_fields=["status", "updated_at"])
    django_messages.success(request, "User blocked. They can no longer message you.")
    return redirect("message-inbox")
