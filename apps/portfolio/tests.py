import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from apps.models_app.models import ModelProfile
from apps.portfolio.models import PortfolioPost

User = get_user_model()


class PortfolioTestMixin:
    """Shared setup for portfolio tests."""

    def setUp(self):
        self.client = Client()

        # Model user who owns a portfolio post
        self.owner = User.objects.create_user(
            email="owner@test.com",
            full_name="Owner Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.owner.onboarding_completed = True
        self.owner.save(update_fields=["onboarding_completed"])
        self.owner_profile = ModelProfile.objects.create(
            user=self.owner, slug="owner-model", is_public=True
        )

        # Another model user (not the owner)
        self.other = User.objects.create_user(
            email="other@test.com",
            full_name="Other Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.other.onboarding_completed = True
        self.other.save(update_fields=["onboarding_completed"])
        self.other_profile = ModelProfile.objects.create(
            user=self.other, slug="other-model", is_public=True
        )

        # Non-model user (agency staff)
        self.agency_user = User.objects.create_user(
            email="agency@test.com",
            full_name="Agency Staff",
            password="testpass123",
            role=User.Role.AGENCY_STAFF,
        )

        # Public portfolio post
        self.public_post = PortfolioPost.objects.create(
            owner_profile=self.owner_profile,
            title="Public Post",
            slug="public-post",
            is_public=True,
        )

        # Private portfolio post
        self.private_post = PortfolioPost.objects.create(
            owner_profile=self.owner_profile,
            title="Private Post",
            slug="private-post",
            is_public=False,
        )


class PortfolioDetailTests(PortfolioTestMixin, TestCase):
    """Tests for the portfolio_detail view."""

    def test_public_post_accessible_by_anonymous(self):
        url = reverse("portfolio-detail", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_post.title)

    def test_public_post_accessible_by_other_user(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("portfolio-detail", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_private_post_404_for_anonymous(self):
        url = reverse("portfolio-detail", kwargs={"slug": self.private_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_private_post_accessible_by_owner(self):
        self.client.login(email="owner@test.com", password="testpass123")
        url = reverse("portfolio-detail", kwargs={"slug": self.private_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.private_post.title)

    def test_private_post_404_for_other_user(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("portfolio-detail", kwargs={"slug": self.private_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_post_404(self):
        url = reverse("portfolio-detail", kwargs={"slug": "does-not-exist"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class PortfolioCreateTests(PortfolioTestMixin, TestCase):
    """Tests for the portfolio_create view."""

    def test_login_required(self):
        url = reverse("portfolio-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_non_model_user_redirected(self):
        self.client.login(email="agency@test.com", password="testpass123")
        url = reverse("portfolio-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_get_renders_form(self):
        self.client.login(email="owner@test.com", password="testpass123")
        url = reverse("portfolio-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIn("formset", response.context)
        self.assertEqual(response.context["action"], "Create")

    def test_model_without_profile_redirected_to_onboarding(self):
        """A model user who has no ModelProfile gets redirected to onboarding."""
        no_profile_user = User.objects.create_user(
            email="noprofile@test.com",
            full_name="No Profile",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.client.login(email="noprofile@test.com", password="testpass123")
        url = reverse("portfolio-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("onboarding", response.url)


class PortfolioEditTests(PortfolioTestMixin, TestCase):
    """Tests for the portfolio_edit view."""

    def test_login_required(self):
        url = reverse("portfolio-edit", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_owner_can_edit_own_post(self):
        self.client.login(email="owner@test.com", password="testpass123")
        url = reverse("portfolio-edit", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["action"], "Edit")

    def test_other_user_cannot_edit_post_404(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("portfolio-edit", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_non_model_user_redirected(self):
        self.client.login(email="agency@test.com", password="testpass123")
        url = reverse("portfolio-edit", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class PortfolioDeleteTests(PortfolioTestMixin, TestCase):
    """Tests for the portfolio_delete view."""

    def test_login_required(self):
        url = reverse("portfolio-delete", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_owner_can_view_delete_confirmation(self):
        self.client.login(email="owner@test.com", password="testpass123")
        url = reverse("portfolio-delete", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_owner_can_delete_own_post(self):
        self.client.login(email="owner@test.com", password="testpass123")
        url = reverse("portfolio-delete", kwargs={"slug": self.public_post.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PortfolioPost.objects.filter(pk=self.public_post.pk).exists())

    def test_other_user_cannot_delete_post_404(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("portfolio-delete", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # Confirm the post still exists
        self.assertTrue(PortfolioPost.objects.filter(pk=self.public_post.pk).exists())

    def test_non_model_user_redirected(self):
        self.client.login(email="agency@test.com", password="testpass123")
        url = reverse("portfolio-delete", kwargs={"slug": self.public_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class PortfolioPostModelTests(TestCase):
    """Tests for the PortfolioPost model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="model@test.com",
            full_name="Test Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.profile = ModelProfile.objects.create(
            user=self.user, slug="test-model", is_public=True
        )

    def test_slug_auto_generated_from_title(self):
        post = PortfolioPost.objects.create(
            owner_profile=self.profile, title="My Great Shoot"
        )
        self.assertEqual(post.slug, "my-great-shoot")

    def test_explicit_slug_preserved(self):
        post = PortfolioPost.objects.create(
            owner_profile=self.profile, title="Some Title", slug="custom-slug"
        )
        self.assertEqual(post.slug, "custom-slug")

    def test_str_representation(self):
        post = PortfolioPost.objects.create(
            owner_profile=self.profile, title="Editorial Look"
        )
        self.assertIn("Editorial Look", str(post))

    def test_default_is_public_true(self):
        post = PortfolioPost.objects.create(
            owner_profile=self.profile, title="Default Visibility"
        )
        self.assertTrue(post.is_public)
