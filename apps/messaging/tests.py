from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.models_app.models import ModelProfile
from apps.notifications.models import Notification
from .models import Conversation, Message, MessageBlock

User = get_user_model()


class MessagingTestMixin:
    """Shared setup for messaging tests."""

    def setUp(self):
        self.model_a = User.objects.create_user(
            email="alice@test.com", full_name="Alice Model", password="testpass123",
            role=User.Role.MODEL,
        )
        self.model_b = User.objects.create_user(
            email="bob@test.com", full_name="Bob Model", password="testpass123",
            role=User.Role.MODEL,
        )
        self.agency_user = User.objects.create_user(
            email="agency@test.com", full_name="Agency Staff", password="testpass123",
            role=User.Role.AGENCY_STAFF,
        )
        self.profile_a = ModelProfile.objects.create(
            user=self.model_a, slug="alice-model", is_public=True
        )
        self.profile_b = ModelProfile.objects.create(
            user=self.model_b, slug="bob-model", is_public=True
        )


# ─── Model Tests ───────────────────────────────────────────────────────────


class ConversationModelTest(MessagingTestMixin, TestCase):

    def test_create_conversation(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        self.assertEqual(conv.status, Conversation.Status.PENDING)
        self.assertFalse(conv.is_agency_initiated)

    def test_get_other_participant(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        self.assertEqual(conv.get_other_participant(self.model_a), self.model_b)
        self.assertEqual(conv.get_other_participant(self.model_b), self.model_a)

    def test_is_participant(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        self.assertTrue(conv.is_participant(self.model_a))
        self.assertTrue(conv.is_participant(self.model_b))
        self.assertFalse(conv.is_participant(self.agency_user))

    def test_last_message_property(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        self.assertIsNone(conv.last_message)
        Message.objects.create(conversation=conv, sender=self.model_a, content="Hello")
        msg2 = Message.objects.create(conversation=conv, sender=self.model_b, content="Hi back")
        self.assertEqual(conv.last_message, msg2)

    def test_unique_constraint_prevents_duplicates(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Conversation.objects.create(
                participant_one=self.model_a,
                participant_two=self.model_b,
                initiated_by=self.model_a,
            )

    def test_ordering_by_updated_at_desc(self):
        conv1 = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
        )
        user_c = User.objects.create_user(
            email="charlie@test.com", full_name="Charlie", password="testpass123"
        )
        conv2 = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=user_c,
            initiated_by=self.model_a,
        )
        convs = list(Conversation.objects.all())
        self.assertEqual(convs[0].pk, conv2.pk)


class MessageModelTest(MessagingTestMixin, TestCase):

    def test_create_message(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )
        msg = Message.objects.create(conversation=conv, sender=self.model_a, content="Hello!")
        self.assertEqual(msg.content, "Hello!")
        self.assertFalse(msg.is_read)

    def test_message_ordering_chronological(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )
        msg1 = Message.objects.create(conversation=conv, sender=self.model_a, content="First")
        msg2 = Message.objects.create(conversation=conv, sender=self.model_b, content="Second")
        msgs = list(conv.messages.all())
        self.assertEqual(msgs[0].pk, msg1.pk)
        self.assertEqual(msgs[1].pk, msg2.pk)


class MessageBlockModelTest(MessagingTestMixin, TestCase):

    def test_create_block(self):
        block = MessageBlock.objects.create(blocker=self.model_a, blocked=self.model_b)
        self.assertEqual(block.blocker, self.model_a)
        self.assertEqual(block.blocked, self.model_b)

    def test_unique_block(self):
        MessageBlock.objects.create(blocker=self.model_a, blocked=self.model_b)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            MessageBlock.objects.create(blocker=self.model_a, blocked=self.model_b)


# ─── Start Conversation View Tests ─────────────────────────────────────────


class StartConversationTest(MessagingTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.post(reverse("start-conversation", kwargs={"slug": "bob-model"}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_redirects_to_profile(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("start-conversation", kwargs={"slug": "bob-model"}))
        self.assertEqual(response.status_code, 302)

    def test_start_new_conversation(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Hey Bob!"},
        )
        self.assertEqual(response.status_code, 302)
        conv = Conversation.objects.first()
        self.assertIsNotNone(conv)
        self.assertEqual(conv.status, Conversation.Status.PENDING)
        self.assertEqual(conv.initiated_by, self.model_a)
        self.assertEqual(conv.messages.count(), 1)
        self.assertEqual(conv.messages.first().content, "Hey Bob!")

    def test_creates_message_request_notification(self):
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Hey Bob!"},
        )
        notif = Notification.objects.filter(
            user=self.model_b, notification_type=Notification.Type.MESSAGE_REQUEST
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.actor, self.model_a)

    def test_cannot_message_self(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "alice-model"}),
            {"message": "Talking to myself"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_cannot_message_blocked_user(self):
        MessageBlock.objects.create(blocker=self.model_b, blocked=self.model_a)
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Hey!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_redirects_to_existing_accepted_conversation(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Hey again!"},
        )
        self.assertRedirects(response, reverse("conversation-detail", kwargs={"pk": conv.pk}))
        self.assertEqual(Message.objects.count(), 0)

    def test_redirects_to_existing_pending_conversation(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Still waiting!"},
        )
        self.assertRedirects(response, reverse("conversation-detail", kwargs={"pk": conv.pk}))

    def test_declined_conversation_can_be_rerequested(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.DECLINED,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Please reconsider!"},
        )
        conv.refresh_from_db()
        self.assertEqual(conv.status, Conversation.Status.PENDING)
        self.assertEqual(Message.objects.count(), 1)

    def test_blocked_conversation_cannot_be_rerequested(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.BLOCKED,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Please!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Message.objects.count(), 0)

    def test_agency_conversation_auto_accepted(self):
        self.client.login(email="agency@test.com", password="testpass123")
        response = self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "We'd like to work with you!"},
        )
        conv = Conversation.objects.first()
        self.assertIsNotNone(conv)
        self.assertEqual(conv.status, Conversation.Status.ACCEPTED)
        self.assertTrue(conv.is_agency_initiated)

    def test_agency_conversation_creates_new_message_notification(self):
        self.client.login(email="agency@test.com", password="testpass123")
        self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Interested in you!"},
        )
        notif = Notification.objects.filter(user=self.model_b).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.Type.NEW_MESSAGE)


# ─── Inbox View Tests ──────────────────────────────────────────────────────


class InboxViewTest(MessagingTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.get(reverse("message-inbox"))
        self.assertEqual(response.status_code, 302)

    def test_empty_inbox(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No conversations yet")

    def test_shows_accepted_conversations(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )
        Message.objects.create(conversation=conv, sender=self.model_a, content="Hey!")
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob Model")

    def test_requests_tab_shows_pending_received(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"), {"tab": "requests"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Model")
        self.assertContains(response, "New request")

    def test_requests_tab_does_not_show_sent_requests(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"), {"tab": "requests"})
        self.assertContains(response, "No message requests")

    def test_messages_tab_shows_waiting_for_response(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"), {"tab": "messages"})
        self.assertContains(response, "Waiting for response")
        self.assertContains(response, "Request pending")

    def test_declined_conversations_not_shown(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.DECLINED,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("message-inbox"))
        self.assertNotContains(response, "Bob Model")


# ─── Conversation Detail View Tests ────────────────────────────────────────


class ConversationDetailTest(MessagingTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )

    def test_login_required(self):
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 302)

    def test_non_participant_forbidden(self):
        self.client.login(email="agency@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 403)

    def test_shows_messages(self):
        Message.objects.create(conversation=self.conv, sender=self.model_a, content="Hello!")
        Message.objects.create(conversation=self.conv, sender=self.model_b, content="Hi there!")
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello!")
        self.assertContains(response, "Hi there!")

    def test_marks_other_users_messages_as_read(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.model_b, content="Read me!", is_read=False
        )
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_does_not_mark_own_messages_as_read(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.model_a, content="My message", is_read=False
        )
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        msg.refresh_from_db()
        self.assertFalse(msg.is_read)

    def test_accepted_conversation_shows_send_form(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertContains(response, 'name="message"')
        self.assertContains(response, "Send")

    def test_pending_conversation_hides_send_form_for_initiator(self):
        self.conv.status = Conversation.Status.PENDING
        self.conv.save()
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertContains(response, "Waiting for")

    def test_pending_conversation_shows_accept_decline_for_recipient(self):
        self.conv.status = Conversation.Status.PENDING
        self.conv.save()
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertContains(response, "Accept")
        self.assertContains(response, "Decline")
        self.assertContains(response, "Block")

    def test_blocked_conversation_shows_blocked_message(self):
        self.conv.status = Conversation.Status.BLOCKED
        self.conv.save()
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("conversation-detail", kwargs={"pk": self.conv.pk}))
        self.assertContains(response, "blocked")


# ─── Send Message View Tests ──────────────────────────────────────────────


class SendMessageTest(MessagingTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )

    def test_login_required(self):
        response = self.client.post(reverse("send-message", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 302)

    def test_send_message_in_accepted_conversation(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "How are you?"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.conv.messages.count(), 1)
        self.assertEqual(self.conv.messages.first().content, "How are you?")

    def test_send_message_creates_notification(self):
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "Notification test"},
        )
        notif = Notification.objects.filter(
            user=self.model_b, notification_type=Notification.Type.NEW_MESSAGE
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.actor, self.model_a)

    def test_cannot_send_in_pending_conversation(self):
        self.conv.status = Conversation.Status.PENDING
        self.conv.save()
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "Sneaky message"},
        )
        self.assertEqual(self.conv.messages.count(), 0)

    def test_cannot_send_in_blocked_conversation(self):
        self.conv.status = Conversation.Status.BLOCKED
        self.conv.save()
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "Blocked message"},
        )
        self.assertEqual(self.conv.messages.count(), 0)

    def test_non_participant_forbidden(self):
        self.client.login(email="agency@test.com", password="testpass123")
        response = self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "Intruder!"},
        )
        self.assertEqual(response.status_code, 403)

    def test_empty_message_not_saved(self):
        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("send-message", kwargs={"pk": self.conv.pk}),
            {"message": "   "},
        )
        self.assertEqual(self.conv.messages.count(), 0)


