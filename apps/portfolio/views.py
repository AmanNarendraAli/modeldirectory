from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import PortfolioPost
from .forms import PortfolioPostForm, PortfolioAssetFormset


def portfolio_detail(request, slug):
    post = get_object_or_404(PortfolioPost, slug=slug, is_public=True)
    assets = post.assets.all()
    return render(request, "portfolio/portfolio_detail.html", {
        "post": post,
        "assets": assets,
    })


@login_required
def portfolio_create(request):
    if not request.user.is_model_user:
        return redirect("home")
    if not hasattr(request.user, "model_profile"):
        return redirect("onboarding")

    profile = request.user.model_profile

    if request.method == "POST":
        form = PortfolioPostForm(request.POST, request.FILES)
        formset = PortfolioAssetFormset(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            post = form.save(commit=False)
            post.owner_profile = profile
            post.save()
            formset.instance = post
            formset.save()
            messages.success(request, "Portfolio post created.")
            return redirect("portfolio-detail", slug=post.slug)
    else:
        form = PortfolioPostForm()
        formset = PortfolioAssetFormset()

    return render(request, "portfolio/portfolio_form.html", {
        "form": form,
        "formset": formset,
        "action": "Create",
    })


@login_required
def portfolio_edit(request, slug):
    if not request.user.is_model_user:
        return redirect("home")
    profile = request.user.model_profile
    post = get_object_or_404(PortfolioPost, slug=slug, owner_profile=profile)

    if request.method == "POST":
        form = PortfolioPostForm(request.POST, request.FILES, instance=post)
        formset = PortfolioAssetFormset(request.POST, request.FILES, instance=post)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Portfolio post updated.")
            return redirect("portfolio-detail", slug=post.slug)
    else:
        form = PortfolioPostForm(instance=post)
        formset = PortfolioAssetFormset(instance=post)

    return render(request, "portfolio/portfolio_form.html", {
        "form": form,
        "formset": formset,
        "post": post,
        "action": "Edit",
    })


@login_required
def portfolio_delete(request, slug):
    if not request.user.is_model_user:
        return redirect("home")
    profile = request.user.model_profile
    post = get_object_or_404(PortfolioPost, slug=slug, owner_profile=profile)

    if request.method == "POST":
        post.delete()
        messages.success(request, "Portfolio post deleted.")
        return redirect("dashboard")

    return render(request, "portfolio/portfolio_confirm_delete.html", {"post": post})
