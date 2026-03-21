from django.test import TestCase, Client
from django.urls import reverse

from apps.agencies.models import Agency


class LandingPageTests(TestCase):
    """Tests for the home/landing page."""

    def setUp(self):
        self.client = Client()
        # Create featured and non-featured agencies
        Agency.objects.create(
            name="Featured Agency", slug="featured", is_active=True,
            is_featured=True, featured_order=1,
        )
        Agency.objects.create(
            name="Regular Agency", slug="regular", is_active=True,
            is_featured=False,
        )
        Agency.objects.create(
            name="Inactive Featured", slug="inactive-featured", is_active=False,
            is_featured=True,
        )

    def test_landing_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/landing.html")

    def test_landing_shows_featured_agencies(self):
        response = self.client.get(reverse("home"))
        featured = response.context["featured_agencies"]
        slugs = [a.slug for a in featured]
        self.assertIn("featured", slugs)
        self.assertNotIn("regular", slugs)

    def test_landing_excludes_inactive_featured(self):
        response = self.client.get(reverse("home"))
        featured = response.context["featured_agencies"]
        slugs = [a.slug for a in featured]
        self.assertNotIn("inactive-featured", slugs)
