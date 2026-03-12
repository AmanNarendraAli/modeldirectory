# The Modelling Directory — Phase 4 Workplan

## Goal

Ship a polished, production-ready platform. Phase 4 adds an agency portfolio/past work showcase, removes the send-email form, polishes every user-facing surface (toast auto-dismiss, empty states, custom error pages), hardens security (rate limiting, CSRF audit, input sanitization), optimises database queries, and prepares the deployment stack (WhiteNoise, S3 media storage, production settings).

---

## Prerequisites (from Phase 3)

- ✅ Agency self-management (edit agency, requirements, roster)
- ✅ Application workflow with feedback and email notifications
- ✅ Email infrastructure (console dev / SMTP prod)
- ✅ Contact applicant email form on applicant detail
- ✅ Profile completeness indicator
- ✅ Role switching, account deletion
- ✅ Image optimisation with django-imagekit + Cropper.js
- ✅ Ban system, roster search, custom agency name
- ✅ Verification status fields on ModelProfile and Agency (admin-only)

## Pre-Phase 4 improvements (completed 11th–12th March 2026)

- ✅ Agency access to private model profiles — agency staff can view private profiles of their roster models via `model_detail`; blue banner explains "viewing as roster staff"
- ✅ Model experience level — `ModelProfile.experience_level` (amateur/experienced); migration `models_app.0005`; onboarding, edit profile, model detail sidebar, model list cards/filter, applicant detail stats
- ✅ Agency public profile link — "View Public Page" button on agency dashboard header
- ✅ Onboarding form parity with edit profile — `experience_level` and Representation section (agency dropdown + custom agency name with "other" toggle JS) added to `onboarding.html`
- ✅ "Signed" application status — `Application.Status.SIGNED` added (migration `applications.0005`); setting status to "signed" automatically adds the model to the agency roster (sets `represented_by_agency`, clears any `AgencyBan`)
- ✅ Experience level filter on agency dashboard — dropdown between Gender and Verified, filtering by `applicant_profile__experience_level`
- ✅ "Our Models" roster visibility for own-agency viewers — agency staff see all roster models (public + private); signed models see themselves even if private; everyone else gated by `is_roster_public` as before. Template condition is now `{% if roster_models is not None %}` with the logic in the view
- ✅ "You" badge on agency roster cards — same pattern as model list
- ✅ Agency detail cm/in toggle polish — button styling matches model detail; `agSetUnit('cm')` called on page load so values show " cm" suffix immediately
- ✅ Minimal `requirements.txt` added

---

## Phase 4 Steps

### ✅ 1. Agency Portfolio / Past Work Section

Agency portfolio mirrors the model portfolio post structure exactly: `AgencyPortfolioPost` (cover image + metadata) with `AgencyPortfolioAsset` items (multiple photos per post). Managed from the agency dashboard; dedicated create/edit/delete pages with Cropper.js support.

#### Models (`apps/agencies/models.py`, migration `agencies.0007`)
- `AgencyPortfolioPost`: `agency` FK, `title`, `slug`, `caption`, `cover_image`, `is_public`, timestamps
- `AgencyPortfolioAsset`: `portfolio_post` FK, `image`, `alt_text`, `display_order`
- Replaces the earlier single-image `AgencyPortfolioItem` model (deleted in migration 0007)

#### Forms (`apps/agencies/forms.py`)
- `AgencyPortfolioPostForm` (title, caption, cover_image, is_public)
- `AgencyPortfolioAssetFormset` (inline from AgencyPortfolioPost → AgencyPortfolioAsset, max 10, can_delete)

#### Views (`apps/dashboard/views.py`)
- `agency_portfolio_create` / `agency_portfolio_edit` / `agency_portfolio_delete` — gated to `can_edit_agency` staff
- `agency_dashboard` passes `portfolio_posts` and `can_edit` to template

#### URLs (`apps/dashboard/urls.py`)
```python
path("agency/portfolio/new/", views.agency_portfolio_create, name="agency-portfolio-create"),
path("agency/portfolio/<int:post_id>/edit/", views.agency_portfolio_edit, name="agency-portfolio-edit"),
path("agency/portfolio/<int:post_id>/delete/", views.agency_portfolio_delete, name="agency-portfolio-delete"),
```

