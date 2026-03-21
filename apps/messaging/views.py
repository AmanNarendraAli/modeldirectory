from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, Exists, OuterRef
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from apps.accounts.models import User
from apps.agencies.models import AgencyStaff
from apps.models_app.models import ModelProfile
from apps.notifications.models import Notification
from .models import Conversation, Message, MessageBlock


def _get_user_conversations(user):
    """Return all conversations where the user is a participant."""
    return Conversation.objects.filter(
        Q(participant_one=user) | Q(participant_two=user)
    ).select_related(
        "participant_one", "participant_one__model_profile",
        "participant_two", "participant_two__model_profile",
        "initiated_by",
    )


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
    from django.urls import reverse
    from apps.agencies.models import AgencyStaff

    result = list(conversations)

    # Collect all other participant IDs to batch-fetch agency staff info
    other_users = []
    for conv in result:
        conv.other_participant = conv.get_other_participant(user)
        other_users.append(conv.other_participant)

    # Batch fetch agency staff roles with agency info
    other_user_ids = [u.pk for u in other_users]
    staff_map = {}
    for staff in AgencyStaff.objects.filter(user_id__in=other_user_ids).select_related("agency"):
        staff_map[staff.user_id] = staff

    for conv in result:
        other = conv.other_participant
        if other.is_agency_staff and other.pk in staff_map:
            staff = staff_map[other.pk]
            conv.other_role_label = f"Agency Staff – {staff.agency.name}"
            conv.other_profile_url = reverse("agency-detail", kwargs={"slug": staff.agency.slug})
            conv.other_avatar_url = staff.agency.logo_thumbnail.url if staff.agency.logo else ""
            conv.other_avatar_full_url = staff.agency.logo.url if staff.agency.logo else ""
        elif other.is_model_user and hasattr(other, "model_profile"):
            conv.other_role_label = "Model"
            conv.other_profile_url = reverse("model-detail", kwargs={"slug": other.model_profile.slug})
            conv.other_avatar_url = other.model_profile.profile_image_thumbnail.url if other.model_profile.profile_image else ""
            conv.other_avatar_full_url = other.model_profile.profile_image.url if other.model_profile.profile_image else ""
        else:
            conv.other_role_label = ""
            conv.other_profile_url = ""
            conv.other_avatar_url = ""
            conv.other_avatar_full_url = ""

    return result


