import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from apps.models_app.models import ModelProfile
from apps.portfolio.models import PortfolioPost

User = get_user_model()


class ModelsAppTestMixin:
    """Shared setup for models_app tests."""

    def setUp(self):
        self.client = Client()

        # Public, discoverable model
        self.model_user = User.objects.create_user(
            email="model@test.com",
            full_name="Test Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.model_user.onboarding_completed = True
        self.model_user.save(update_fields=["onboarding_completed"])
        self.public_profile = ModelProfile.objects.create(
            user=self.model_user,
            slug="test-model",
            city="Mumbai",
            gender=ModelProfile.Gender.FEMALE,
            is_public=True,
            is_discoverable=True,
        )

        # Another public model in a different city
        self.model_user2 = User.objects.create_user(
            email="model2@test.com",
            full_name="Delhi Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.model_user2.onboarding_completed = True
        self.model_user2.save(update_fields=["onboarding_completed"])
        self.public_profile2 = ModelProfile.objects.create(
            user=self.model_user2,
            slug="delhi-model",
            city="Delhi",
            gender=ModelProfile.Gender.MALE,
            is_public=True,
            is_discoverable=True,
        )

        # Private model
        self.private_user = User.objects.create_user(
            email="private@test.com",
            full_name="Private Model",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.private_user.onboarding_completed = True
        self.private_user.save(update_fields=["onboarding_completed"])
        self.private_profile = ModelProfile.objects.create(
            user=self.private_user,
            slug="private-model",
            is_public=False,
            is_discoverable=False,
        )

        # Another logged-in user (not an owner)
        self.other_user = User.objects.create_user(
            email="other@test.com",
            full_name="Other User",
            password="testpass123",
            role=User.Role.MODEL,
        )
        self.other_user.onboarding_completed = True
        self.other_user.save(update_fields=["onboarding_completed"])
        ModelProfile.objects.create(
            user=self.other_user, slug="other-user", is_public=True
        )


class ModelListTests(ModelsAppTestMixin, TestCase):
    """Tests for the model_list view."""

    def test_renders_successfully(self):
        url = reverse("model-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("profiles", response.context)

    def test_only_public_discoverable_profiles_shown(self):
        url = reverse("model-list")
        response = self.client.get(url)
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile, profiles)
        self.assertIn(self.public_profile2, profiles)
        self.assertNotIn(self.private_profile, profiles)

    def test_filter_by_city(self):
        url = reverse("model-list")
        response = self.client.get(url, {"city": ["Mumbai"]})
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile, profiles)
        self.assertNotIn(self.public_profile2, profiles)

    def test_filter_by_gender(self):
        url = reverse("model-list")
        response = self.client.get(url, {"gender": "male"})
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile2, profiles)
        self.assertNotIn(self.public_profile, profiles)

    def test_filter_by_search_query(self):
        url = reverse("model-list")
        response = self.client.get(url, {"q": "Delhi"})
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile2, profiles)
        self.assertNotIn(self.public_profile, profiles)

    def test_multiple_city_filter(self):
        url = reverse("model-list")
        response = self.client.get(url, {"city": ["Mumbai", "Delhi"]})
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile, profiles)
        self.assertIn(self.public_profile2, profiles)

    def test_has_filters_context(self):
        url = reverse("model-list")
        # No filters
        response = self.client.get(url)
        self.assertFalse(response.context["has_filters"])
        # With filter
        response = self.client.get(url, {"gender": "female"})
        self.assertTrue(response.context["has_filters"])

    def test_height_filter(self):
        self.public_profile.height_cm = 175
        self.public_profile.save()
        self.public_profile2.height_cm = 165
        self.public_profile2.save()

        url = reverse("model-list")
        response = self.client.get(url, {"min_height": "170"})
        profiles = list(response.context["profiles"])
        self.assertIn(self.public_profile, profiles)
        self.assertNotIn(self.public_profile2, profiles)


