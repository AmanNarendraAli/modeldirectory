from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.resources.models import ResourceArticle


class ResourceListTests(TestCase):
    """Tests for the resource_list view."""

    def setUp(self):
        self.client = Client()
        ResourceArticle.objects.create(
            title="Published Guide",
            slug="published-guide",
            content="Some content",
            is_published=True,
            published_at=timezone.now(),
        )
        ResourceArticle.objects.create(
            title="Draft Article",
            slug="draft-article",
            content="Draft content",
            is_published=False,
        )

    def test_resource_list_renders(self):
        response = self.client.get(reverse("resource-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resources/resource_list.html")

    def test_resource_list_shows_only_published(self):
        response = self.client.get(reverse("resource-list"))
        articles = response.context["articles"]
        titles = [a.title for a in articles]
        self.assertIn("Published Guide", titles)
        self.assertNotIn("Draft Article", titles)


class ResourceDetailTests(TestCase):
    """Tests for the resource_detail view."""

    def setUp(self):
        self.client = Client()
        self.published = ResourceArticle.objects.create(
            title="Published Article",
            slug="published-article",
            content="Full article content here.",
            is_published=True,
            published_at=timezone.now(),
        )
        self.unpublished = ResourceArticle.objects.create(
            title="Unpublished Article",
            slug="unpublished-article",
            content="Hidden content.",
            is_published=False,
        )

    def test_published_article_renders(self):
        response = self.client.get(reverse("resource-detail", kwargs={"slug": "published-article"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resources/resource_detail.html")
        self.assertEqual(response.context["article"], self.published)

    def test_unpublished_article_returns_404(self):
        response = self.client.get(reverse("resource-detail", kwargs={"slug": "unpublished-article"}))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_article_returns_404(self):
        response = self.client.get(reverse("resource-detail", kwargs={"slug": "no-such-article"}))
        self.assertEqual(response.status_code, 404)
