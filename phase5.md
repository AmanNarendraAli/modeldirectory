# The Modelling Directory — Phase 5 Workplan

## Goal

Ship a production-ready, mobile-polished platform. Phase 5 covers three pillars: (1) mobile interface refinement across all pages, (2) full deployment to Render + Supabase + Cloudflare R2 with production configuration, and (3) end-to-end testing before and after deployment.

---

## Prerequisites (from Phase 4)

- ✅ Agency + model portfolio with carousel, create/edit/delete, Cropper.js
- ✅ Toast auto-dismiss, custom error pages (400/403/404/429/500)
- ✅ Access-restriction pages (private profile, banned applicant, private roster)
- ✅ WhiteNoise for static files, S3 media storage config
- ✅ Production security settings (SSL, HSTS, secure cookies)
- ✅ Rate limiting, CSRF hardening, file upload limits
- ✅ Query optimisation, city dropdown caching
- ✅ Mobile hamburger menu, navbar polish
- ✅ Verification badges on all list/detail views

---

## Phase 5 Steps

### ✅ 1. Mobile Interface Refinement

Audit and fix all mobile-unfriendly layouts. Test at 375px (iPhone SE) and 390px (iPhone 14) viewports.

#### 1a. Dashboard Portfolio Grids

The portfolio grid in `model_dashboard.html` uses fixed `grid-cols-3` with no responsive breakpoint — cramped on small screens.

**Do:**
- In `templates/dashboard/model_dashboard.html`, change the portfolio grid from:
  ```html
  <div class="grid grid-cols-3 gap-3">
  ```
  to:
  ```html
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
  ```
- In `templates/dashboard/agency_dashboard.html`, apply the same change to the portfolio grid if it uses fixed `grid-cols-3`.

**Test:** Resize to 375px — portfolio cards show 2 per row. At 640px+ — 3 per row.

#### 1b. Model List Filter Form

The filter bar in `model_list.html` uses `flex-nowrap` with fixed-width inputs (`w-28`) and `min-w-[130px]` measurement sliders. On phones < 400px, elements overflow or get cramped.

**Do:**
- Wrap the main filter row in `overflow-x-auto` as a safety fallback so it scrolls rather than overflowing the page
- Change the search input from `w-28` to `w-24 sm:w-28` for slightly more breathing room
- Verify the "More Filters" expanded panel stacks properly on mobile (it already uses `flex-wrap`, but confirm)
- Test that measurement range sliders are usable on touch screens at 375px

**Test:** Open model list at 375px width. Filters should not cause horizontal page overflow. Expanded filters should wrap cleanly. Sliders should be draggable on touch.

#### 1c. Agency List Filter Dropdowns

The multiselect dropdowns on `agency_list.html` use absolute positioning with `min-width:160px`. On narrow screens, dropdowns can extend beyond the viewport edge.

**Do:**
- Add `max-width: calc(100vw - 2rem)` to the dropdown panels so they don't overflow the screen
- Ensure dropdown z-index is high enough to sit above other content on mobile

**Test:** Open agency list at 375px. Open a filter dropdown — it should not cause horizontal scrolling.

#### 1d. Form Layouts on Small Screens

Several forms use `grid-cols-2` for side-by-side fields. While generally fine, some label+input combos get cramped below 375px.

**Do:**
- In `templates/portfolio/portfolio_form.html` and `templates/agencies/portfolio_form.html`, change the alt text / order grid from:
  ```html
  <div class="grid grid-cols-2 gap-3">
  ```
  to:
  ```html
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
  ```
  (This applies to both the inline asset forms and the `<template>` for new slots.)
- In `templates/models_app/edit_profile.html` and `templates/models_app/onboarding.html`, verify measurement grids (`grid-cols-2 sm:grid-cols-3`) are usable at 375px. If any field labels truncate, reduce to `grid-cols-1 sm:grid-cols-2`.

**Test:** Open portfolio create form at 375px — alt text and order fields stack vertically. Edit profile measurements are readable and tappable.

#### 1e. Portfolio Detail Carousel on Mobile

The carousel uses `height:70vh` which is good, but prev/next buttons may be hard to tap on mobile.

**Do:**
- Increase touch target size on carousel buttons from `w-10 h-10` to `w-12 h-12` on mobile (use `w-10 h-10 sm:w-10 sm:h-10` or just keep `w-12 h-12` universally — the difference is minimal)
- Verify swipe gesture works smoothly (threshold is 40px, which is appropriate for mobile)
- Test that dots at the bottom are tappable (current `w-2 h-2` is small — consider `w-2.5 h-2.5` with adequate gap)

**Test:** Open a portfolio post with 3+ images on a phone. Swipe left/right — slides change. Tap dots — slides change. Tap prev/next — responsive.

