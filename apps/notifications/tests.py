from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.discovery.models import Follow
from apps.models_app.models import ModelProfile
from apps.notifications.models import Notification
from apps.notifications.context_processors import unread_notification_count

User = get_user_model()


class NotificationTestMixin:
    """Shared setup for notification tests."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            email="alice@test.com", full_name="Alice Model", password="testpass123"
        )
        self.user_b = User.objects.create_user(
            email="bob@test.com", full_name="Bob Model", password="testpass123"
        )
        self.profile_a = ModelProfile.objects.create(
            user=self.user_a, slug="alice-model", is_public=True
        )
        self.profile_b = ModelProfile.objects.create(
            user=self.user_b, slug="bob-model", is_public=True
        )


# ─── Model Tests ───────────────────────────────────────────────────────────


class NotificationModelTest(NotificationTestMixin, TestCase):

    def test_create_follow_notification(self):
        notif = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
            target_profile=self.profile_b,
        )
        self.assertEqual(notif.user, self.user_b)
        self.assertEqual(notif.notification_type, "follow")
        self.assertFalse(notif.is_read)

    def test_display_text_follow(self):
        notif = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
            target_profile=self.profile_b,
        )
        self.assertIn("Alice Model", notif.display_text)
        self.assertIn("following", notif.display_text)

    def test_display_text_message_request(self):
        notif = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.MESSAGE_REQUEST,
            actor=self.user_a,
        )
        self.assertIn("Alice Model", notif.display_text)
        self.assertIn("message", notif.display_text)

    def test_display_text_new_message(self):
        notif = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.NEW_MESSAGE,
            actor=self.user_a,
        )
        self.assertIn("Alice Model", notif.display_text)
        self.assertIn("message", notif.display_text.lower())

    def test_ordering_newest_first(self):
        n1 = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
        )
        n2 = Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.MESSAGE_REQUEST,
            actor=self.user_a,
        )
        notifs = list(Notification.objects.filter(user=self.user_b))
        self.assertEqual(notifs[0].pk, n2.pk)
        self.assertEqual(notifs[1].pk, n1.pk)


# ─── Signal Tests ──────────────────────────────────────────────────────────


class FollowNotificationSignalTest(NotificationTestMixin, TestCase):

    def test_follow_creates_notification(self):
        Follow.objects.create(follower=self.user_a, followed_profile=self.profile_b)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.user_b)
        self.assertEqual(notif.actor, self.user_a)
        self.assertEqual(notif.notification_type, Notification.Type.FOLLOW)
        self.assertEqual(notif.target_profile, self.profile_b)

    def test_follow_notification_goes_to_profile_owner(self):
        Follow.objects.create(follower=self.user_a, followed_profile=self.profile_b)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.user_b)

    def test_unfollow_refollow_creates_new_notification(self):
        f = Follow.objects.create(follower=self.user_a, followed_profile=self.profile_b)
        self.assertEqual(Notification.objects.count(), 1)
        f.delete()
        Follow.objects.create(follower=self.user_a, followed_profile=self.profile_b)
        self.assertEqual(Notification.objects.count(), 2)

    def test_multiple_followers_create_separate_notifications(self):
        user_c = User.objects.create_user(
            email="charlie@test.com", full_name="Charlie Model", password="testpass123"
        )
        Follow.objects.create(follower=self.user_a, followed_profile=self.profile_b)
        Follow.objects.create(follower=user_c, followed_profile=self.profile_b)
        self.assertEqual(Notification.objects.filter(user=self.user_b).count(), 2)


# ─── Context Processor Tests ──────────────────────────────────────────────


class NotificationContextProcessorTest(NotificationTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_authenticated_user_with_unread(self):
        Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
        )
        request = self.factory.get("/")
        request.user = self.user_b
        ctx = unread_notification_count(request)
        self.assertEqual(ctx["unread_notification_count"], 1)

    def test_authenticated_user_no_unread(self):
        request = self.factory.get("/")
        request.user = self.user_b
        ctx = unread_notification_count(request)
        self.assertEqual(ctx["unread_notification_count"], 0)

    def test_read_notifications_not_counted(self):
        Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
            is_read=True,
        )
        request = self.factory.get("/")
        request.user = self.user_b
        ctx = unread_notification_count(request)
        self.assertEqual(ctx["unread_notification_count"], 0)

    def test_anonymous_user_returns_zero(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        ctx = unread_notification_count(request)
        self.assertEqual(ctx["unread_notification_count"], 0)

    def test_count_only_own_notifications(self):
        Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
        )
        Notification.objects.create(
            user=self.user_a,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_b,
        )
        request = self.factory.get("/")
        request.user = self.user_b
        ctx = unread_notification_count(request)
        self.assertEqual(ctx["unread_notification_count"], 1)


# ─── View Tests ────────────────────────────────────────────────────────────


class NotificationListViewTest(NotificationTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_renders_notifications(self):
        self.client.login(email="bob@test.com", password="testpass123")
        Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
            target_profile=self.profile_b,
        )
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Model")

    def test_partial_format_returns_html_fragment(self):
        self.client.login(email="bob@test.com", password="testpass123")
        Notification.objects.create(
            user=self.user_b,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_a,
            target_profile=self.profile_b,
        )
        response = self.client.get(reverse("notification-list"), {"format": "partial"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<!DOCTYPE")
        self.assertContains(response, "Alice Model")

    def test_partial_empty_returns_empty(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.get(reverse("notification-list"), {"format": "partial"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_pagination(self):
        self.client.login(email="bob@test.com", password="testpass123")
        for i in range(25):
            user = User.objects.create_user(
                email=f"user{i}@test.com", full_name=f"User {i}", password="testpass123"
            )
            Notification.objects.create(
                user=self.user_b,
                notification_type=Notification.Type.FOLLOW,
                actor=user,
            )
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 1 of 2")


class MarkNotificationsReadViewTest(NotificationTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.post(reverse("mark-notifications-read"))
        self.assertEqual(response.status_code, 302)

    def test_marks_all_unread_as_read(self):
        self.client.login(email="bob@test.com", password="testpass123")
        for _ in range(3):
            Notification.objects.create(
                user=self.user_b,
                notification_type=Notification.Type.FOLLOW,
                actor=self.user_a,
            )
        self.assertEqual(Notification.objects.filter(user=self.user_b, is_read=False).count(), 3)
        response = self.client.post(reverse("mark-notifications-read"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user_b, is_read=False).count(), 0)

    def test_does_not_mark_other_users_notifications(self):
        self.client.login(email="bob@test.com", password="testpass123")
        Notification.objects.create(
            user=self.user_a,
            notification_type=Notification.Type.FOLLOW,
            actor=self.user_b,
        )
        self.client.post(reverse("mark-notifications-read"))
        self.assertEqual(Notification.objects.filter(user=self.user_a, is_read=False).count(), 1)

    def test_get_not_allowed(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.get(reverse("mark-notifications-read"))
        self.assertEqual(response.status_code, 405)

    def test_returns_json(self):
        self.client.login(email="bob@test.com", password="testpass123")
        response = self.client.post(reverse("mark-notifications-read"))
        self.assertEqual(response["Content-Type"], "application/json")
