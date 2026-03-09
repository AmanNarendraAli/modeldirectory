from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from apps.discovery.models import SavedAgency, Follow
from apps.agencies.models import Agency
from apps.models_app.models import ModelProfile


@login_required
def save_agency(request, slug):
    if request.method != "POST":
        return redirect("agency-detail", slug=slug)
    agency = get_object_or_404(Agency, slug=slug)
    obj, created = SavedAgency.objects.get_or_create(user=request.user, agency=agency)
    if not created:
        obj.delete()
    return redirect("agency-detail", slug=slug)


@login_required
def follow_model(request, slug):
    if request.method != "POST":
        return redirect("model-detail", slug=slug)
    profile = get_object_or_404(ModelProfile, slug=slug)
    if profile.user == request.user:
        return redirect("model-detail", slug=slug)
    obj, created = Follow.objects.get_or_create(follower=request.user, followed_profile=profile)
    if not created:
        obj.delete()
    return redirect("model-detail", slug=slug)