#### 1f. Touch Target Audit

Ensure all interactive elements meet the minimum 44x44px touch target guideline.

**Do:**
- Review all buttons and links on key pages at mobile width
- Particular areas to check:
  - Edit/Delete overlay buttons on dashboard portfolio cards (currently `text-xs px-1.5 py-0.5` — very small)
  - Filter chips on model list
  - Carousel dots
  - Toast close button
- For hover-only elements (like Edit/Del overlays on dashboard portfolio cards), add a mobile alternative since hover doesn't work on touch screens. Options:
  - Show Edit/Del buttons always on mobile: `hidden group-hover:flex md:hidden flex md:group-hover:flex` → shows always on mobile, hover-only on desktop
  - Or: tap card to navigate, long-press for edit (more complex — skip for now)

**Test:** Use Chrome DevTools touch simulation. All buttons should be easily tappable without accidental presses.

---

### 2. Deployment — Render + Supabase + Cloudflare R2

#### 2a. What You (the developer) Need to Do First

These are manual steps that require account creation and credentials — Claude cannot do these for you.

**Supabase (Postgres database):**
1. Go to supabase.com and create a free account
2. Create a new project (pick a region close to your users — e.g., Mumbai `ap-south-1` for India)
3. Go to Settings → Database → Connection string → URI
4. Copy the connection string — it looks like: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
5. Note: use the **pooler** connection string (port 6543), not the direct connection (port 5432) — this works better with Render's serverless model

**Cloudflare R2 (media storage):**
1. Go to dash.cloudflare.com → R2 Object Storage
2. Create a bucket (e.g., `modelling-directory-media`)
3. Go to R2 → Manage R2 API Tokens → Create API Token
4. Select "Object Read & Write" permissions for your bucket
5. Copy: Access Key ID, Secret Access Key, and your Account ID
6. Your S3-compatible endpoint will be: `https://<account-id>.r2.cloudflarestorage.com`
7. Optional: set up a custom domain or public bucket URL for serving images (R2 → bucket → Settings → Public access). The public URL will be like `https://pub-[hash].r2.dev` or your custom domain

**Render (app hosting):**
1. Go to render.com and create a free account
2. Connect your GitHub account
3. You'll create the web service in step 2d after the code is ready

**Collect all these values — you'll need them as environment variables:**
```
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_STORAGE_BUCKET_NAME=modelling-directory-media
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_S3_CUSTOM_DOMAIN=<your-r2-public-url-without-https>
SECRET_KEY=<generate-a-new-one>
ALLOWED_HOSTS=<your-app>.onrender.com
```

---

#### ✅ 2b. Production Settings (Claude does this)

Update `modeldirectory/settings/production.py` to read all config from environment variables.

**Do:**
- Install `dj-database-url` for parsing `DATABASE_URL`:
  ```
  pipenv install dj-database-url
  ```
- Update `production.py`:
  ```python
  import os
  import dj_database_url
  from .base import *  # noqa

  DEBUG = False

  SECRET_KEY = os.environ["SECRET_KEY"]
  ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

  # Database — Supabase Postgres via DATABASE_URL
  DATABASES = {
      "default": dj_database_url.config(
          default=os.environ.get("DATABASE_URL"),
          conn_max_age=600,
          conn_health_checks=True,
          ssl_require=True,
      )
  }

  # Static files — WhiteNoise (already in base.py middleware)
  STORAGES = {
      "staticfiles": {
          "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
      },
      "default": {
          "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
          "OPTIONS": {
              "bucket_name": os.environ.get("AWS_STORAGE_BUCKET_NAME", ""),
              "access_key": os.environ.get("AWS_ACCESS_KEY_ID", ""),
              "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
              "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL", ""),
              "custom_domain": os.environ.get("AWS_S3_CUSTOM_DOMAIN", ""),
              "default_acl": None,
              "file_overwrite": False,
              "querystring_auth": False,
          },
      },
  }

  # Security
  SECURE_SSL_REDIRECT = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

  # Email — use a real SMTP service in production
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
  EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
  EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
  EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
  DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@modellingdirectory.com")

  # Logging
  LOGGING = {
      "version": 1,
      "disable_existing_loggers": False,
      "handlers": {
          "console": {
              "class": "logging.StreamHandler",
          },
      },
      "root": {
          "handlers": ["console"],
          "level": "WARNING",
      },
  }
  ```

