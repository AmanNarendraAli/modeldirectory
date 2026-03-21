from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.agencies.models import Agency, AgencyBan
from apps.applications.models import Application, ApplicationSnapshot
from apps.models_app.models import ModelProfile

User = get_user_model()


class ApplicationTestMixin:
    """Shared setup for application tests."""

    def setUp(self):
        # Model user (onboarding complete)
        self.model_user = User.objects.create_user(
            email="model@test.com",
            full_name="Test Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.model_user.onboarding_completed = True
        self.model_user.save(update_fields=["onboarding_completed"])

        self.profile = ModelProfile.objects.create(
            user=self.model_user, slug="test-model", is_public=True
        )

        # Agency staff user (non-model)
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            full_name="Staff User",
            password="testpass123",
            role=User.Role.AGENCY_STAFF,
        )

        # Active agency accepting applications
        self.agency = Agency.objects.create(
            name="Test Agency",
            slug="test-agency",
            is_active=True,
            is_accepting_applications=True,
        )

        self.apply_url = reverse("apply", kwargs={"agency_slug": self.agency.slug})
        self.success_url = reverse("apply-success", kwargs={"agency_slug": self.agency.slug})


# --- Apply View Tests -------------------------------------------------------


class ApplyViewLoginRequiredTest(ApplicationTestMixin, TestCase):

    def test_get_redirects_to_login(self):
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_post_redirects_to_login(self):
        response = self.client.post(self.apply_url, {"cover_note": "Hello"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class ApplyViewNonModelBlockedTest(ApplicationTestMixin, TestCase):

    def test_agency_staff_cannot_apply(self):
        self.client.login(email="staff@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("agency-detail", kwargs={"slug": self.agency.slug})
        )
        self.assertEqual(Application.objects.count(), 0)


class ApplyViewAgencyNotAcceptingTest(ApplicationTestMixin, TestCase):

    def test_closed_agency_blocks_application(self):
        self.agency.is_accepting_applications = False
        self.agency.save(update_fields=["is_accepting_applications"])

        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("agency-detail", kwargs={"slug": self.agency.slug})
        )


class ApplyViewOnboardingIncompleteTest(ApplicationTestMixin, TestCase):

    def test_incomplete_onboarding_redirects(self):
        self.model_user.onboarding_completed = False
        self.model_user.save(update_fields=["onboarding_completed"])

        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("onboarding"))


class ApplyViewDuplicateBlockedTest(ApplicationTestMixin, TestCase):

    def test_existing_application_blocks_duplicate(self):
        Application.objects.create(
            applicant_profile=self.profile,
            agency=self.agency,
            status=Application.Status.SUBMITTED,
        )
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("agency-detail", kwargs={"slug": self.agency.slug})
        )

    def test_withdrawn_application_allows_reapply(self):
        Application.objects.create(
            applicant_profile=self.profile,
            agency=self.agency,
            status=Application.Status.WITHDRAWN,
        )
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 200)


class ApplyViewBannedModelTest(ApplicationTestMixin, TestCase):

    def test_banned_model_cannot_apply(self):
        AgencyBan.objects.create(model_profile=self.profile, agency=self.agency)
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("agency-detail", kwargs={"slug": self.agency.slug})
        )
        self.assertEqual(Application.objects.count(), 0)


class ApplyViewGetRendersFormTest(ApplicationTestMixin, TestCase):

    def test_get_renders_form(self):
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cover_note")
        self.assertEqual(response.context["agency"], self.agency)
        self.assertEqual(response.context["profile"], self.profile)


class ApplyViewSuccessfulSubmissionTest(ApplicationTestMixin, TestCase):

    def test_post_creates_application_and_snapshot(self):
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.post(self.apply_url, {"cover_note": "I love modeling"})
        self.assertRedirects(response, self.success_url)

        # Application created
        self.assertEqual(Application.objects.count(), 1)
        app = Application.objects.first()
        self.assertEqual(app.applicant_profile, self.profile)
        self.assertEqual(app.agency, self.agency)
        self.assertEqual(app.status, Application.Status.SUBMITTED)
        self.assertEqual(app.cover_note, "I love modeling")
        self.assertIsNotNone(app.submitted_at)

        # Snapshot created
        self.assertEqual(ApplicationSnapshot.objects.count(), 1)
        snap = ApplicationSnapshot.objects.first()
        self.assertEqual(snap.application, app)
        self.assertEqual(snap.applicant_name, self.profile.public_display_name or self.model_user.full_name)

    def test_post_with_empty_cover_note(self):
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.post(self.apply_url, {"cover_note": ""})
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Application.objects.count(), 1)

    def test_snapshot_captures_profile_data(self):
        self.profile.gender = "female"
        self.profile.city = "Mumbai"
        self.profile.height_cm = 175
        self.profile.bust_cm = 84
        self.profile.waist_cm = 60
        self.profile.hips_cm = 89
        self.profile.bio = "Experienced model"
        self.profile.save()

        self.client.login(email="model@test.com", password="testpass123")
        self.client.post(self.apply_url, {"cover_note": "Hi"})

        snap = ApplicationSnapshot.objects.first()
        self.assertEqual(snap.gender, "female")
        self.assertEqual(snap.city, "Mumbai")
        self.assertEqual(snap.height_cm, 175)
        self.assertEqual(snap.bust_cm, 84)
        self.assertEqual(snap.waist_cm, 60)
        self.assertEqual(snap.hips_cm, 89)
        self.assertEqual(snap.portfolio_summary, "Experienced model")


# --- Apply Success View Tests ------------------------------------------------


class ApplySuccessViewTest(ApplicationTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.get(self.success_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_renders_correctly(self):
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.success_url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_agency(self):
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(self.success_url)
        self.assertEqual(response.context["agency"], self.agency)

    def test_nonexistent_agency_slug_returns_404(self):
        self.client.login(email="model@test.com", password="testpass123")
        url = reverse("apply-success", kwargs={"agency_slug": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