class ModelDetailTests(ModelsAppTestMixin, TestCase):
    """Tests for the model_detail view."""

    def test_public_profile_accessible_by_anonymous(self):
        url = reverse("model-detail", kwargs={"slug": self.public_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profile"], self.public_profile)

    def test_private_profile_403_for_anonymous(self):
        url = reverse("model-detail", kwargs={"slug": self.private_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_private_profile_accessible_by_owner(self):
        self.client.login(email="private@test.com", password="testpass123")
        url = reverse("model-detail", kwargs={"slug": self.private_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_own_profile"])

    def test_private_profile_403_for_other_user(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("model-detail", kwargs={"slug": self.private_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_nonexistent_profile_404(self):
        url = reverse("model-detail", kwargs={"slug": "does-not-exist"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_messaging_context_for_logged_in_user(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("model-detail", kwargs={"slug": self.public_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("can_message", response.context)
        self.assertIn("existing_conversation", response.context)
        self.assertIn("is_blocked", response.context)
        # Other user should be able to message (no block, no existing convo)
        self.assertTrue(response.context["can_message"])
        self.assertFalse(response.context["is_blocked"])
        self.assertIsNone(response.context["existing_conversation"])

    def test_messaging_context_not_shown_for_own_profile(self):
        self.client.login(email="model@test.com", password="testpass123")
        url = reverse("model-detail", kwargs={"slug": self.public_profile.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Own profile: can_message should be False (messaging context block skipped)
        self.assertFalse(response.context["can_message"])

    def test_portfolio_posts_context(self):
        # Create a public and private portfolio post
        PortfolioPost.objects.create(
            owner_profile=self.public_profile,
            title="Public Shoot",
            slug="public-shoot",
            is_public=True,
        )
        PortfolioPost.objects.create(
            owner_profile=self.public_profile,
            title="Private Shoot",
            slug="private-shoot",
            is_public=False,
        )

        # Anonymous sees only public posts
        url = reverse("model-detail", kwargs={"slug": self.public_profile.slug})
        response = self.client.get(url)
        titles = [p.title for p in response.context["portfolio_posts"]]
        self.assertIn("Public Shoot", titles)
        self.assertNotIn("Private Shoot", titles)

        # Owner sees all posts
        self.client.login(email="model@test.com", password="testpass123")
        response = self.client.get(url)
        titles = [p.title for p in response.context["portfolio_posts"]]
        self.assertIn("Public Shoot", titles)
        self.assertIn("Private Shoot", titles)

    def test_follow_context(self):
        self.client.login(email="other@test.com", password="testpass123")
        url = reverse("model-detail", kwargs={"slug": self.public_profile.slug})
        response = self.client.get(url)
        self.assertFalse(response.context["is_following"])


class ModelProfileModelTests(TestCase):
    """Tests for the ModelProfile model (slug, age, completeness)."""

    def _make_user(self, email, full_name="Test User"):
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password="testpass123",
            role=User.Role.MODEL,
        )
        return user

    def test_slug_generated_from_display_name(self):
        user = self._make_user("slug1@test.com", "Priya Sharma")
        profile = ModelProfile.objects.create(user=user, public_display_name="Priya Sharma")
        self.assertEqual(profile.slug, "priya-sharma")

    def test_slug_generated_from_full_name_when_no_display_name(self):
        user = self._make_user("slug2@test.com", "Ankit Verma")
        profile = ModelProfile.objects.create(user=user)
        self.assertEqual(profile.slug, "ankit-verma")

    def test_slug_uniqueness_with_counter(self):
        user1 = self._make_user("slug3@test.com", "Same Name")
        user2 = self._make_user("slug4@test.com", "Same Name")
        p1 = ModelProfile.objects.create(user=user1, public_display_name="Same Name")
        p2 = ModelProfile.objects.create(user=user2, public_display_name="Same Name")
        self.assertEqual(p1.slug, "same-name")
        self.assertEqual(p2.slug, "same-name-2")

    def test_slug_uniqueness_triple(self):
        user1 = self._make_user("s1@test.com", "Triple Name")
        user2 = self._make_user("s2@test.com", "Triple Name")
        user3 = self._make_user("s3@test.com", "Triple Name")
        p1 = ModelProfile.objects.create(user=user1, public_display_name="Triple Name")
        p2 = ModelProfile.objects.create(user=user2, public_display_name="Triple Name")
        p3 = ModelProfile.objects.create(user=user3, public_display_name="Triple Name")
        self.assertEqual(p1.slug, "triple-name")
        self.assertEqual(p2.slug, "triple-name-2")
        self.assertEqual(p3.slug, "triple-name-3")

    def test_explicit_slug_preserved(self):
        user = self._make_user("slug5@test.com", "Whatever")
        profile = ModelProfile.objects.create(user=user, slug="custom-slug")
        self.assertEqual(profile.slug, "custom-slug")

    def test_age_calculation(self):
        user = self._make_user("age@test.com", "Age Test")
        profile = ModelProfile.objects.create(user=user, slug="age-test")

        # Set DOB to exactly 25 years ago
        today = datetime.date.today()
        dob = today.replace(year=today.year - 25)
        profile.date_of_birth = dob
        profile.save()
        self.assertEqual(profile.age, 25)

    def test_age_before_birthday_this_year(self):
        user = self._make_user("age2@test.com", "Age Test 2")
        profile = ModelProfile.objects.create(user=user, slug="age-test-2")

        # Set DOB so birthday hasn't happened yet this year (tomorrow)
        today = datetime.date.today()
        try:
            future_bday = today.replace(year=today.year - 25, month=today.month, day=today.day + 1)
        except ValueError:
            # End of month edge case: use next month 1st
            if today.month == 12:
                future_bday = datetime.date(today.year - 25, 1, 1)
            else:
                future_bday = datetime.date(today.year - 25, today.month + 1, 1)
        profile.date_of_birth = future_bday
        profile.save()
        self.assertEqual(profile.age, 24)

    def test_age_returns_none_when_no_dob(self):
        user = self._make_user("age3@test.com", "No DOB")
        profile = ModelProfile.objects.create(user=user, slug="no-dob")
        self.assertIsNone(profile.age)

    def test_completeness_empty_profile(self):
        user = self._make_user("complete@test.com", "Empty Profile")
        profile = ModelProfile.objects.create(user=user, slug="empty-profile")
        pct, missing = profile.get_completeness()
        self.assertEqual(pct, 0)
        self.assertEqual(len(missing), 12)

    def test_completeness_partial_profile(self):
        user = self._make_user("partial@test.com", "Partial Profile")
        profile = ModelProfile.objects.create(
            user=user,
            slug="partial-profile",
            bio="Hello world",
            city="Mumbai",
            gender=ModelProfile.Gender.FEMALE,
            height_cm=170,
            bust_cm=85,
            waist_cm=65,
            contact_email="me@example.com",
            instagram_url="https://instagram.com/test",
            available_for_runway=True,
        )
        # That fills: bio, city, gender, height, bust, waist, contact, social, availability = 9/12
        # Missing: profile image, date of birth, portfolio post = 3
        pct, missing = profile.get_completeness()
        self.assertEqual(pct, 75)  # 9/12 = 75%
        self.assertEqual(len(missing), 3)
        self.assertIn("Profile image", missing)
        self.assertIn("Date of birth", missing)
        self.assertIn("At least one portfolio post", missing)

    def test_completeness_with_portfolio_post(self):
        user = self._make_user("withpost@test.com", "With Post")
        profile = ModelProfile.objects.create(
            user=user,
            slug="with-post",
            bio="Bio",
            city="Delhi",
            date_of_birth=datetime.date(2000, 1, 1),
            gender=ModelProfile.Gender.MALE,
            height_cm=180,
            bust_cm=95,
            waist_cm=80,
            contact_email="x@example.com",
            instagram_url="https://instagram.com/x",
            available_for_editorial=True,
        )
        # Create a public portfolio post
        PortfolioPost.objects.create(
            owner_profile=profile, title="My Shoot", slug="my-shoot", is_public=True
        )
        pct, missing = profile.get_completeness()
        # 11/12 (missing profile image only)
        self.assertEqual(pct, 91)
        self.assertEqual(len(missing), 1)
        self.assertIn("Profile image", missing)

    def test_public_display_name_auto_filled(self):
        user = self._make_user("auto@test.com", "Auto Name")
        profile = ModelProfile.objects.create(user=user, slug="auto-name")
        self.assertEqual(profile.public_display_name, "Auto Name")

    def test_bust_chest_label(self):
        user_m = self._make_user("male@test.com", "Male Model")
        profile_m = ModelProfile.objects.create(
            user=user_m, slug="male-model", gender=ModelProfile.Gender.MALE
        )
        self.assertEqual(profile_m.get_bust_chest_label(), "Chest")

        user_f = self._make_user("female@test.com", "Female Model")
        profile_f = ModelProfile.objects.create(
            user=user_f, slug="female-model", gender=ModelProfile.Gender.FEMALE
        )
        self.assertEqual(profile_f.get_bust_chest_label(), "Bust")

    def test_str_representation(self):
        user = self._make_user("str@test.com", "Display Name Test")
        profile = ModelProfile.objects.create(
            user=user, slug="str-test", public_display_name="Stunning Model"
        )
        self.assertEqual(str(profile), "Stunning Model")