#### Templates
- `templates/agencies/portfolio_form.html` — full create/edit page (cover image + additional photos formset, Add Photo / Remove JS, `data-crop` on all file inputs). Mirrors `portfolio/portfolio_form.html`.
- `templates/agencies/portfolio_confirm_delete.html` — delete confirmation page
- `templates/dashboard/agency_dashboard.html` — Portfolio section at the bottom; `+ New Post` / Edit / Delete only visible to `can_edit` staff; read-only view for other staff
- `templates/agencies/agency_detail.html` — Portfolio section visible to all; `+ Add post` link only for `can_edit_agency` staff; private posts visible to agency staff only
- Model public view (`templates/models_app/model_detail.html`) and agency public view both show `+ Add post` to owners/edit-staff

**Test:** As edit-staff, create a portfolio post with cover + 2 extra photos. Visit agency detail — posts appear. Visit as non-staff — only public posts visible. Non-edit staff see posts but no add/edit/delete buttons.

---

### ✅ 3. Toast Auto-Dismiss + Polished Messages

Currently, flash messages in `base.html` stay on screen indefinitely with no close button.

**Do:**
- In `templates/base.html`, replace the flash messages block (lines 49–61) with a version that includes:
  - A close button (`&times;`) on each toast, absolutely positioned top-right
  - Auto-dismiss after 5 seconds using JavaScript (`setTimeout` + fade-out)
  - A CSS transition for smooth fade-out: `transition: opacity 0.3s ease-out`
  - Accessible `role="alert"` on each toast
- Add the following `<script>` immediately after the messages block:
  ```javascript
  <script>
  (function() {
      document.querySelectorAll('[data-toast]').forEach(function(toast) {
          var closeBtn = toast.querySelector('[data-toast-close]');
          function dismiss() { toast.style.opacity = '0'; setTimeout(function() { toast.remove(); }, 300); }
          if (closeBtn) closeBtn.addEventListener('click', dismiss);
          setTimeout(dismiss, 5000);
      });
  })();
  </script>
  ```
- Each toast `<div>` should get `data-toast` attribute. The close button gets `data-toast-close`. Initial opacity is `1` with `transition: opacity 0.3s ease-out` inline style.

Keep the entire toast `<div>` tag and all its class attributes on a single line (or use only the `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` tags for line breaks — never split the class string across lines).

**Test:** Trigger a success message (e.g. save profile) — toast appears, fades out after 5 seconds. Click the X — toast dismisses immediately. Multiple messages stack correctly.

---

### ✅ 4. Custom Error Pages (400, 403, 404, 500)

**Do:**
- Create `templates/400.html`, `templates/403.html`, `templates/404.html`, `templates/500.html`. Each extends `base.html` and shows:
  - A centred message with the error code in large `font-display` heading
  - A brief human-friendly description
  - A "Go Home" link styled as a button
  - Use the existing stone colour palette
  - The 500 page should use minimal template logic (no database queries) in case of a server error — it can still extend `base.html` but must not rely on context variables
- Example structure for 404:
  ```html
  {% extends "base.html" %}
  {% block title %}Page Not Found — The Modelling Directory{% endblock %}
  {% block content %}
  <div class="max-w-md mx-auto px-4 py-32 text-center">
      <h1 class="font-display text-6xl font-bold text-stone-300 mb-4">404</h1>
      <p class="text-stone-600 mb-8">The page you're looking for doesn't exist or has been moved.</p>
      <a href="/" class="bg-stone-900 text-white text-sm font-medium px-6 py-2.5 rounded-lg hover:bg-stone-700 transition-colors">Go Home</a>
  </div>
  {% endblock %}
  ```
- In `modeldirectory/urls.py`, add the custom error handlers at module level (outside `urlpatterns`):
  ```python
  handler400 = "apps.core.views.error_400"
  handler403 = "apps.core.views.error_403"
  handler404 = "apps.core.views.error_404"
  handler500 = "apps.core.views.error_500"
  ```
- In `apps/core/views.py`, add the four error views. Each returns the appropriate template with the correct status code:
  ```python
  def error_400(request, exception):
      return render(request, "400.html", status=400)

  def error_403(request, exception):
      return render(request, "403.html", status=403)

  def error_404(request, exception):
      return render(request, "404.html", status=404)

  def error_500(request):
      return render(request, "500.html", status=500)
  ```
  Note: `error_500` does NOT take an `exception` parameter — Django calls it with only `request`.

