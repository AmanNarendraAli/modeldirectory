from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.agencies.models import Agency, AgencyRequest, AgencyStaff

User = get_user_model()


class AgencyListViewTests(TestCase):
    """Tests for the agency_list view."""

    def setUp(self):
        self.client = Client()
        # Create a mix of active/inactive agencies
        for i in range(1, 13):
            Agency.objects.create(
                name=f"Agency {i}",
                slug=f"agency-{i}",
                is_active=True,
                city="Mumbai" if i % 2 == 0 else "Delhi",
                is_accepting_applications=(i <= 6),
                verification_status="verified" if i <= 4 else "unverified",
            )
        Agency.objects.create(
            name="Inactive Agency",
            slug="inactive-agency",
            is_active=False,
        )

    def test_agency_list_renders(self):
        response = self.client.get(reverse("agency-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "agencies/agency_list.html")

    def test_agency_list_excludes_inactive(self):
        response = self.client.get(reverse("agency-list"))
        agencies = response.context["agencies"]
        slugs = [a.slug for a in agencies]
        self.assertNotIn("inactive-agency", slugs)
        self.assertEqual(len(agencies), 12)

    def test_agency_list_search_filter(self):
        response = self.client.get(reverse("agency-list"), {"q": "Agency 1"})
        agencies = response.context["agencies"]
        # Matches "Agency 1", "Agency 10", "Agency 11", "Agency 12"
        for a in agencies:
            self.assertIn("Agency 1", a.name)

    def test_agency_list_city_filter(self):
        response = self.client.get(reverse("agency-list"), {"city": ["Mumbai"]})
        agencies = response.context["agencies"]
        for a in agencies:
            self.assertEqual(a.city, "Mumbai")

    def test_agency_list_accepting_filter(self):
        response = self.client.get(reverse("agency-list"), {"accepting": "1"})
        agencies = response.context["agencies"]
        for a in agencies:
            self.assertTrue(a.is_accepting_applications)

    def test_agency_list_verified_filter(self):
        response = self.client.get(reverse("agency-list"), {"verified": "1"})
        agencies = response.context["agencies"]
        for a in agencies:
            self.assertEqual(a.verification_status, "verified")

    def test_agency_list_cities_in_context(self):
        response = self.client.get(reverse("agency-list"))
        cities = response.context["cities"]
        self.assertIn("Mumbai", cities)
        self.assertIn("Delhi", cities)


class AgencyDetailViewTests(TestCase):
    """Tests for the agency_detail view."""

    def setUp(self):
        self.client = Client()
        self.agency = Agency.objects.create(
            name="Detail Agency",
            slug="detail-agency",
            is_active=True,
            is_roster_public=False,
        )
        # Create a model user with profile on the agency roster
        self.model_user = User.objects.create_user(
            email="model@test.com", full_name="Model User", password="testpass123", role=User.Role.MODEL
        )
        from apps.models_app.models import ModelProfile
        self.model_profile = ModelProfile.objects.create(
            user=self.model_user,
            public_display_name="Test Model",
            represented_by_agency=self.agency,
            is_public=True,
        )

        # Agency staff user
        self.staff_user = User.objects.create_user(
            email="staff@test.com", full_name="Staff User", password="testpass123", role=User.Role.AGENCY_STAFF
        )
        AgencyStaff.objects.create(
            user=self.staff_user, agency=self.agency, can_review_applications=True
        )

    def test_agency_detail_renders(self):
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "detail-agency"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "agencies/agency_detail.html")
        self.assertEqual(response.context["agency"], self.agency)

    def test_agency_detail_inactive_404(self):
        inactive = Agency.objects.create(name="Dead", slug="dead", is_active=False)
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "dead"}))
        self.assertEqual(response.status_code, 404)

    def test_agency_detail_nonexistent_404(self):
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "nonexistent"}))
        self.assertEqual(response.status_code, 404)

    def test_roster_private_for_anonymous(self):
        """When roster is private, anonymous users see no roster."""
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "detail-agency"}))
        self.assertTrue(response.context["roster_is_private"])
        self.assertIsNone(response.context["roster_models"])

    def test_roster_visible_for_staff(self):
        """Agency staff always sees the full roster."""
        self.client.login(email="staff@test.com", password="testpass123")
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "detail-agency"}))
        self.assertFalse(response.context["roster_is_private"])
        self.assertIn(self.model_profile, response.context["roster_models"])

    def test_roster_public_shows_public_models(self):
        """When roster is public, all public models are visible."""
        self.agency.is_roster_public = True
        self.agency.save()
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "detail-agency"}))
        self.assertFalse(response.context["roster_is_private"])
        self.assertIn(self.model_profile, response.context["roster_models"])

    def test_roster_public_hides_non_public_models(self):
        """Non-public models hidden from public roster view."""
        self.agency.is_roster_public = True
        self.agency.save()
        self.model_profile.is_public = False
        self.model_profile.save()
        response = self.client.get(reverse("agency-detail", kwargs={"slug": "detail-agency"}))
        self.assertNotIn(self.model_profile, list(response.context["roster_models"]))


class AgencyRequestViewTests(TestCase):
    """Tests for the agency_request view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("agency-request")
        self.valid_data = {
            "agency_name": "New Agency",
            "agency_city": "Bangalore",
            "agency_website": "https://example.com",
            "contact_name": "John Doe",
            "contact_email": "john@example.com",
            "role_at_agency": "Owner",
        }

    def test_get_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "agencies/agency_request.html")
        self.assertIn("form", response.context)

    def test_post_creates_request(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertRedirects(response, reverse("agency-list"))
        self.assertTrue(AgencyRequest.objects.filter(agency_name="New Agency").exists())

    def test_post_invalid_data_does_not_create(self):
        response = self.client.post(self.url, {"agency_name": ""})
        self.assertEqual(response.status_code, 200)  # re-renders form
        self.assertEqual(AgencyRequest.objects.count(), 0)

    def test_post_authenticated_sets_submitted_by(self):
        user = User.objects.create_user(
            email="requester@test.com", full_name="Requester", password="testpass123"
        )
        self.client.login(email="requester@test.com", password="testpass123")
        self.client.post(self.url, self.valid_data)
        req = AgencyRequest.objects.get(agency_name="New Agency")
        self.assertEqual(req.submitted_by, user)

    def test_post_anonymous_submitted_by_is_null(self):
        self.client.post(self.url, self.valid_data)
        req = AgencyRequest.objects.get(agency_name="New Agency")
        self.assertIsNone(req.submitted_by)
