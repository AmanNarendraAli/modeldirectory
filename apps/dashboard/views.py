from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.http import JsonResponse

from apps.models_app.models import ModelProfile
from apps.applications.models import Application
from apps.applications.forms import FeedbackForm, ContactApplicantForm
from apps.discovery.models import SavedAgency, Follow
from apps.portfolio.models import PortfolioPost
from apps.accounts.forms import OnboardingForm
from apps.agencies.models import AgencyStaff
from apps.agencies.forms import AgencyEditForm, AgencyRequirementFormSet


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

    completeness, missing_fields = profile.get_completeness()

    return render(request, "dashboard/model_dashboard.html", {
        "profile": profile,
        "applications": applications,
        "portfolio_posts": portfolio_posts,
        "saved_agencies": saved_agencies,
        "followed_profiles": followed_profiles,
        "completeness": completeness,
        "missing_fields": missing_fields,
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
    import datetime

    agency = _get_agency_for_staff(request.user)
    if not agency:
        messages.error(request, "You are not linked to any agency. Contact an admin.")
        return redirect("home")

    status_filter = request.GET.get("status", "")
    selected_cities = request.GET.getlist("city")
    min_age = request.GET.get("min_age", "").strip()
    max_age = request.GET.get("max_age", "").strip()
    min_height = request.GET.get("min_height", "").strip()
    max_height = request.GET.get("max_height", "").strip()
    min_bust = request.GET.get("min_bust", "").strip()
    max_bust = request.GET.get("max_bust", "").strip()
    min_waist = request.GET.get("min_waist", "").strip()
    max_waist = request.GET.get("max_waist", "").strip()
    min_hips = request.GET.get("min_hips", "").strip()
    max_hips = request.GET.get("max_hips", "").strip()
    min_inseam = request.GET.get("min_inseam", "").strip()
    max_inseam = request.GET.get("max_inseam", "").strip()
    selected_hair_colors = request.GET.getlist("hair_color")
    selected_eye_colors = request.GET.getlist("eye_color")
    verified = request.GET.get("verified", "").strip()

    applications = Application.objects.filter(agency=agency).select_related(
        "applicant_profile", "applicant_profile__user"
    ).order_by("-submitted_at")

    if status_filter:
        applications = applications.filter(status=status_filter)

    if selected_cities:
        from django.db.models import Q as DQ
        city_q = DQ()
        for c in selected_cities:
            city_q |= DQ(applicant_profile__city__iexact=c)
        applications = applications.filter(city_q)

    today = datetime.date.today()

    def _dob_cutoff(years):
        try:
            return today.replace(year=today.year - years)
        except ValueError:
            return today.replace(year=today.year - years, day=28)

    if min_age:
        try:
            applications = applications.filter(applicant_profile__date_of_birth__lte=_dob_cutoff(int(min_age)))
        except (ValueError, OverflowError):
            pass
    if max_age:
        try:
            applications = applications.filter(applicant_profile__date_of_birth__gt=_dob_cutoff(int(max_age) + 1))
        except (ValueError, OverflowError):
            pass
    if min_height:
        try:
            applications = applications.filter(applicant_profile__height_cm__gte=float(min_height))
        except ValueError:
            pass
    if max_height:
        try:
            applications = applications.filter(applicant_profile__height_cm__lte=float(max_height))
        except ValueError:
            pass
    if min_bust:
        try:
            applications = applications.filter(applicant_profile__bust_cm__gte=float(min_bust))
        except ValueError:
            pass
    if max_bust:
        try:
            applications = applications.filter(applicant_profile__bust_cm__lte=float(max_bust))
        except ValueError:
            pass
    if min_waist:
        try:
            applications = applications.filter(applicant_profile__waist_cm__gte=float(min_waist))
        except ValueError:
            pass
    if max_waist:
        try:
            applications = applications.filter(applicant_profile__waist_cm__lte=float(max_waist))
        except ValueError:
            pass
    if min_hips:
        try:
            applications = applications.filter(applicant_profile__hips_cm__gte=float(min_hips))
        except ValueError:
            pass
    if max_hips:
        try:
            applications = applications.filter(applicant_profile__hips_cm__lte=float(max_hips))
        except ValueError:
            pass
    if min_inseam:
        try:
            applications = applications.filter(applicant_profile__inseam_cm__gte=float(min_inseam))
        except ValueError:
            pass
    if max_inseam:
        try:
            applications = applications.filter(applicant_profile__inseam_cm__lte=float(max_inseam))
        except ValueError:
            pass
    if selected_hair_colors:
        from django.db.models import Q as DQ
        hair_q = DQ()
        for hc in selected_hair_colors:
            hair_q |= DQ(applicant_profile__hair_color__iexact=hc)
        applications = applications.filter(hair_q)
    if selected_eye_colors:
        from django.db.models import Q as DQ
        eye_q = DQ()
        for ec in selected_eye_colors:
            eye_q |= DQ(applicant_profile__eye_color__iexact=ec)
        applications = applications.filter(eye_q)
    if verified == "1":
        applications = applications.filter(applicant_profile__verification_status="verified")

    # Distinct city/hair/eye values from this agency's applicants (unfiltered)
    base_apps = Application.objects.filter(agency=agency).select_related("applicant_profile")
    applicant_cities = list(
        base_apps.exclude(applicant_profile__city="")
        .values_list("applicant_profile__city", flat=True)
        .distinct().order_by("applicant_profile__city")
    )
    applicant_hair_colors = list(
        base_apps.exclude(applicant_profile__hair_color="")
        .values_list("applicant_profile__hair_color", flat=True)
        .distinct().order_by("applicant_profile__hair_color")
    )
    applicant_eye_colors = list(
        base_apps.exclude(applicant_profile__eye_color="")
        .values_list("applicant_profile__eye_color", flat=True)
        .distinct().order_by("applicant_profile__eye_color")
    )

    can_edit = AgencyStaff.objects.filter(user=request.user, agency=agency, can_edit_agency=True).exists()
    roster_models = agency.represented_models.all().order_by('public_display_name')
    agency_requirements = list(agency.requirements.filter(is_current=True))

    has_filters = any([
        status_filter, selected_cities, min_age, max_age, min_height, max_height,
        min_bust, max_bust, min_waist, max_waist, min_hips, max_hips,
        min_inseam, max_inseam, selected_hair_colors, selected_eye_colors, verified,
    ])

    return render(request, "dashboard/agency_dashboard.html", {
        "agency": agency,
        "applications": applications,
        "status_choices": Application.Status.choices,
        "status_filter": status_filter,
        "selected_cities": selected_cities,
        "applicant_cities": applicant_cities,
        "applicant_hair_colors": applicant_hair_colors,
        "applicant_eye_colors": applicant_eye_colors,
        "min_age": min_age,
        "max_age": max_age,
        "min_height": min_height,
        "max_height": max_height,
        "min_bust": min_bust,
        "max_bust": max_bust,
        "min_waist": min_waist,
        "max_waist": max_waist,
        "min_hips": min_hips,
        "max_hips": max_hips,
        "min_inseam": min_inseam,
        "max_inseam": max_inseam,
        "selected_hair_colors": selected_hair_colors,
        "selected_eye_colors": selected_eye_colors,
        "verified": verified,
        "can_edit": can_edit,
        "roster_models": roster_models,
        "agency_requirements": agency_requirements,
        "has_filters": has_filters,
        "selected_unit": request.GET.get("unit", "cm"),
    })


@login_required
def edit_agency(request):
    staff = AgencyStaff.objects.filter(user=request.user, can_edit_agency=True).select_related("agency").first()
    if not staff:
        messages.error(request, "You don't have permission to edit this agency.")
        return redirect("dashboard")
    agency = staff.agency
    if request.method == "POST":
        form = AgencyEditForm(request.POST, request.FILES, instance=agency)
        req_formset = AgencyRequirementFormSet(request.POST, instance=agency, prefix="req")
        if form.is_valid() and req_formset.is_valid():
            form.save()
            req_formset.save()
            messages.success(request, "Agency profile updated.")
            return redirect("dashboard")
    else:
        form = AgencyEditForm(instance=agency)
        req_formset = AgencyRequirementFormSet(instance=agency, prefix="req")
    return render(request, "dashboard/edit_agency.html", {
        "form": form,
        "agency": agency,
        "req_formset": req_formset,
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
    feedback_form = FeedbackForm(instance=application)
    contact_form = ContactApplicantForm()

    return render(request, "dashboard/applicant_detail.html", {
        "application": application,
        "snapshot": snapshot,
        "portfolio_posts": portfolio_posts,
        "agency": agency,
        "status_choices": Application.Status.choices,
        "feedback_form": feedback_form,
        "contact_form": contact_form,
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

        from apps.core.emails import send_status_changed_email
        send_status_changed_email(application)

    return redirect("applicant-detail", application_id=application_id)


@login_required
def submit_feedback(request, application_id):
    if request.method != "POST":
        return redirect("agency-dashboard")

    agency = _get_agency_for_staff(request.user)
    if not agency:
        return redirect("home")

    application = get_object_or_404(Application, id=application_id, agency=agency)
    form = FeedbackForm(request.POST, instance=application)
    if form.is_valid():
        app = form.save(commit=False)
        app.feedback_updated_at = timezone.now()
        app.save(update_fields=["feedback", "feedback_updated_at"])
        messages.success(request, "Feedback saved.")

    return redirect("applicant-detail", application_id=application_id)


@login_required
def contact_applicant(request, application_id):
    if request.method != "POST":
        return redirect("agency-dashboard")

    agency = _get_agency_for_staff(request.user)
    if not agency:
        return redirect("home")

    application = get_object_or_404(Application, id=application_id, agency=agency)
    form = ContactApplicantForm(request.POST)
    if form.is_valid():
        subject = form.cleaned_data["subject"]
        body = form.cleaned_data["body"]
        recipient = application.applicant_profile.contact_email or application.applicant_profile.user.email
        from_email = request.user.email
        send_mail(
            subject=f"[{agency.name}] {subject}",
            message=body,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=True,
        )
        messages.success(request, f"Email sent to {recipient}.")

    return redirect("applicant-detail", application_id=application_id)


@login_required
def link_model(request, agency_id):
    if request.method != "POST":
        return redirect("dashboard")

    agency = _get_agency_for_staff(request.user)
    if not agency or agency.id != agency_id:
        return redirect("home")

    model_id = request.POST.get("model_id", "").strip()
    if not model_id:
        messages.error(request, "No model selected.")
        return redirect("dashboard")

    try:
        model_profile = ModelProfile.objects.get(pk=model_id)
    except (ModelProfile.DoesNotExist, ValueError):
        messages.error(request, "Model not found.")
        return redirect("dashboard")

    if model_profile.represented_by_agency == agency:
        messages.info(request, f"{model_profile.public_display_name} is already on the roster.")
    else:
        from apps.agencies.models import AgencyBan
        AgencyBan.objects.filter(model_profile=model_profile, agency=agency).delete()
        model_profile.represented_by_agency = agency
        model_profile.save(update_fields=["represented_by_agency"])
        messages.success(request, f"Added {model_profile.public_display_name} to the roster.")

    return redirect("dashboard")


@login_required
def unlink_model(request, agency_id, model_id):
    if request.method != "POST":
        return redirect("dashboard")

    agency = _get_agency_for_staff(request.user)
    if not agency or agency.id != agency_id:
        return redirect("home")

    model_profile = get_object_or_404(ModelProfile, id=model_id, represented_by_agency=agency)
    model_profile.represented_by_agency = None
    model_profile.save(update_fields=["represented_by_agency"])

    from apps.agencies.models import AgencyBan
    AgencyBan.objects.get_or_create(model_profile=model_profile, agency=agency)

    messages.success(request, f"Removed {model_profile.public_display_name} from the roster.")
    return redirect("dashboard")


@login_required
def search_models_for_roster(request, agency_id):
    agency = _get_agency_for_staff(request.user)
    if not agency or agency.id != agency_id:
        return JsonResponse({"error": "Forbidden"}, status=403)

    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    profiles = (
        ModelProfile.objects
        .filter(public_display_name__icontains=q)
        .exclude(represented_by_agency=agency)
        .select_related("user")[:10]
    )

    results = []
    for p in profiles:
        results.append({
            "id": p.id,
            "name": p.public_display_name,
            "city": p.city or "",
            "height_cm": p.height_cm or "",
            "profile_image_url": p.profile_image.url if p.profile_image else "",
        })

    return JsonResponse({"results": results})
