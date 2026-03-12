from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Agency, AgencyStaff


def agency_list(request):
    qs = Agency.objects.filter(is_active=True)

    search = request.GET.get("q", "").strip()
    selected_cities = request.GET.getlist("city")
    accepting = request.GET.get("accepting", "")

    if search:
        qs = qs.filter(name__icontains=search)
    if selected_cities:
        city_q = Q()
        for c in selected_cities:
            city_q |= Q(city__icontains=c)
        qs = qs.filter(city_q)
    if accepting == "1":
        qs = qs.filter(is_accepting_applications=True)

    cities = Agency.objects.filter(is_active=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city")

    user_agency_ids = set()
    if request.user.is_authenticated:
        user_agency_ids = set(
            AgencyStaff.objects.filter(user=request.user).values_list("agency_id", flat=True)
        )

    # Map agency_id → (status_value, status_label) for the current model user's applications
    user_app_statuses = {}
    if request.user.is_authenticated and hasattr(request.user, "model_profile"):
        from apps.applications.models import Application
        status_labels = dict(Application.Status.choices)
        for row in Application.objects.filter(
            applicant_profile=request.user.model_profile
        ).exclude(status=Application.Status.DRAFT).values("agency_id", "status"):
            user_app_statuses[row["agency_id"]] = (row["status"], status_labels.get(row["status"], row["status"]))

    agencies_list = list(qs)
    for ag in agencies_list:
        pair = user_app_statuses.get(ag.pk)
        ag.user_app_status_value = pair[0] if pair else None
        ag.user_app_status_label = pair[1] if pair else None

    return render(request, "agencies/agency_list.html", {
        "agencies": agencies_list,
        "cities": cities,
        "search": search,
        "selected_cities": selected_cities,
        "accepting": accepting,
        "user_agency_ids": user_agency_ids,
    })


def agency_detail(request, slug):
    agency = get_object_or_404(Agency, slug=slug, is_active=True)
    requirements = agency.requirements.filter(is_current=True)
    highlights = agency.highlights.all()

    is_saved = False
    if request.user.is_authenticated:
        from apps.discovery.models import SavedAgency
        is_saved = SavedAgency.objects.filter(user=request.user, agency=agency).exists()

    existing_application = None
    if request.user.is_authenticated and hasattr(request.user, "model_profile"):
        from apps.applications.models import Application
        existing_application = Application.objects.filter(
            applicant_profile=request.user.model_profile, agency=agency
        ).first()

    is_agency_staff = (
        request.user.is_authenticated and
        AgencyStaff.objects.filter(user=request.user, agency=agency).exists()
    )
    viewer_profile = getattr(request.user, "model_profile", None) if request.user.is_authenticated else None

    portfolio_items = agency.portfolio_items.all()

    is_banned = False
    if request.user.is_authenticated and hasattr(request.user, "model_profile"):
        from apps.agencies.models import AgencyBan
        is_banned = AgencyBan.objects.filter(
            model_profile=request.user.model_profile, agency=agency
        ).exists()

    if is_agency_staff:
        roster_models = agency.represented_models.all().order_by("public_display_name")
    elif agency.is_roster_public:
        public_qs = agency.represented_models.filter(is_public=True)
        if viewer_profile and viewer_profile.represented_by_agency_id == agency.pk and not viewer_profile.is_public:
            roster_models = (public_qs | agency.represented_models.filter(pk=viewer_profile.pk)).order_by("public_display_name")
        else:
            roster_models = public_qs.order_by("public_display_name")
    elif viewer_profile and viewer_profile.represented_by_agency_id == agency.pk:
        roster_models = agency.represented_models.filter(pk=viewer_profile.pk)
    else:
        roster_models = None

    roster_is_private = not agency.is_roster_public and not is_agency_staff

    return render(request, "agencies/agency_detail.html", {
        "agency": agency,
        "requirements": requirements,
        "highlights": highlights,
        "portfolio_items": portfolio_items,
        "is_banned": is_banned,
        "roster_is_private": roster_is_private,
        "is_saved": is_saved,
        "existing_application": existing_application,
        "roster_models": roster_models,
    })
