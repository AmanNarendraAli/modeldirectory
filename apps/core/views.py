from django.shortcuts import render
from apps.agencies.models import Agency


def landing(request):
    featured_agencies = Agency.objects.filter(
        is_active=True, is_featured=True
    ).order_by("featured_order")[:6]
    return render(request, "core/landing.html", {"featured_agencies": featured_agencies})


def error_400(request, exception):
    return render(request, "400.html", status=400)


def error_403(request, exception=None, reason=""):
    return render(request, "403.html", status=403)


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_429(request, exception=None):
    return render(request, "429.html", status=429)


def error_500(request):
    return render(request, "500.html", status=500)
