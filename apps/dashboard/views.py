from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.models_app.models import ModelProfile
from apps.applications.models import Application
from apps.discovery.models import SavedAgency, Follow
from apps.portfolio.models import PortfolioPost
from apps.accounts.forms import OnboardingForm
from apps.agencies.models import AgencyStaff


def _get_agency_for_staff(user):
    """Return the agency this staff member manages, or None."""
    staff = AgencyStaff.objects.filter(user=user, can_review_applications=True).select_related("agency").first()
    return staff.agency if staff else None


@login_required
def dashboard(request):
    if request.user.is_agency_staff:
        return agency_dashboard(request)
    return model_dashboard(request)


@login_required
def model_dashboard(request):
    if not request.user.is_model_user:
        return redirect("home")

    if not request.user.onboarding_completed:
        return redirect("onboarding")

    profile = get_object_or_404(ModelProfile, user=request.user)
    applications = Application.objects.filter(applicant_profile=profile).select_related("agency").order_by("-submitted_at")
    portfolio_posts = PortfolioPost.objects.filter(owner_profile=profile).order_by("-created_at")
    saved_agencies = SavedAgency.objects.filter(user=request.user).select_related("agency")
    followed_profiles = Follow.objects.filter(follower=request.user).select_related("followed_profile")

    # Profile completeness
    fields = [profile.profile_image, profile.bio, profile.city, profile.height_cm, profile.instagram_url or profile.contact_email]
    completeness = int(sum(1 for f in fields if f) / len(fields) * 100)

    return render(request, "dashboard/model_dashboard.html", {
        "profile": profile,
        "applications": applications,
        "portfolio_posts": portfolio_posts,
        "saved_agencies": saved_agencies,
        "followed_profiles": followed_profiles,
        "completeness": completeness,
    })


@login_required
def edit_profile(request):
    if not request.user.is_model_user:
        return redirect("home")

    profile = get_object_or_404(ModelProfile, user=request.user)

    if request.method == "POST":
        form = OnboardingForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard")
    else:
        form = OnboardingForm(instance=profile)

    return render(request, "dashboard/edit_profile.html", {"form": form, "profile": profile})


@login_required
def agency_dashboard(request):
    agency = _get_agency_for_staff(request.user)
    if not agency:
        messages.error(request, "You are not linked to any agency. Contact an admin.")
        return redirect("home")

    status_filter = request.GET.get("status", "")
    city_filter = request.GET.get("city", "").strip()

    applications = Application.objects.filter(agency=agency).select_related(
        "applicant_profile", "applicant_profile__user"
    ).order_by("-submitted_at")

    if status_filter:
        applications = applications.filter(status=status_filter)
    if city_filter:
        applications = applications.filter(applicant_profile__city__icontains=city_filter)

    return render(request, "dashboard/agency_dashboard.html", {
        "agency": agency,
        "applications": applications,
        "status_choices": Application.Status.choices,
        "status_filter": status_filter,
        "city_filter": city_filter,
    })


@login_required
def applicant_detail(request, application_id):
    agency = _get_agency_for_staff(request.user)
    if not agency:
        return redirect("home")

    application = get_object_or_404(Application, id=application_id, agency=agency)
    snapshot = getattr(application, "snapshot", None)
    portfolio_posts = PortfolioPost.objects.filter(
        owner_profile=application.applicant_profile, is_public=True
    )

    return render(request, "dashboard/applicant_detail.html", {
        "application": application,
        "snapshot": snapshot,
        "portfolio_posts": portfolio_posts,
        "agency": agency,
        "status_choices": Application.Status.choices,
    })


@login_required
def update_application_status(request, application_id):
    if request.method != "POST":
        return redirect("agency-dashboard")

    agency = _get_agency_for_staff(request.user)
    if not agency:
        return redirect("home")

    application = get_object_or_404(Application, id=application_id, agency=agency)
    new_status = request.POST.get("status")
    valid_statuses = [s[0] for s in Application.Status.choices]

    if new_status in valid_statuses:
        application.status = new_status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        messages.success(request, f"Application status updated to {application.get_status_display()}.")

    return redirect("applicant-detail", application_id=application_id)
