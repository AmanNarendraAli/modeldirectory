from django.shortcuts import render, get_object_or_404
from .models import ModelProfile


def model_list(request):
    qs = ModelProfile.objects.filter(is_public=True, is_discoverable=True)

    search = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    gender = request.GET.get("gender", "").strip()
    represented = request.GET.get("represented", "").strip()

    if search:
        qs = qs.filter(public_display_name__icontains=search)
    if city:
        qs = qs.filter(city__icontains=city)
    if gender:
        qs = qs.filter(gender=gender)
    if represented == "yes":
        qs = qs.filter(represented_by_agency__isnull=False)
    elif represented == "no":
        qs = qs.filter(represented_by_agency__isnull=True)

    cities = ModelProfile.objects.filter(is_public=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city")

    return render(request, "models_app/model_list.html", {
        "profiles": qs,
        "cities": cities,
        "gender_choices": ModelProfile.Gender.choices,
        "search": search,
        "selected_city": city,
        "selected_gender": gender,
        "selected_represented": represented,
    })


def model_detail(request, slug):
    profile = get_object_or_404(ModelProfile, slug=slug, is_public=True)
    portfolio_posts = profile.portfolio_posts.filter(is_public=True)

    is_following = False
    if request.user.is_authenticated:
        from apps.discovery.models import Follow
        is_following = Follow.objects.filter(follower=request.user, followed_profile=profile).exists()

    follower_count = profile.followers.count()

    return render(request, "models_app/model_detail.html", {
        "profile": profile,
        "portfolio_posts": portfolio_posts,
        "is_following": is_following,
        "follower_count": follower_count,
    })