**Test:** Set `DEBUG=False` temporarily, visit `/nonexistent-page/` — custom 404 page appears. Force a 500 (e.g. raise an exception in a view) — custom 500 page appears. Verify all four templates render correctly.

---

### ✅ 4b. Custom Access-Restriction Pages

HTTP error pages (403, 404) are generic. When a user hits an application-level access restriction — private profile, private roster, banned from an agency — they deserve a contextual, helpful page rather than a blank 404 or silent empty section.

#### 4b-i. Private Profile Page

Currently, visiting a private model profile raises `Http404` (in `apps/models_app/views.py` line 230–232). This pretends the profile doesn't exist. Instead, show a dedicated "private profile" page.

**Do:**
- Create `templates/models_app/model_private.html`:
  ```html
  {% extends "base.html" %}
  {% block title %}Private Profile — The Modelling Directory{% endblock %}
  {% block content %}
  <div class="max-w-md mx-auto px-4 py-32 text-center">
      <div class="w-16 h-16 bg-stone-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-stone-400"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>
      </div>
      <h1 class="font-display text-2xl font-bold text-stone-900 mb-2">This Profile is Private</h1>
      <p class="text-stone-500 mb-8">This model has chosen to keep their profile private. Only their representing agency can view it.</p>
      <a href="{% url 'model-list' %}" class="bg-stone-900 text-white text-sm font-medium px-6 py-2.5 rounded-lg hover:bg-stone-700 transition-colors">Browse Models</a>
  </div>
  {% endblock %}
  ```
- In `apps/models_app/views.py`, replace the `Http404` raise (line 230–232) with a render of the private page:
  ```python
  if not profile.is_public and not is_own_profile and not is_agency_viewer:
      return render(request, "models_app/model_private.html", status=403)
  ```

**Test:** Visit a private model's profile URL while logged out — see "This Profile is Private" page with a lock icon and "Browse Models" link. Visit while logged in as the owner — normal profile renders. Visit as the model's agency staff — normal profile renders with blue banner.

#### 4b-ii. Banned Model — Apply Block

Currently, there is **no check** for `AgencyBan` in the apply view (`apps/applications/views.py`). A model that was removed/banned by an agency can still submit new applications. This is a security gap.

**Do:**
- In `apps/applications/views.py` `apply()`, add a ban check after the duplicate guard (after line 36):
  ```python
  from apps.agencies.models import AgencyBan
  if AgencyBan.objects.filter(model_profile=profile, agency=agency).exists():
      messages.error(request, "You are unable to apply to this agency.")
      return redirect("agency-detail", slug=agency_slug)
  ```
- Also hide the "Apply" button on `agency_detail.html` when the user is banned. In `apps/agencies/views.py` `agency_detail()`, add a context variable:
  ```python
  is_banned = False
  if request.user.is_authenticated and hasattr(request.user, "model_profile"):
      from apps.agencies.models import AgencyBan
      is_banned = AgencyBan.objects.filter(
          model_profile=request.user.model_profile, agency=agency
      ).exists()
  ```
  Pass `"is_banned": is_banned` in the context dict.
- In `templates/agencies/agency_detail.html`, wrap the Apply button with `{% if not is_banned %}`. Where the button would be, show a subtle message if banned:
  ```html
  {% if is_banned %}
      <p class="text-sm text-stone-400 italic">You are not eligible to apply to this agency.</p>
  {% endif %}
  ```

**Test:** As agency staff, remove a model from the roster (creating a ban). Log in as that model, visit the agency — no Apply button, subtle "not eligible" message. Try the apply URL directly — error message, redirect back to agency detail.

#### 4b-iii. Private Roster Explanation

Currently, when `is_roster_public=False` the "Our Models" section is completely hidden with no explanation. Visitors don't know whether the agency has no models or has chosen to hide them.

**Do:**
- In `apps/agencies/views.py` `agency_detail()`, add a context flag:
  ```python
  roster_is_private = not agency.is_roster_public and not is_agency_staff
  ```
  Pass `"roster_is_private": roster_is_private` in the context dict.
- In `templates/agencies/agency_detail.html`, after the `{% if roster_models is not None %}...{% endif %}` block, add:
  ```html
  {% if roster_is_private %}
  <div class="text-center py-10">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-stone-300 mx-auto mb-3"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>
      <p class="text-stone-400 text-sm">This agency's roster is private.</p>
  </div>
  {% endif %}
  ```