**Test:** Run `DJANGO_SETTINGS_MODULE=modeldirectory.settings.production python manage.py check --deploy` (will warn about missing env vars — that's expected locally).

---

#### ✅ 2c. Deployment Files (Claude does this)

Create the files Render needs to build and run the app.

**`requirements.txt`** — Update to include all production dependencies:
- Ensure `dj-database-url`, `gunicorn`, `psycopg2-binary`, `whitenoise`, `django-storages`, `boto3` are listed
- Generate from Pipfile: `pipenv requirements > requirements.txt`

**`render.yaml`** (optional — Render Blueprint for one-click deploy):
```yaml
services:
  - type: web
    name: modelling-directory
    runtime: python
    buildCommand: pip install -r requirements.txt && python modeldirectory/manage.py collectstatic --noinput && python modeldirectory/manage.py migrate
    startCommand: cd modeldirectory && gunicorn modeldirectory.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: modeldirectory.settings.production
      - key: PYTHON_VERSION
        value: "3.11"
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        sync: false
      - key: ALLOWED_HOSTS
        sync: false
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_STORAGE_BUCKET_NAME
        sync: false
      - key: AWS_S3_ENDPOINT_URL
        sync: false
      - key: AWS_S3_CUSTOM_DOMAIN
        sync: false
```

**`Procfile`** (alternative to render.yaml):
```
web: cd modeldirectory && gunicorn modeldirectory.wsgi:application --bind 0.0.0.0:$PORT
```

**`runtime.txt`**:
```
python-3.11.7
```

**Test:** Run `gunicorn modeldirectory.wsgi:application --bind 0.0.0.0:8000` locally to verify gunicorn starts without import errors.

---

#### 2d. Deploy to Render (you do this)

1. Push your code to GitHub (main branch)
2. On Render dashboard → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt && cd modeldirectory && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command:** `cd modeldirectory && gunicorn modeldirectory.wsgi:application --bind 0.0.0.0:$PORT`
   - **Environment:** Python 3
5. Add environment variables (all from section 2a):
   - `DJANGO_SETTINGS_MODULE` = `modeldirectory.settings.production`
   - `SECRET_KEY` = (generate one: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `DATABASE_URL` = (from Supabase)
   - `ALLOWED_HOSTS` = `<your-app>.onrender.com`
   - `AWS_ACCESS_KEY_ID` = (from R2)
   - `AWS_SECRET_ACCESS_KEY` = (from R2)
   - `AWS_STORAGE_BUCKET_NAME` = (your bucket name)
   - `AWS_S3_ENDPOINT_URL` = `https://<account-id>.r2.cloudflarestorage.com`
   - `AWS_S3_CUSTOM_DOMAIN` = (your R2 public URL, without `https://`)
6. Click Deploy

**After first deploy:**
- Render runs the build command which includes `migrate` — this creates all tables in Supabase
- Verify the site loads at `https://<your-app>.onrender.com`

---

#### 2e. Create Site Admin — CRITICAL (you do this)

**The app will not function without a superuser.** Verification badges, agency activation, bans, resource publishing, and all admin-panel operations require a staff/superuser account.

1. On Render → your service → Shell tab
2. Run:
   ```bash
   cd modeldirectory && python manage.py createsuperuser
   ```
3. Enter a username, email, and strong password
4. Verify by visiting `https://<your-app>.onrender.com/admin/` and logging in
5. From the admin panel, you can now:
   - Activate agencies (`is_active = True`)
   - Set verification status on models and agencies
   - Manage bans, applications, and all other data
   - Publish resources/articles

**Without this step, no agencies can be activated and no content can be moderated.**

---

#### 2f. Migrate Local Data to Production (optional, you do this)

**Note:** If you go with Option A (fresh start), you still need the superuser from step 2e above.

If you want to move your dev data to production:

**Option A — Fresh start (recommended):**
- Just create a new superuser and re-add content through the UI
- Upload images will go to R2 automatically

**Option B — Dump and restore:**
```bash
# Local: dump data (excluding contenttypes, auth.permission to avoid conflicts)
cd modeldirectory
python manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 > datadump.json

# Production (via Render Shell):
cd modeldirectory
python manage.py loaddata datadump.json
```
- Note: This won't migrate media files. You'd need to manually upload them to R2 or use `rclone` to sync your local `media/` folder to the R2 bucket.

---

#### 2g. Custom Domain (optional, you do this)

1. On Render → your service → Settings → Custom Domains → Add your domain
2. Update DNS (CNAME to `<your-app>.onrender.com`)
3. Update `ALLOWED_HOSTS` env var to include your custom domain
4. Render provides free SSL via Let's Encrypt

---

### 3. Testing Plan

#### 3a. Pre-Deployment Testing (local)

Run these before pushing to production:

| Area | Test | How | Expected |
|------|------|-----|----------|
| Mobile — Dashboard | Open model dashboard at 375px | Chrome DevTools → responsive | Portfolio grid shows 2 cols, no overflow |
| Mobile — Model List | Open model list at 375px, expand filters | DevTools | Filters wrap, no horizontal scroll |
| Mobile — Agency List | Open agency list at 375px, open dropdown | DevTools | Dropdown doesn't overflow viewport |
| Mobile — Portfolio Form | Open portfolio create at 375px | DevTools | Alt text / order fields stack vertically |
| Mobile — Carousel | Open portfolio detail at 375px, swipe | DevTools touch simulation | Slides change, dots/buttons tappable |
| Mobile — Navbar | Open any page at 375px, tap hamburger | DevTools | Menu opens with all nav links |
| Mobile — Onboarding | Open onboarding at 375px | DevTools | All fields accessible, no truncation |
| Auth — Signup | Create new account | Browser | Redirects to onboarding |
| Auth — Login/Logout | Log in, log out | Browser | Correct redirects |
| Portfolio — Create | Create post with cover + 2 assets | Browser | Post appears on dashboard + public page |
| Portfolio — Edit | Edit post title + replace an image | Browser | Changes saved, image updated |
| Portfolio — Delete | Delete a post | Browser | Post removed, redirected to dashboard |
| Agency — Portfolio | Same create/edit/delete as above for agency | Browser | Works identically to model portfolio |
| Permissions — Private | Set model profile to private, visit as stranger | Browser | "Private Profile" page shown |
| Permissions — Banned | Ban a model, visit agency as that model | Browser | No apply button, "not eligible" message |
| Permissions — Agency staff | Visit agency as non-edit staff | Browser | See posts, no add/edit/delete buttons |
| Error pages | Visit `/nonexistent/` with DEBUG=False | Browser | Custom 404 page |
| Rate limit | Submit signup form 6 times rapidly | Browser | 429 page on 6th attempt |
| Toast | Save profile | Browser | Toast appears, auto-dismisses in 5s |
| Static files | `python manage.py collectstatic --noinput` | Terminal | Completes without errors |

#### 3b. Post-Deployment Testing (production)

Run these after deploying to Render:

| Area | Test | Expected |
|------|------|----------|
| Site loads | Visit `https://<app>.onrender.com` | Landing page renders with styles |
| Static files | Check CSS/JS load (no 404s in network tab) | All assets served by WhiteNoise |
| Media upload | Upload a profile image | Image saved to R2, displays correctly |
| Media display | Visit a profile with images | Images load from R2 CDN URL |
| HTTPS | Visit HTTP URL | Redirects to HTTPS |
| Database | Create an account, log in | Data persisted in Supabase |
| Admin | Visit `/admin/`, log in as superuser | Admin panel works |
| Error pages | Visit `/nonexistent/` | Custom 404 page (not Django debug page) |
| Mobile | Visit on actual phone | Full mobile experience works |
| Cold start | Wait 15+ min, visit site | Site wakes up (Render free tier sleeps) |
| Image cropping | Upload + crop an image | Cropped image saved to R2 correctly |
| Email | Trigger an email action (e.g., application) | Email sends (or logs if no SMTP configured) |

#### 3c. Cross-Browser Testing

Test on:
- Chrome (desktop + mobile)
- Safari (iOS — critical for Indian market)
- Firefox (desktop)
- Samsung Internet (popular on Android in India)

Key things to verify:
- Cropper.js works on all browsers
- Carousel touch/swipe works on iOS Safari
- CSS backdrop-filter / blur effects render (used in navbar)
- File input styling renders acceptably

---

## Future Improvements

These items are carried forward from Phase 4 and are not covered by Phase 5:

- **Live messaging (LinkedIn-style):** Agency staff can initiate contact, then back-and-forth messaging with applicants in real time. Models can message-request each other. Requires a messaging model, inbox UI, and notification system (WebSocket or polling).

- **Instagram portfolio integration:** Agencies and models can connect their IG business/creator account and select 6 posts to show on their profile. Requires IG API integration, a model to store connected accounts and selected posts, and dashboard UI to manage the connection. Only works for business/creator accounts — handle personal account error gracefully. IG posts displayed in our own card design (not native embed) for consistency. Also increase portfolio carousel limit to 20 images and add video support to portfolios.

- **Resources section fleshing out:** Expand the resources/articles area with categories, search, richer content.

- **Email verification flow:** `is_verified_email` field exists but is unused. Add email verification on signup with confirmation link.

- **Model/agency verification workflows:** Currently verification is admin-only toggle. Build a request → review → approve/reject flow with notifications.

- **Social features on portfolios:** Likes, comments, share functionality on portfolio posts.

- **Email service for production:** Configure a proper transactional email service (e.g., Resend, Postmark, or Gmail SMTP) for application notifications, password resets, and future email verification.

- **Redis cache for production:** The production settings reference Redis for caching (`REDIS_URL`). If needed, add a Redis instance (Render offers Redis, or use Upstash free tier) and set the `REDIS_URL` env var. Until then, caching falls back to local memory (resets on each deploy).
