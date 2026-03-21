from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .emails import send_verification_email
from .forms import SignupForm, OnboardingForm
from apps.models_app.models import ModelProfile
from apps.applications.models import Application

User = get_user_model()


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        send_verification_email(user, self.request)
        if user.role == user.Role.MODEL:
            return redirect("onboarding")
        return redirect("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(ratelimit(key="ip", rate="5/h", method="POST"))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@login_required
def onboarding(request):
    # Only models need onboarding
    if not request.user.is_model_user:
        return redirect("home")

    # Already done
    if request.user.onboarding_completed:
        return redirect("dashboard")

    # Get or init profile instance
    profile = ModelProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = OnboardingForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            request.user.onboarding_completed = True
            request.user.save(update_fields=["onboarding_completed"])
            messages.success(request, "Welcome! Your profile is ready.")
            return redirect("dashboard")
    else:
        form = OnboardingForm(instance=profile)

    return render(request, "accounts/onboarding.html", {"form": form})


# ─── Email Verification ────────────────────────────────────────────────────


def verify_email(request, uidb64, token):
    """Verify a user's email via token link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, "accounts/verify_email_invalid.html")

    # Already verified — handle repeat clicks gracefully
    if user.is_verified_email:
        return render(request, "accounts/verify_email_done.html")

    if default_token_generator.check_token(user, token):
        user.is_verified_email = True
        user.save(update_fields=["is_verified_email"])
        return render(request, "accounts/verify_email_done.html")

    return render(request, "accounts/verify_email_invalid.html")


@login_required
@ratelimit(key="user", rate="3/h", method="POST")
def resend_verification(request):
    """Resend verification email."""
    if request.method != "POST":
        return redirect("dashboard")

    if request.user.is_verified_email:
        messages.info(request, "Your email is already verified.")
        return redirect("dashboard")

    send_verification_email(request.user, request)
    messages.success(request, "Verification email sent! Check your inbox.")
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


# ─── Forgot Password (verified users only) ─────────────────────────────────


class VerifiedPasswordResetView(PasswordResetView):
    """Password reset that shows the same page for all outcomes (no info leak)."""
    template_name = "registration/password_reset_form.html"
    email_template_name = "accounts/emails/password_reset_email.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal that the account doesn't exist
            return redirect("password_reset_done")

        if not user.is_verified_email:
            # Don't reveal verified/unverified status — same neutral page
            return redirect("password_reset_done")

        return super().form_valid(form)


# ─── Account Deletion ──────────────────────────────────────────────────────


@login_required
@ratelimit(key="user", rate="3/h", method="POST")
def delete_account(request):
    if request.method == "POST":
        confirm_text = request.POST.get("confirm", "")
        if confirm_text.lower() == "delete my account":
            user = request.user

            # Delete all applications submitted by this user
            profile = ModelProfile.objects.filter(user=user).first()
            if profile:
                Application.objects.filter(applicant_profile=profile).delete()

                # Free up the model profile slug so it can be reused
                profile.slug = f"deleted-{user.id}"
                profile.public_display_name = "Deleted User"
                profile.is_public = False
                profile.is_discoverable = False
                profile.save(update_fields=[
                    "slug", "public_display_name", "is_public", "is_discoverable",
                ])

            user.is_active = False
            user.email = f"deleted_{user.id}@deleted.modellingdirectory.com"
            user.full_name = "Deleted User"
            user.save(update_fields=["is_active", "email", "full_name"])
            logout(request)
            messages.success(request, "Your account has been deleted.")
            return redirect("home")
        else:
            messages.error(request, 'Please type "delete my account" exactly to confirm.')
    return render(request, "accounts/delete_account.html")
