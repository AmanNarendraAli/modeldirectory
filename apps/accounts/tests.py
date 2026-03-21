from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class AccountTestMixin:
    """Shared setup for account tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            password="OldPassword123!",
        )

    def _make_verify_url(self, user=None):
        user = user or self.user
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return reverse("verify-email", args=[uid, token])


# ─── Change Password Tests ─────────────────────────────────────────────────


class ChangePasswordTest(AccountTestMixin, TestCase):

    def test_change_password_page_requires_login(self):
        response = self.client.get(reverse("password_change"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_change_password_renders(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.get(reverse("password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Change Password")

    def test_change_password_success(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.post(reverse("password_change"), {
            "old_password": "OldPassword123!",
            "new_password1": "NewSecurePass456!",
            "new_password2": "NewSecurePass456!",
        })
        self.assertEqual(response.status_code, 302)
        # Can login with new password
        self.client.logout()
        self.assertTrue(self.client.login(email="test@example.com", password="NewSecurePass456!"))

    def test_change_password_wrong_current(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.post(reverse("password_change"), {
            "old_password": "WrongPassword!",
            "new_password1": "NewSecurePass456!",
            "new_password2": "NewSecurePass456!",
        })
        self.assertEqual(response.status_code, 200)
        # Old password still works
        self.client.logout()
        self.assertTrue(self.client.login(email="test@example.com", password="OldPassword123!"))

    def test_change_password_weak_password(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.post(reverse("password_change"), {
            "old_password": "OldPassword123!",
            "new_password1": "123",
            "new_password2": "123",
        })
        self.assertEqual(response.status_code, 200)
        # Form should show errors

    def test_edit_profile_has_change_password_link(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        # Need a model profile for edit page
        from apps.models_app.models import ModelProfile
        ModelProfile.objects.create(user=self.user, slug="test-user", is_public=True)
        response = self.client.get(reverse("edit-profile"))
        self.assertContains(response, reverse("password_change"))
        self.assertContains(response, "Change Password")


# ─── Email Verification Tests ──────────────────────────────────────────────


class EmailVerificationOnSignupTest(TestCase):

    def test_signup_sends_verification_email(self):
        response = self.client.post(reverse("signup"), {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password1": "SecurePassword123!",
            "password2": "SecurePassword123!",
            "role": "MODEL",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())
        self.assertIn("newuser@example.com", mail.outbox[0].to)

    def test_signup_succeeds_even_if_email_fails(self):
        with patch("apps.accounts.emails.send_mail", side_effect=Exception("SMTP down")):
            response = self.client.post(reverse("signup"), {
                "email": "newuser@example.com",
                "full_name": "New User",
                "password1": "SecurePassword123!",
                "password2": "SecurePassword123!",
                "role": "MODEL",
            })
            # Should still redirect (signup succeeded)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(User.objects.filter(email="newuser@example.com").exists())


class VerifyEmailViewTest(AccountTestMixin, TestCase):

    def test_valid_token_verifies_email(self):
        self.assertFalse(self.user.is_verified_email)
        url = self._make_verify_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Verified")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified_email)

    def test_invalid_token_shows_error(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse("verify-email", args=[uid, "invalid-token"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expired or Invalid")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified_email)

    def test_invalid_uid_shows_error(self):
        url = reverse("verify-email", args=["baduid", "sometoken"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expired or Invalid")

    def test_already_verified_shows_success(self):
        self.user.is_verified_email = True
        self.user.save(update_fields=["is_verified_email"])
        url = self._make_verify_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Verified")

    def test_no_login_required(self):
        # User clicks link from email while logged out
        url = self._make_verify_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Verified")


class ResendVerificationTest(AccountTestMixin, TestCase):

    def test_login_required(self):
        response = self.client.post(reverse("resend-verification"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_resend_sends_email(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.post(reverse("resend-verification"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_skips_if_already_verified(self):
        self.user.is_verified_email = True
        self.user.save(update_fields=["is_verified_email"])
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.post(reverse("resend-verification"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_get_redirects(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.get(reverse("resend-verification"))
        self.assertEqual(response.status_code, 302)


class VerificationBannerTest(AccountTestMixin, TestCase):

    def test_banner_shown_for_unverified_user(self):
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "verify your email")

    def test_banner_hidden_for_verified_user(self):
        self.user.is_verified_email = True
        self.user.save(update_fields=["is_verified_email"])
        self.client.login(email="test@example.com", password="OldPassword123!")
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "verify your email")

    def test_banner_hidden_for_anonymous(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "verify your email")


# ─── Forgot Password Tests ─────────────────────────────────────────────────


class ForgotPasswordTest(AccountTestMixin, TestCase):

    def test_reset_form_renders(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forgot Password")

    def test_verified_user_gets_reset_email(self):
        self.user.is_verified_email = True
        self.user.save(update_fields=["is_verified_email"])
        response = self.client.post(reverse("password_reset"), {
            "email": "test@example.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset", mail.outbox[0].subject.lower())

    def test_unverified_user_no_email_same_page(self):
        # Unverified user sees same "check inbox" page — no info leak
        response = self.client.post(reverse("password_reset"), {
            "email": "test@example.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_nonexistent_email_same_page(self):
        response = self.client.post(reverse("password_reset"), {
            "email": "nobody@example.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_login_page_has_forgot_password_link(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("password_reset"))
        self.assertContains(response, "Forgot password")

    def test_full_reset_flow(self):
        """End-to-end: generate token → visit confirm page → set new password → login."""
        self.user.is_verified_email = True
        self.user.save(update_fields=["is_verified_email"])

        # Generate token directly (same as what Django would email)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        # Visit the confirm URL — Django redirects to set-password URL
        confirm_url = reverse("password_reset_confirm", args=[uid, token])
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Password")

        # The redirect replaces the token with "set-password" in the URL
        form_url = response.redirect_chain[-1][0]

        # Set new password
        response = self.client.post(form_url, {
            "new_password1": "BrandNewPass789!",
            "new_password2": "BrandNewPass789!",
        })
        self.assertEqual(response.status_code, 302)

        # Login with new password
        self.client.logout()
        self.assertTrue(self.client.login(email="test@example.com", password="BrandNewPass789!"))