# ─── Accept / Decline / Block View Tests ───────────────────────────────────


class AcceptRequestTest(MessagingTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )

    def test_accept_changes_status(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.post(reverse("accept-request", kwargs={"pk": self.conv.pk}))
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.ACCEPTED)
        self.assertEqual(response.status_code, 302)

    def test_initiator_cannot_accept(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(reverse("accept-request", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 403)
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.PENDING)

    def test_cannot_accept_non_pending(self):
        self.conv.status = Conversation.Status.ACCEPTED
        self.conv.save()
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("accept-request", kwargs={"pk": self.conv.pk}))
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.ACCEPTED)

    def test_non_participant_forbidden(self):
        self.client.login(email="agency@test.com", password="testpass123")
        response = self.client.post(reverse("accept-request", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 403)


class DeclineRequestTest(MessagingTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )

    def test_decline_changes_status(self):
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("decline-request", kwargs={"pk": self.conv.pk}))
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.DECLINED)

    def test_decline_redirects_to_inbox(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.post(reverse("decline-request", kwargs={"pk": self.conv.pk}))
        self.assertRedirects(response, reverse("message-inbox"))

    def test_initiator_cannot_decline(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.post(reverse("decline-request", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 403)
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.PENDING)


class BlockUserTest(MessagingTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )

    def test_block_changes_status(self):
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.BLOCKED)

    def test_block_creates_message_block(self):
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))
        self.assertTrue(
            MessageBlock.objects.filter(blocker=self.model_b, blocked=self.model_a).exists()
        )

    def test_block_redirects_to_inbox(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))
        self.assertRedirects(response, reverse("message-inbox"))

    def test_non_participant_forbidden(self):
        self.client.login(email="agency@test.com", password="testpass123")
        response = self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))
        self.assertEqual(response.status_code, 403)

    def test_block_from_accepted_conversation(self):
        self.conv.status = Conversation.Status.ACCEPTED
        self.conv.save()
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, Conversation.Status.BLOCKED)
        self.assertTrue(
            MessageBlock.objects.filter(blocker=self.model_b, blocked=self.model_a).exists()
        )

    def test_blocked_user_cannot_start_new_conversation(self):
        self.client.login(email="bob@test.com", password="testpass123")
        self.client.post(reverse("block-user", kwargs={"pk": self.conv.pk}))

        self.client.login(email="alice@test.com", password="testpass123")
        self.client.post(
            reverse("start-conversation", kwargs={"slug": "bob-model"}),
            {"message": "Please unblock me"},
        )
        self.assertEqual(Message.objects.count(), 0)


