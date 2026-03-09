from django.shortcuts import render
from apps.agencies.models import Agency


def landing(request):
    featured_agencies = Agency.objects.filter(
        is_active=True, is_featured=True
    ).order_by("featured_order")[:6]
    return render(request, "core/landing.html", {"featured_agencies": featured_agencies})
