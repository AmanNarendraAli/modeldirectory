from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Agency


def agency_list(request):
    qs = Agency.objects.filter(is_active=True)

    search = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    accepting = request.GET.get("accepting", "")

    if search:
        qs = qs.filter(name__icontains=search)
    if city:
        qs = qs.filter(city__icontains=city)
    if accepting == "1":
        qs = qs.filter(is_accepting_applications=True)

    cities = Agency.objects.filter(is_active=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city")

    return render(request, "agencies/agency_list.html", {
        "agencies": qs,
        "cities": cities,
        "search": search,
        "selected_city": city,
        "accepting": accepting,
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

    return render(request, "agencies/agency_detail.html", {
        "agency": agency,
        "requirements": requirements,
        "highlights": highlights,
        "is_saved": is_saved,
        "existing_application": existing_application,
    })