# ─── Model Detail Message Button Tests ─────────────────────────────────────


class ModelDetailMessageButtonTest(MessagingTestMixin, TestCase):

    def test_message_button_visible_for_other_model(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("model-detail", kwargs={"slug": "bob-model"}))
        self.assertContains(response, "Message")

    def test_message_button_hidden_for_own_profile(self):
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("model-detail", kwargs={"slug": "alice-model"}))
        self.assertNotContains(response, "message-modal")

    def test_message_button_hidden_for_anonymous(self):
        response = self.client.get(reverse("model-detail", kwargs={"slug": "bob-model"}))
        self.assertNotContains(response, "message-modal")

    def test_message_button_hidden_when_blocked(self):
        MessageBlock.objects.create(blocker=self.model_b, blocked=self.model_a)
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("model-detail", kwargs={"slug": "bob-model"}))
        self.assertNotContains(response, "message-modal")

    def test_shows_existing_conversation_link(self):
        conv = Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.ACCEPTED,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("model-detail", kwargs={"slug": "bob-model"}))
        expected_url = reverse("conversation-detail", kwargs={"pk": conv.pk})
        self.assertContains(response, expected_url)

    def test_shows_request_pending_for_pending_conversation(self):
        Conversation.objects.create(
            participant_one=self.model_a,
            participant_two=self.model_b,
            initiated_by=self.model_a,
            status=Conversation.Status.PENDING,
        )
        self.client.login(email="alice@test.com", password="testpass123")
        response = self.client.get(reverse("model-detail", kwargs={"slug": "bob-model"}))
        self.assertContains(response, "Request Pending")
