import datetime

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.cache import cache
from .models import ModelProfile


def _dob_cutoff(today, years):
    """Return the date `years` years before today, handling Feb-29 gracefully."""
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, day=28)


def model_list(request):
    qs = ModelProfile.objects.filter(
        is_public=True, is_discoverable=True
    ).select_related("represented_by_agency")

    search = request.GET.get("q", "").strip()
    selected_cities = request.GET.getlist("city")
    gender = request.GET.get("gender", "").strip()
    represented = request.GET.get("represented", "").strip()
    verified = request.GET.get("verified", "").strip()
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

    if search:
        qs = qs.filter(public_display_name__icontains=search)

    if selected_cities:
        city_q = Q()
        for c in selected_cities:
            city_q |= Q(city__iexact=c)
        qs = qs.filter(city_q)

    if gender:
        qs = qs.filter(gender=gender)

    if represented == "yes":
        qs = qs.filter(represented_by_agency__isnull=False)
    elif represented == "no":
        qs = qs.filter(represented_by_agency__isnull=True)

    if verified == "1":
        qs = qs.filter(verification_status="verified")

    # Age filters — convert age range to date_of_birth range
    today = datetime.date.today()
    if min_age:
        try:
            qs = qs.filter(date_of_birth__lte=_dob_cutoff(today, int(min_age)))
        except (ValueError, OverflowError):
            pass
    if max_age:
        try:
            qs = qs.filter(date_of_birth__gt=_dob_cutoff(today, int(max_age) + 1))
        except (ValueError, OverflowError):
            pass

    # Height filters
    if min_height:
        try:
            qs = qs.filter(height_cm__gte=float(min_height))
        except ValueError:
            pass
    if max_height:
        try:
            qs = qs.filter(height_cm__lte=float(max_height))
        except ValueError:
            pass

    # Bust/chest filters
    if min_bust:
        try:
            qs = qs.filter(bust_cm__gte=float(min_bust))
        except ValueError:
            pass
    if max_bust:
        try:
            qs = qs.filter(bust_cm__lte=float(max_bust))
        except ValueError:
            pass

    # Waist filters
    if min_waist:
        try:
            qs = qs.filter(waist_cm__gte=float(min_waist))
        except ValueError:
            pass
    if max_waist:
        try:
            qs = qs.filter(waist_cm__lte=float(max_waist))
        except ValueError:
            pass

    # Hips filters
    if min_hips:
        try:
            qs = qs.filter(hips_cm__gte=float(min_hips))
        except ValueError:
            pass
    if max_hips:
        try:
            qs = qs.filter(hips_cm__lte=float(max_hips))
        except ValueError:
            pass

    # Inseam filters
    if min_inseam:
        try:
            qs = qs.filter(inseam_cm__gte=float(min_inseam))
        except ValueError:
            pass
    if max_inseam:
        try:
            qs = qs.filter(inseam_cm__lte=float(max_inseam))
        except ValueError:
            pass

    # Hair/eye colour multi-filters (iexact match against distinct DB values)
    if selected_hair_colors:
        hair_q = Q()
        for hc in selected_hair_colors:
            hair_q |= Q(hair_color__iexact=hc)
        qs = qs.filter(hair_q)

    if selected_eye_colors:
        eye_q = Q()
        for ec in selected_eye_colors:
            eye_q |= Q(eye_color__iexact=ec)
        qs = qs.filter(eye_q)

    # Distinct values for filter panels
    base_public = ModelProfile.objects.filter(is_public=True, is_discoverable=True)
    all_cities = cache.get("model_cities")
    if all_cities is None:
        all_cities = list(base_public.exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
        cache.set("model_cities", all_cities, 300)
    all_hair_colors = (
        base_public.exclude(hair_color="").values_list("hair_color", flat=True).distinct().order_by("hair_color")
    )
    all_eye_colors = (
        base_public.exclude(eye_color="").values_list("eye_color", flat=True).distinct().order_by("eye_color")
    )

    # Requirement templates for agency staff (auto-fill filters)
    agency_requirements = []
    if request.user.is_authenticated and request.user.is_agency_staff:
        from apps.agencies.models import AgencyStaff
        staff = AgencyStaff.objects.filter(user=request.user).select_related("agency").first()
        if staff:
            agency_requirements = list(staff.agency.requirements.filter(is_current=True))

    has_filters = any([
        search, selected_cities, gender, represented, verified,
        min_age, max_age, min_height, max_height,
        min_bust, max_bust, min_waist, max_waist,
        min_hips, max_hips, min_inseam, max_inseam,
        selected_hair_colors, selected_eye_colors,
    ])

    return render(request, "models_app/model_list.html", {
        "profiles": qs,
        "all_cities": all_cities,
        "all_hair_colors": all_hair_colors,
        "all_eye_colors": all_eye_colors,
        "gender_choices": ModelProfile.Gender.choices,
        "search": search,
        "selected_cities": selected_cities,
        "selected_gender": gender,
        "selected_represented": represented,
        "selected_verified": verified,
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
        "agency_requirements": agency_requirements,
        "has_filters": has_filters,
        "selected_unit": request.GET.get("unit", "cm"),
    })


def model_detail(request, slug):
    profile = get_object_or_404(ModelProfile.objects.select_related("represented_by_agency"), slug=slug)

    # If profile is private, only the owner or their agency can view it
    is_own_profile = request.user.is_authenticated and request.user == profile.user
    is_agency_viewer = False
    if (
        request.user.is_authenticated
        and hasattr(request.user, "is_agency_staff")
        and request.user.is_agency_staff
        and profile.represented_by_agency
    ):
        from apps.agencies.models import AgencyStaff

        is_agency_viewer = AgencyStaff.objects.filter(
            user=request.user, agency=profile.represented_by_agency
        ).exists()

    if not profile.is_public and not is_own_profile and not is_agency_viewer:
        return render(request, "models_app/model_private.html", status=403)

    if is_own_profile:
        portfolio_posts = profile.portfolio_posts.all()
    else:
        portfolio_posts = profile.portfolio_posts.filter(is_public=True)

    is_following = False
    if request.user.is_authenticated:
        from apps.discovery.models import Follow
        is_following = Follow.objects.filter(follower=request.user, followed_profile=profile).exists()

    follower_count = profile.followers.count()

    # Messaging context
    existing_conversation = None
    can_message = False
    is_blocked = False
    if request.user.is_authenticated and not is_own_profile:
        from apps.messaging.models import Conversation, MessageBlock
        from django.db.models import Q

        # Check if blocked
        is_blocked = MessageBlock.objects.filter(
            Q(blocker=request.user, blocked=profile.user)
            | Q(blocker=profile.user, blocked=request.user)
        ).exists()

        if not is_blocked:
            existing_conversation = Conversation.objects.filter(
                Q(participant_one=request.user, participant_two=profile.user)
                | Q(participant_one=profile.user, participant_two=request.user)
            ).first()

            if existing_conversation:
                # A pending conversation with no messages is just an empty
                # shell from search — don't treat it as a real request
                if (existing_conversation.status == Conversation.Status.PENDING
                        and not existing_conversation.messages.exists()):
                    existing_conversation = None
                    can_message = True
                else:
                    can_message = existing_conversation.status in (
                        Conversation.Status.ACCEPTED,
                        Conversation.Status.PENDING,
                    )
            else:
                can_message = True  # Can start a new conversation

    return render(request, "models_app/model_detail.html", {
        "profile": profile,
        "portfolio_posts": portfolio_posts,
        "is_following": is_following,
        "follower_count": follower_count,
        "is_own_profile": is_own_profile,
        "is_own_private_profile": is_own_profile and not profile.is_public,
        "is_agency_viewer": is_agency_viewer,
        "existing_conversation": existing_conversation,
        "can_message": can_message,
        "is_blocked": is_blocked,
    })
