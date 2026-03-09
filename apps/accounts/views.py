from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from .forms import SignupForm, OnboardingForm
from apps.models_app.models import ModelProfile


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        if self.object.role == self.object.Role.MODEL:
            return redirect("onboarding")
        return redirect("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


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
