from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import SignupForm, OnboardingForm
from apps.models_app.models import ModelProfile
from apps.applications.models import Application


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
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
