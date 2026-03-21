from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.agencies.models import Agency
from apps.discovery.models import Follow, SavedAgency
from apps.models_app.models import ModelProfile

User = get_user_model()


class DiscoveryTestMixin:
    """Shared setup for discovery tests."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            email="alice@test.com",
            full_name="Alice Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.user_b = User.objects.create_user(
            email="bob@test.com",
            full_name="Bob Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.profile_a = ModelProfile.objects.create(
            user=self.user_a, slug="alice-model", is_public=True
        )
        self.profile_b = ModelProfile.objects.create(
            user=self.user_b, slug="bob-model", is_public=True
        )
        self.agency = Agency.objects.create(
            name="Test Agency",
            slug="test-agency",
            is_active=True,
            is_accepting_applications=True,
        )


# --- Follow Model Tests ------------------------------------------------------


class FollowModelLoginRequiredTest(DiscoveryTestMixin, TestCase):

    def test_post_redirects_to_login(self):
        url = reverse("follow-model", kwargs={"slug": self.profile_b.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_redirects_to_login(self):
        url = reverse("follow-model", kwargs={"slug": self.profile_b.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class FollowModelCreateTest(DiscoveryTestMixin, TestCase):

    def test_follow_creates_record(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("follow-model", kwargs={"slug": self.profile_b.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user_a, followed_profile=self.profile_b
            ).exists()
        )


class FollowModelToggleTest(DiscoveryTestMixin, TestCase):

    def test_second_post_unfollows(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("follow-model", kwargs={"slug": self.profile_b.slug})

        # First POST: follow
        self.client.post(url)
        self.assertEqual(Follow.objects.count(), 1)

        # Second POST: unfollow
        self.client.post(url)
        self.assertEqual(Follow.objects.count(), 0)


class FollowModelSelfTest(DiscoveryTestMixin, TestCase):

    def test_cannot_follow_own_profile(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("follow-model", kwargs={"slug": self.profile_a.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Follow.objects.count(), 0)


class FollowModelNonPostTest(DiscoveryTestMixin, TestCase):

    def test_get_redirects_without_creating(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("follow-model", kwargs={"slug": self.profile_b.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("model-detail", kwargs={"slug": self.profile_b.slug})
        )
        self.assertEqual(Follow.objects.count(), 0)


# --- Save Agency Tests --------------------------------------------------------


class SaveAgencyLoginRequiredTest(DiscoveryTestMixin, TestCase):

    def test_post_redirects_to_login(self):
        url = reverse("save-agency", kwargs={"slug": self.agency.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_redirects_to_login(self):
        url = reverse("save-agency", kwargs={"slug": self.agency.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class SaveAgencyCreateTest(DiscoveryTestMixin, TestCase):

    def test_save_creates_record(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("save-agency", kwargs={"slug": self.agency.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SavedAgency.objects.filter(
                user=self.user_a, agency=self.agency
            ).exists()
        )


class SaveAgencyToggleTest(DiscoveryTestMixin, TestCase):

    def test_second_post_unsaves(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("save-agency", kwargs={"slug": self.agency.slug})

        # First POST: save
        self.client.post(url)
        self.assertEqual(SavedAgency.objects.count(), 1)

        # Second POST: unsave
        self.client.post(url)
        self.assertEqual(SavedAgency.objects.count(), 0)


class SaveAgencyNonPostTest(DiscoveryTestMixin, TestCase):

    def test_get_redirects_without_saving(self):
        self.client.login(email="alice@test.com", password="testpass123")
        url = reverse("save-agency", kwargs={"slug": self.agency.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("agency-detail", kwargs={"slug": self.agency.slug})
        )
        self.assertEqual(SavedAgency.objects.count(), 0)