@login_required
def inbox(request):
    user = request.user
    conversations = _get_user_conversations(user)

    # Accepted conversations with last message info (avoids N+1 from last_message property)
    from django.db.models import OuterRef, Subquery
    latest_msg = Message.objects.filter(
        conversation=OuterRef("pk")
    ).order_by("-created_at")
    accepted = (
        conversations
        .filter(status=Conversation.Status.ACCEPTED)
        .annotate(
            last_message_at=Max("messages__created_at"),
            last_message_content=Subquery(latest_msg.values("content")[:1]),
        )
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
    can_send = conversation.status == Conversation.Status.ACCEPTED
    # Pending initiator can send only if they haven't sent any messages yet
    # (happens when conversation was created via search with no initial message)
    if conversation.status == Conversation.Status.PENDING and conversation.initiated_by == request.user:
        can_send = not conversation.messages.exists()

    is_pending_for_me = (
        conversation.status == Conversation.Status.PENDING
        and conversation.initiated_by != request.user
    )

    # Profile URL and role label for other user
    from django.urls import reverse
    from apps.agencies.models import AgencyStaff

    other_profile_url = ""
    other_role_label = ""
    other_avatar_url = ""
    if other_user.is_agency_staff:
        staff = AgencyStaff.objects.filter(user=other_user).select_related("agency").first()
        if staff:
            other_role_label = f"Agency Staff – {staff.agency.name}"
            other_profile_url = reverse("agency-detail", kwargs={"slug": staff.agency.slug})
            other_avatar_url = staff.agency.logo_thumbnail.url if staff.agency.logo else ""
    elif other_user.is_model_user:
        try:
            other_role_label = "Model"
            other_profile_url = reverse("model-detail", kwargs={"slug": other_user.model_profile.slug})
            other_avatar_url = other_user.model_profile.profile_image_thumbnail.url if other_user.model_profile.profile_image else ""
        except ModelProfile.DoesNotExist:
            pass

    return render(request, "messaging/conversation_detail.html", {
        "conversation": conversation,
        "other_user": other_user,
        "messages_list": all_messages,
        "can_send": can_send,
        "is_pending_for_me": is_pending_for_me,
        "other_profile_url": other_profile_url,
        "other_role_label": other_role_label,
        "other_avatar_url": other_avatar_url,
    })


@login_required
@ratelimit(key="user", rate="10/h", method="POST")
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
        if existing.status == Conversation.Status.ACCEPTED:
            return redirect("conversation-detail", pk=existing.pk)
        if existing.status == Conversation.Status.PENDING:
            if request.user.is_agency_staff:
                existing.status = Conversation.Status.ACCEPTED
                existing.save(update_fields=["status", "updated_at"])
            return redirect("conversation-detail", pk=existing.pk)
        # If declined, allow a new request by resetting status
        is_agency = request.user.is_agency_staff
        if existing.status == Conversation.Status.DECLINED:
            existing.status = Conversation.Status.ACCEPTED if is_agency else Conversation.Status.PENDING
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
@ratelimit(key="user", rate="60/h", method="POST")
def send_message(request, pk):
    """Send a message in an existing conversation."""
    if request.method != "POST":
        return redirect("conversation-detail", pk=pk)

    conversation = get_object_or_404(Conversation, pk=pk)
    if not conversation.is_participant(request.user):
        return HttpResponseForbidden()

    # Allow sending in accepted conversations, or first message in pending (from search)
    is_pending_first_message = (
        conversation.status == Conversation.Status.PENDING
        and conversation.initiated_by == request.user
        and not conversation.messages.exists()
    )
    if conversation.status != Conversation.Status.ACCEPTED and not is_pending_first_message:
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

        # Only notify on the first message of a pending conversation (message request)
        # Ongoing accepted chat messages don't create notifications — the red dot
        # on the Messages nav link handles that instead
        if is_pending_first_message:
            other_user = conversation.get_other_participant(request.user)
            Notification.objects.create(
                user=other_user,
                notification_type=Notification.Type.MESSAGE_REQUEST,
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


@login_required
def search_users_for_messaging(request):
    """Search for users to message. Returns JSON."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    user = request.user

    # Get all blocked user IDs (bidirectional)
    block_pairs = MessageBlock.objects.filter(
        Q(blocker=user) | Q(blocked=user)
    ).values_list("blocker", "blocked")
    excluded_ids = {user.pk}
    for blocker_id, blocked_id in block_pairs:
        excluded_ids.add(blocker_id)
        excluded_ids.add(blocked_id)
    excluded_ids.discard(user.pk)
    excluded_ids.add(user.pk)

    results = []

    # Search models by public_display_name
    model_profiles = (
        ModelProfile.objects
        .filter(public_display_name__icontains=q)
        .exclude(user_id__in=excluded_ids)
        .select_related("user")[:10]
    )
    for p in model_profiles:
        conv = _get_or_normalize_conversation(user, p.user)
        results.append({
            "user_id": p.user_id,
            "name": p.public_display_name or p.user.full_name,
            "role_label": "Model",
            "avatar_url": p.profile_image_thumbnail.url if p.profile_image else "",
            "initial": (p.public_display_name or p.user.full_name or "?")[0].upper(),
            "conversation_id": conv.pk if conv else None,
            "status": conv.status if conv else None,
        })

    # Deduplicate by user_id, cap at 10
    seen = set()
    deduped = []
    for r in results:
        if r["user_id"] not in seen:
            seen.add(r["user_id"])
            deduped.append(r)
        if len(deduped) >= 10:
            break

    return JsonResponse({"results": deduped})


@login_required
@ratelimit(key="user", rate="10/h", method="POST")
def start_conversation_with_user(request, user_id):
    """Start a new conversation with any user (from search). POST only."""
    if request.method != "POST":
        return redirect("message-inbox")

    target_user = get_object_or_404(User, pk=user_id, is_active=True)

    if target_user == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect("message-inbox")

    if _is_blocked(request.user, target_user):
        django_messages.error(request, "You cannot message this user.")
        return redirect("message-inbox")

    existing = _get_or_normalize_conversation(request.user, target_user)
    if existing:
        if existing.status == Conversation.Status.BLOCKED:
            django_messages.error(request, "You cannot message this user.")
            return redirect("message-inbox")
        if existing.status == Conversation.Status.ACCEPTED:
            return redirect("conversation-detail", pk=existing.pk)
        if existing.status == Conversation.Status.PENDING:
            if request.user.is_agency_staff:
                existing.status = Conversation.Status.ACCEPTED
                existing.save(update_fields=["status", "updated_at"])
            return redirect("conversation-detail", pk=existing.pk)
        if existing.status == Conversation.Status.DECLINED:
            is_agency = request.user.is_agency_staff
            existing.status = Conversation.Status.ACCEPTED if is_agency else Conversation.Status.PENDING
            existing.initiated_by = request.user
            existing.save(update_fields=["status", "initiated_by", "updated_at"])
            return redirect("conversation-detail", pk=existing.pk)

    is_agency = request.user.is_agency_staff
    conversation = Conversation.objects.create(
        participant_one=request.user,
        participant_two=target_user,
        initiated_by=request.user,
        is_agency_initiated=is_agency,
        status=Conversation.Status.ACCEPTED if is_agency else Conversation.Status.PENDING,
    )

    return redirect("conversation-detail", pk=conversation.pk)
