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

---

## Phase 4 Steps

### 1. Agency Portfolio / Past Work Section

Add a portfolio/past work showcase to the agency detail page, displayed above the "Our Models" roster section. This gives agencies a visual way to show off campaigns, editorials, and other work they've done.

#### 1a. Model

**Do:**
- In `apps/agencies/models.py`, add a new `AgencyPortfolioItem` model:
  ```python
  class AgencyPortfolioItem(models.Model):
      agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="portfolio_items")
      title = models.CharField(max_length=255)
      image = models.ImageField(upload_to="agencies/portfolio/")
      image_thumbnail = ImageSpecField(source="image", processors=[ResizeToFill(400, 400)], format="WEBP", options={"quality": 80})
      image_display = ImageSpecField(source="image", processors=[ResizeToFit(1200, 1200)], format="WEBP", options={"quality": 85})
      caption = models.TextField(blank=True)
      credit = models.CharField(max_length=255, blank=True, help_text="e.g. Photographer, brand, or campaign name")
      display_order = models.PositiveSmallIntegerField(default=0)
      created_at = models.DateTimeField(auto_now_add=True)

      class Meta:
          ordering = ["display_order", "-created_at"]

      def __str__(self):
          return f"{self.agency.name} — {self.title}"
  ```
- Run `python manage.py makemigrations agencies` and `python manage.py migrate`
- Register the model in `apps/agencies/admin.py` as an inline on `AgencyAdmin` (or standalone)

#### 1b. View

**Do:**
- In `apps/agencies/views.py` `agency_detail()`, fetch portfolio items and pass them to context:
  ```python
  portfolio_items = agency.portfolio_items.all()
  ```
  Add `"portfolio_items": portfolio_items,` to the context dict.

#### 1c. Template — Agency Detail

**Do:**
- In `templates/agencies/agency_detail.html`, add a "Portfolio" section in the main content column (`lg:col-span-2`), between the Highlights section and the "Our Models" roster section (i.e. before `{% if agency.is_roster_public %}`):
  ```html
  {% if portfolio_items %}
      <div>
          <h2 class="font-display text-xl font-bold text-stone-900 mb-4">Portfolio</h2>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {% for item in portfolio_items %}
                  <div class="group aspect-square bg-stone-100 rounded-lg overflow-hidden relative">
                      <img src="{{ item.image.url }}" alt="{{ item.title }}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" data-lightbox="{{ item.image.url }}" data-lightbox-alt="{{ item.title }}">
                      <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                          <p class="text-white text-sm font-medium truncate">{{ item.title }}</p>
                          {% if item.credit %}<p class="text-white/70 text-xs truncate">{{ item.credit }}</p>{% endif %}
                      </div>
                  </div>
              {% endfor %}
          </div>
      </div>
  {% endif %}
  ```

#### 1d. Dashboard Management

**Do:**
- In `apps/agencies/forms.py`, add an `AgencyPortfolioItemForm`:
  ```python
  class AgencyPortfolioItemForm(forms.ModelForm):
      class Meta:
          model = AgencyPortfolioItem
          fields = ["title", "image", "caption", "credit", "display_order"]
  ```
- In `apps/dashboard/views.py`, add views for adding and deleting portfolio items (follow the same pattern used for highlights management — agency staff with `can_edit_agency` permission):
  - `add_portfolio_item(request, agency_slug)` — handles form submission, saves with `item.agency = agency`
  - `delete_portfolio_item(request, item_id)` — deletes the item (POST only, verify ownership)
- In `apps/dashboard/urls.py`, add URL patterns:
  ```python
  path("agency/portfolio/add/", views.add_portfolio_item, name="agency-portfolio-add"),
  path("agency/portfolio/<int:item_id>/delete/", views.delete_portfolio_item, name="agency-portfolio-delete"),
  ```
- In `templates/dashboard/edit_agency.html`, add a "Portfolio" management section (similar to highlights management) where staff can see existing items, add new ones, and delete them. Include image preview thumbnails for existing items.

