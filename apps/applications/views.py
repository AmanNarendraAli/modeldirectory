from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.agencies.models import Agency
from apps.models_app.models import ModelProfile
from .models import Application, ApplicationSnapshot
from .forms import ApplicationForm


@login_required
def apply(request, agency_slug):
    if not request.user.is_model_user:
        messages.error(request, "Only model accounts can apply to agencies.")
        return redirect("agency-detail", slug=agency_slug)

    agency = get_object_or_404(Agency, slug=agency_slug, is_active=True)

    if not agency.is_accepting_applications:
        messages.error(request, "This agency is not currently accepting applications.")
        return redirect("agency-detail", slug=agency_slug)

    if not request.user.onboarding_completed:
        messages.warning(request, "Please complete your profile before applying.")
        return redirect("onboarding")

    profile = get_object_or_404(ModelProfile, user=request.user)

    # Duplicate guard
    existing = Application.objects.filter(
        applicant_profile=profile, agency=agency
    ).exclude(status=Application.Status.WITHDRAWN).first()
    if existing:
        messages.info(request, f"You've already applied to {agency.name}.")
        return redirect("agency-detail", slug=agency_slug)

    from apps.agencies.models import AgencyBan
    if AgencyBan.objects.filter(model_profile=profile, agency=agency).exists():
        messages.error(request, "You are unable to apply to this agency.")
        return redirect("agency-detail", slug=agency_slug)

    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant_profile = profile
            application.agency = agency
            application.status = Application.Status.SUBMITTED
            application.submitted_at = timezone.now()
            application.save()

            # Create snapshot
            posts = list(profile.portfolio_posts.filter(is_public=True).values("id", "title", "slug")[:5])
            ApplicationSnapshot.objects.create(
                application=application,
                applicant_name=profile.public_display_name or profile.user.full_name,
                gender=profile.gender,
                city=profile.city,
                height_cm=profile.height_cm,
                bust_cm=profile.bust_cm,
                waist_cm=profile.waist_cm,
                hips_cm=profile.hips_cm,
                inseam_cm=profile.inseam_cm,
                portfolio_summary=profile.bio,
                selected_portfolio_posts=posts,
                submission_payload={
                    "cover_note": application.cover_note,
                    "available_for_editorial": profile.available_for_editorial,
                    "available_for_runway": profile.available_for_runway,
                    "available_for_commercial": profile.available_for_commercial,
                },
            )
            from apps.core.emails import send_application_submitted_email
            send_application_submitted_email(application)
            return redirect("apply-success", agency_slug=agency_slug)
    else:
        form = ApplicationForm()

    recent_posts = profile.portfolio_posts.filter(is_public=True)[:6]

    return render(request, "applications/apply.html", {
        "agency": agency,
        "profile": profile,
        "form": form,
        "recent_posts": recent_posts,
    })


@login_required
def apply_success(request, agency_slug):
    agency = get_object_or_404(Agency, slug=agency_slug)
    return render(request, "applications/apply_success.html", {"agency": agency})
