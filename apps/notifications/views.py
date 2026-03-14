from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.timesince import timesince

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).select_related("actor")

    # Return partial HTML for the dropdown (last 5)
    if request.GET.get("format") == "partial":
        recent = notifications[:5]
        if not recent:
            return HttpResponse("")
        html = render_to_string("notifications/_notification_items.html", {
            "notifications": recent,
        }, request=request)
        return HttpResponse(html)

    paginator = Paginator(notifications, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "notifications/notification_list.html", {"page_obj": page})


@login_required
def mark_notifications_read(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})