**Test:** As agency staff, add a portfolio item with an image, title, and credit. Visit the agency detail page — portfolio grid appears above "Our Models". Delete the item — it disappears. Agency with no portfolio items — section is hidden.

---

### 2. Remove Send Email Form

The "Send Email" card on the applicant detail page and its supporting backend code should be removed entirely.

**Do:**
- In `templates/dashboard/applicant_detail.html`, delete the entire "Send Email" `<div>` block (lines 149–165 — the card containing `contact_form.subject`, `contact_form.body`, and the "Send Email" button)
- In `apps/dashboard/views.py`:
  - Remove the `ContactApplicantForm` import from line 11
  - Remove `contact_form = ContactApplicantForm()` from `applicant_detail()` (line 149)
  - Remove `"contact_form": contact_form,` from the context dict (line 158)
  - Delete the entire `contact_applicant()` view (lines 208–233)
  - Remove the `from django.core.mail import send_mail` import (line 5) and `from django.conf import settings as django_settings` import (line 6) — neither is used elsewhere in this file
- In `apps/dashboard/urls.py`, delete the `contact-applicant` URL pattern (line 11)
- In `apps/applications/forms.py`, delete the `ContactApplicantForm` class (lines 37–51)
- In `apps/core/emails.py`, delete the `send_contact_email` function if it exists (it was planned in Phase 3 step 5 but the actual implementation used `send_mail` directly — verify whether a standalone function exists before deleting)

**Test:** Load applicant detail as agency staff — no "Send Email" card visible. Hit the old URL `/dashboard/applications/1/contact/` — returns 404. Server starts without import errors.

---

### 3. Toast Auto-Dismiss + Polished Messages

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

### 4. Custom Error Pages (400, 403, 404, 500)

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

### 5. Empty State Polish

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
  - If no description, no requirements, no highlights, no portfolio items, and no roster — the main column is empty. Add: `{% if not agency.description and not requirements and not highlights and not portfolio_items and not roster_models %}<p class="text-stone-400 text-sm">This agency hasn't added any details yet.</p>{% endif %}`

**Test:** Create a model with no portfolio/bio — detail page shows fallback message. Create an agency with no description — detail shows fallback. Empty dashboard sections show guide text.

---

### 6. Production Deployment Prep — WhiteNoise + S3 Storage

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

### 7. Security Hardening

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

### 8. Performance — Query Optimization

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

### 9. Caching for Public List Views

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

### 10. Navbar Mobile Menu

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

### 11. Role Switch in Navbar

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

### 12. Agency Verification Badge Parity

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
| 5 | Model with no portfolio → view detail page | "This model hasn't added any content yet." |
| 6 | `python manage.py collectstatic --noinput` | Completes without errors; files in `staticfiles/` |
| 7 | Sign up 6 times in 1 hour from same IP | 6th attempt shows 429 page |
| 8 | Load model list with 20+ models (check queries) | No N+1 — agency names fetched in one query |
| 9 | Load model list twice, check second load queries | Cities dropdown served from cache |
| 10 | Resize to mobile → click hamburger | Menu opens/closes with navigation links |
| 11 | As MODEL, click "Switch to Agency" in navbar | Redirects to agency dashboard (or shows error) |
| 12 | Set agency verified in admin → browse agency list | Emerald badge on card |

---

## What's Done After Phase 4

- ✅ Agency portfolio / past work showcase on detail page with dashboard management
- ✅ Send-email form removed from applicant detail
- ✅ Model verification badges across list, detail, applicant review, and agency inbox
- ✅ Agency verification badges across list and landing page (parity with detail page)
- ✅ Toast messages auto-dismiss with close button
- ✅ Custom error pages (400, 403, 404, 429, 500)
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

## Future improvements
- Mobile interface testing
- Live messaging on app linkedin style. Only agency staff can initiate contact, but then they can message back and forth with applicants in real time. Would require a messaging model, inbox UI, and notification system.
- Resources section fleshing out
- Email verification flow (is_verified_email field exists but unused)
- Model/agency verification workflows
- In-platform messaging between agencies and models
- Social features on portfolios (likes, comments)