**Test:** Set an agency's `is_roster_public=False`. Visit the agency as a non-staff user — see "This agency's roster is private" with a lock icon. Visit as agency staff — full roster visible as normal.

---

### ✅ 5. Empty State Polish

Audit every page for empty/zero-data scenarios and ensure they look clean and guide the user.

**Do:**
- In `templates/dashboard/model_dashboard.html`:
  - The "No applications yet" empty state (line 59) already links to agency list — keep as is
  - The "No portfolio posts yet" empty state (line 90) — add a link: `No portfolio posts yet. <a href="{% url 'portfolio-create' %}" class="text-stone-700 hover:underline">Create your first post →</a>`
- In `templates/dashboard/agency_dashboard.html`:
  - The empty applications state (line 74) is fine
  - The empty roster state (line 116) — add: `No models currently on your roster. Use the search above to add models.`
- In `templates/resources/resource_list.html`:
  - If no articles exist, ensure there's an empty state: `{% if not articles %}<div class="text-center py-20 text-stone-400"><p class="text-lg">No resources published yet.</p></div>{% endif %}`
  - Check the template to verify the variable name (it may be `articles` or `resources` — match the existing name)
- In `templates/models_app/model_detail.html`:
  - If the model has no portfolio posts and no bio, the left column can be completely empty — add a fallback: `{% if not portfolio_posts and not profile.bio %}<p class="text-stone-400 text-sm">This model hasn't added any content yet.</p>{% endif %}`
- In `templates/agencies/agency_detail.html`:
  - If no description, no requirements, no highlights, no portfolio items, and no roster — the main column is empty. Add: `{% if not agency.description and not requirements and not highlights and not portfolio_items and roster_models is none %}<p class="text-stone-400 text-sm">This agency hasn't added any details yet.</p>{% endif %}` (note: `roster_models` is `None` when not visible, so use `is none` rather than `not roster_models`)

**Test:** Create a model with no portfolio/bio — detail page shows fallback message. Create an agency with no description — detail shows fallback. Empty dashboard sections show guide text.

---

### ✅ 6. Production Deployment Prep — WhiteNoise + S3 Storage

**Do:**
- Install packages: `pipenv install whitenoise django-storages[boto3]`
- In `modeldirectory/settings/base.py`:
  - Add `"whitenoise.middleware.WhiteNoiseMiddleware"` to `MIDDLEWARE`, immediately after `SecurityMiddleware` (line 48 area). WhiteNoise must come before all other middleware except SecurityMiddleware
  - Add `STORAGES` dict placeholder (will be overridden per environment):
    ```python
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    ```
- In `modeldirectory/settings/production.py`, add:
  ```python
  # --- Static files (WhiteNoise) ---
  STORAGES = {
      "staticfiles": {
          "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
      },
      "default": {
          "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
          "OPTIONS": {
              "bucket_name": env("AWS_STORAGE_BUCKET_NAME", default=""),
              "region_name": env("AWS_S3_REGION_NAME", default="ap-south-1"),
              "access_key": env("AWS_ACCESS_KEY_ID", default=""),
              "secret_key": env("AWS_SECRET_ACCESS_KEY", default=""),
              "custom_domain": env("AWS_S3_CUSTOM_DOMAIN", default=""),
              "default_acl": None,
              "file_overwrite": False,
              "querystring_auth": True,
              "querystring_expire": 3600,
          },
      },
  }

  # --- Security ---
  SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
  ```
- In `modeldirectory/settings/development.py`, ensure `STORAGES` is NOT overridden (development keeps Django's default file-system storage for media, which is the default when no `"default"` key is set)
- In `modeldirectory/urls.py`, the `if settings.DEBUG:` block for serving media (line 38) is correct — in production, S3 serves media files directly; in development, Django serves them

**Do NOT:**
- Change any existing model `upload_to` paths — S3 storage uses the same paths
- Add `collectstatic` to the plan — that is a deploy-time command, not a code change

**Test:** Run `python manage.py collectstatic --noinput` in development (should collect to `staticfiles/` directory without errors). Verify the app starts and serves pages normally with the WhiteNoise middleware in place. In development, media uploads still save to the local `media/` directory.

---

### ✅ 7. Security Hardening

**Do:**

#### 7a. Rate Limiting
- Install: `pipenv install django-ratelimit`
- Apply `@ratelimit` decorator to abuse-prone views:
  - `apps/accounts/views.py` — `SignupView`: override `dispatch()` to check `ratelimit(key='ip', rate='5/h', method='POST')`. If limited, return a 429 response with a message
  - `apps/accounts/views.py` — `delete_account()`: add `@ratelimit(key='user', rate='3/h', method='POST')`
  - `apps/applications/views.py` — `apply()`: add `@ratelimit(key='user', rate='10/h', method='POST')`
  - `apps/dashboard/views.py` — `submit_feedback()`: add `@ratelimit(key='user', rate='30/h', method='POST')`
  - `apps/dashboard/views.py` — `search_models_for_roster()`: add `@ratelimit(key='user', rate='60/m', method='GET')`
- For the `SignupView` CBV, add the rate limit in `dispatch()`:
  ```python
  from django_ratelimit.decorators import ratelimit
  from django_ratelimit.exceptions import Ratelimited

  def dispatch(self, request, *args, **kwargs):
      if request.user.is_authenticated:
          return redirect("home")
      return super().dispatch(request, *args, **kwargs)

  @method_decorator(ratelimit(key='ip', rate='5/h', method='POST'))
  def post(self, request, *args, **kwargs):
      return super().post(request, *args, **kwargs)
  ```
- Create a `templates/429.html` error page (same style as the other error pages): "Too many requests. Please slow down and try again shortly."
- In `modeldirectory/settings/base.py`, add:
  ```python
  RATELIMIT_VIEW = "apps.core.views.error_429"
  ```
- In `apps/core/views.py`, add:
  ```python
  def error_429(request, exception=None):
      return render(request, "429.html", status=429)
  ```

#### 7b. CSRF Hardening
- In `modeldirectory/settings/base.py`, add:
  ```python
  CSRF_FAILURE_VIEW = "apps.core.views.error_403"
  ```
  This ensures CSRF failures show the styled 403 page rather than the ugly Django default.

#### 7c. Input Sanitization Audit
- Review all `TextField` and `CharField` inputs rendered with `{{ }}` in templates. Django auto-escapes by default, so no changes are needed for standard template rendering. Confirm that NO template uses `|safe` or `{% autoescape off %}` on user-supplied content. The key templates to verify:
  - `model_detail.html` — bio uses `{{ profile.bio }}` (auto-escaped, OK)
  - `agency_detail.html` — description uses `{{ agency.description }}` (auto-escaped, OK)
  - `applicant_detail.html` — cover note uses `{{ application.cover_note }}` (auto-escaped, OK)
  - `model_dashboard.html` — feedback uses `{{ app.feedback|truncatewords:25 }}` (auto-escaped, OK)
- If any `|safe` usage is found on user content, remove it

#### 7d. File Upload Size Limit
- In `modeldirectory/settings/base.py`, add:
  ```python
  FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
  DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
  ```

**Test:** Attempt to sign up more than 5 times in an hour from the same IP — rate limited. Upload a file over 10 MB — rejected. Submit a form without CSRF token — styled 403 page.

---

### ✅ 8. Performance — Query Optimization

Audit all views for N+1 queries and add `select_related` / `prefetch_related` where missing.

**Do:**
- In `apps/models_app/views.py`:
  - `model_list()`: ✅ already has `.select_related("represented_by_agency")` — no change needed
  - `model_detail()`: add `.select_related("represented_by_agency")` to the `get_object_or_404` queryset. Replace `get_object_or_404(ModelProfile, slug=slug, is_public=True)` with:
    ```python
    profile = get_object_or_404(ModelProfile.objects.select_related("represented_by_agency"), slug=slug, is_public=True)
    ```
  - `model_detail()`: add `.prefetch_related("assets")` to the portfolio_posts query if the detail page renders asset thumbnails (currently it doesn't, so skip this)
- In `apps/agencies/views.py`:
  - `agency_list()`: the queryset on line 10 is fine (no FK fields rendered per card)
  - `agency_detail()`: add `.prefetch_related("requirements", "highlights", "portfolio_items")` to avoid separate queries:
    ```python
    agency = get_object_or_404(Agency.objects.prefetch_related("requirements", "highlights", "portfolio_items"), slug=slug, is_active=True)
    ```
    Then change `requirements = agency.requirements.filter(is_current=True)` to filter in Python instead to use the prefetched cache:
    ```python
    requirements = [r for r in agency.requirements.all() if r.is_current]
    ```
  - Note: `agency_detail()` now also queries `AgencyStaff` and checks `viewer_profile.represented_by_agency_id` for roster visibility logic (added in pre-phase4 work). These are single-row lookups and don't need optimization, but keep them in mind when auditing query counts.
- In `apps/dashboard/views.py`:
  - `model_dashboard()`: the existing `select_related` calls are good. Add `.select_related("represented_by_agency")` to the profile fetch if not already present. Currently `get_object_or_404(ModelProfile, user=request.user)` — change to:
    ```python
    profile = get_object_or_404(ModelProfile.objects.select_related("represented_by_agency"), user=request.user)
    ```
  - `agency_dashboard()`: the existing `select_related("applicant_profile", "applicant_profile__user")` is good
  - `applicant_detail()`: the `application` query already has the agency from the filter. Add `select_related("applicant_profile", "applicant_profile__user")` to the application fetch:
    ```python
    application = get_object_or_404(Application.objects.select_related("applicant_profile", "applicant_profile__user"), id=application_id, agency=agency)
    ```
- In `apps/core/views.py`:
  - `landing()`: the featured agencies query is fine (no FK joins needed)
- In `apps/discovery/views.py`:
  - If the save/follow toggles do additional queries, add `select_related` as needed (these are simple toggle views — likely fine)

**Test:** Install `django-debug-toolbar` in dev and verify that list pages do not issue more than 5–7 queries. Specifically: model list with 20 models should not fire 20+ queries for agency names.

---

### ✅ 9. Caching for Public List Views

**Do:**
- In `modeldirectory/settings/base.py`, add a local-memory cache backend (sufficient for single-server deployments; swap to Redis in production if needed):
  ```python
  CACHES = {
      "default": {
          "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
      }
  }
  ```
- In `modeldirectory/settings/production.py`, override with Redis (already installed):
  ```python
  CACHES = {
      "default": {
          "BACKEND": "django.core.cache.backends.redis.RedisCache",
          "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
      }
  }
  ```
- In `apps/models_app/views.py`, cache the cities dropdown (it rarely changes):
  ```python
  from django.core.cache import cache

  # Inside model_list():
  cities = cache.get("model_cities")
  if cities is None:
      cities = list(ModelProfile.objects.filter(is_public=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
      cache.set("model_cities", cities, 300)  # 5 minutes
  ```
- In `apps/agencies/views.py`, cache the cities dropdown similarly:
  ```python
  from django.core.cache import cache

  # Inside agency_list():
  cities = cache.get("agency_cities")
  if cities is None:
      cities = list(Agency.objects.filter(is_active=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
      cache.set("agency_cities", cities, 300)
  ```
- Do NOT cache the full querysets (they depend on filters and user auth state)

**Test:** Load model list twice — second load should not query for cities. Check cache works by adding a new city in admin — old list persists for up to 5 minutes, then refreshes.

---

### ✅ 10. Navbar Mobile Menu

The navbar currently hides nav links on mobile (`hidden md:flex`). There is no hamburger menu.

**Do:**
- In `templates/partials/_navbar.html`, add a hamburger button visible only on mobile (`md:hidden`), placed before the auth section:
  ```html
  <button type="button" id="mobile-menu-btn" class="md:hidden text-stone-600 hover:text-stone-900" aria-label="Menu">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
  </button>
  ```
- Below the main `<div class="flex items-center justify-between h-16">` container, add a collapsible mobile menu `<div>`:
  ```html
  <div id="mobile-menu" class="hidden md:hidden border-t border-stone-200 pb-3 pt-2">
      <a href="{% url 'agency-list' %}" class="block px-4 py-2 text-sm text-stone-600 hover:bg-stone-50">Agencies</a>
      <a href="{% url 'model-list' %}" class="block px-4 py-2 text-sm text-stone-600 hover:bg-stone-50">Models</a>
      <a href="{% url 'resource-list' %}" class="block px-4 py-2 text-sm text-stone-600 hover:bg-stone-50">Resources</a>
      {% if user.is_authenticated %}
      <a href="{% url 'dashboard' %}" class="block px-4 py-2 text-sm text-stone-600 hover:bg-stone-50">Dashboard</a>
      {% endif %}
  </div>
  ```
- Add toggle script:
  ```javascript
  <script>
  document.getElementById('mobile-menu-btn').addEventListener('click', function() {
      document.getElementById('mobile-menu').classList.toggle('hidden');
  });
  </script>
  ```
- Place the hamburger button between the nav links div and the auth div, inside the `h-16` flex container. The mobile menu div goes after the `h-16` container but still inside the `<nav>` tag.

**Test:** Resize browser to mobile width — hamburger appears, links hidden. Click hamburger — menu drops down with Agencies, Models, Resources links. Click again — menu collapses.

---

### ✅ 11. Role Switch in Navbar - DO NOT ADD. instead, just remove all trace of the role switch functionality - only admin should be able to do it.

Phase 3 added the `switch_role` view but no UI in the navbar. Add it.

**Do:**
- In `templates/partials/_navbar.html`, in the authenticated user section (between the Dashboard link and the Logout form), add a role-switch form:
  ```html
  {% if user.is_model_user %}
  <form method="post" action="{% url 'switch-role' %}" class="hidden sm:inline">{% csrf_token %}<input type="hidden" name="role" value="AGENCY_STAFF"><button type="submit" class="text-xs text-stone-400 hover:text-stone-700 transition-colors">Switch to Agency</button></form>
  {% elif user.is_agency_staff %}
  <form method="post" action="{% url 'switch-role' %}" class="hidden sm:inline">{% csrf_token %}<input type="hidden" name="role" value="MODEL"><button type="submit" class="text-xs text-stone-400 hover:text-stone-700 transition-colors">Switch to Model</button></form>
  {% endif %}
  ```
- Also add the role-switch option in the mobile menu (inside the `{% if user.is_authenticated %}` block):
  ```html
  {% if user.is_model_user %}
  <form method="post" action="{% url 'switch-role' %}" class="px-4 py-2">{% csrf_token %}<input type="hidden" name="role" value="AGENCY_STAFF"><button type="submit" class="text-sm text-stone-500 hover:text-stone-700">Switch to Agency</button></form>
  {% elif user.is_agency_staff %}
  <form method="post" action="{% url 'switch-role' %}" class="px-4 py-2">{% csrf_token %}<input type="hidden" name="role" value="MODEL"><button type="submit" class="text-sm text-stone-500 hover:text-stone-700">Switch to Model</button></form>
  {% endif %}
  ```

**Test:** Log in as a MODEL user — "Switch to Agency" link visible in navbar. Click it — if linked to an agency, redirects to agency dashboard; if not, error message. Switch back — model dashboard loads.

---

### ✅ 12. Agency Verification Badge Parity

Agency already has a verification badge on `agency_detail.html` (line 37–41). Extend to the list view.

**Do:**
- In `templates/agencies/agency_list.html`, inside the card's `<div class="p-5">` block (line 71), add a verified badge next to the agency name (same location as the model list badge), checking `agency.verification_status == "verified"`:
  ```
  <div class="flex items-center gap-1.5">
      {% if agency.logo %}<img ...>{% endif %}
      <h2 class="font-semibold text-stone-900 text-sm leading-tight">{{ agency.name }}</h2>
      {% if agency.verification_status == "verified" %}<span class="flex-shrink-0" title="Verified"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 text-emerald-500"><path fill-rule="evenodd" d="M8.603 3.799A4.49 4.49 0 0 1 12 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 0 1 3.498 1.307 4.491 4.491 0 0 1 1.307 3.497A4.49 4.49 0 0 1 21.75 12a4.49 4.49 0 0 1-1.549 3.397 4.491 4.491 0 0 1-1.307 3.497 4.491 4.491 0 0 1-3.497 1.307A4.49 4.49 0 0 1 12 21.75a4.49 4.49 0 0 1-3.397-1.549 4.49 4.49 0 0 1-3.498-1.307 4.491 4.491 0 0 1-1.307-3.497A4.49 4.49 0 0 1 2.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 0 1 1.307-3.497 4.49 4.49 0 0 1 3.497-1.307Zm7.007 6.387a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clip-rule="evenodd" /></svg></span>{% endif %}
  </div>
  ```
  Keep the `{% if %}...{% endif %}` block on a single line.
- In `templates/core/landing.html`, add the same badge to the featured agency cards (inside the `<div class="flex items-center gap-3 mb-2">` block, after the agency name `<h3>`, line 96), using `w-4 h-4`

**Test:** Set an agency's `verification_status` to `verified` in admin. Browse agency list and landing page — badge appears next to verified agency names.

---

## Testing Plan

Run these yourself after each step:

| Step | Command / Action | Expected |
|------|-----------------|----------|
| 1 | As agency staff, add portfolio item → view agency detail | Portfolio grid appears above "Our Models"; delete removes it |
| 2 | Load applicant detail, hit old `/contact/` URL | No "Send Email" card; old URL returns 404 |
| 3 | Trigger a message → wait 5 seconds | Toast fades out automatically; X closes early |
| 4 | Set `DEBUG=False`, visit `/nonexistent/` | Custom 404 page with "Go Home" button |
| 4b-i | Visit a private model's profile while logged out | "This Profile is Private" page with lock icon |
| 4b-ii | As a banned model, visit the agency that banned you | No Apply button; "not eligible" message shown |
| 4b-ii | As a banned model, try the apply URL directly | Error message, redirect to agency detail |
| 4b-iii | Visit agency with `is_roster_public=False` as non-staff | "This agency's roster is private" message |
| 5 | Model with no portfolio → view detail page | "This model hasn't added any content yet." |
| 6 | `python manage.py collectstatic --noinput` | Completes without errors; files in `staticfiles/` |
| 7 | Sign up 6 times in 1 hour from same IP | 6th attempt shows 429 page |
| 8 | Load model list with 20+ models (check queries) | No N+1 — agency names fetched in one query |
| 9 | Load model list twice, check second load queries | Cities dropdown served from cache |
| 10 | Resize to mobile → click hamburger | Menu opens/closes with navigation links |
| 11 | Set agency verified in admin → browse agency list | Emerald badge on card |

---

## What's Done After Phase 4

- ✅ Agency portfolio (mirrors model portfolio): `AgencyPortfolioPost` + `AgencyPortfolioAsset`, dedicated create/edit/delete pages with Cropper.js, managed from agency dashboard, `+ Add post` on public views for edit-staff
- ✅ Send-email form removed from applicant detail
- ✅ Model verification badges across list, detail, applicant review, and agency inbox
- ✅ Agency verification badges across list and landing page (parity with detail page)
- ✅ Toast messages auto-dismiss with close button
- ✅ Custom error pages (400, 403, 404, 429, 500)
- ✅ Custom access-restriction pages (private profile, banned applicant, private roster)
- ✅ AgencyBan enforcement on the apply view (security fix)
- ✅ Empty state polish across all views
- ✅ WhiteNoise for static files in production
- ✅ S3 media storage configuration for production
- ✅ Production security settings (SSL, HSTS, secure cookies)
- ✅ Rate limiting on signup, applications, feedback, search, account deletion
- ✅ CSRF failure shows styled error page
- ✅ File upload size limits
- ✅ Query optimisation with select_related / prefetch_related audit
- ✅ Caching for city dropdowns
- ✅ Mobile hamburger menu
- ✅ Role switch accessible from navbar
- ✅ Onboarding form parity with edit profile (experience level, representation section)
- ✅ "Signed" application status with automatic roster addition
- ✅ Experience level filter on agency dashboard
- ✅ "Our Models" roster visible to own-agency staff (all models) and signed models (themselves)
- ✅ "You" badge on agency roster cards
- ✅ Consistent cm/in toggle styling and initial unit display across all pages

## Future improvements
- Mobile interface testing
- Live messaging on app linkedin style. Only agency staff can initiate contact, but then they can message back and forth with applicants in real time. Would require a messaging model, inbox UI, and notification system. Models should be able to message request each other. 
- Agencies and models can pull portfolios from instagram. They can connect their IG account and select 6 posts to show on their profile. This requires IG API integration, a new model to store connected accounts and selected posts, and UI in the dashboard (agency - edit, model - onboarding and edit) to manage the connection and post selection. Also this only works for business/creator accounts, so we need to handle the case where a user tries to connect a personal account (error message, instructions to switch to business/creator). However, the visual style of the portfolio grid and cards would be the same as the existing portfolios. The ig posts would not be embedded with the native IG widget, but rather we would fetch the post image and caption and display them in our own card design for consistency with uploaded portfolio items. will also need to change limit on portfolio carousel items to 20 images, and portfolio will need to be able to handle video.
- Resources section fleshing out
- Email verification flow (is_verified_email field exists but unused)
- Model/agency verification workflows
- Social features on portfolios (likes, comments)



