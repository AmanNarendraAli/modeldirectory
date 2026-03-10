# The Modelling Directory — Phase 2 Workplan

## Goal

Build all public-facing pages, authenticated user flows, and dashboards. By end of Phase 2 the platform is functionally usable end-to-end: models can sign up, complete onboarding, build a portfolio, discover agencies, apply — and agency staff can review applications from a dashboard. Templates use Tailwind CSS with a shared base layout.

---

## Prerequisites (from Phase 1)

- ✅ Project structure, split settings, env vars, Docker Postgres
- ✅ Custom User model (email login, roles)
- ✅ All core data models migrated (Agency, ModelProfile, PortfolioPost, Application, etc.)
- ✅ Full admin interface
- ✅ Media upload working in dev
- ✅ Basic login / logout / signup
- ✅ Stub landing page

---

## Phase 2 Steps

### 1. Template System + Tailwind CSS + Static Pipeline

**Do:**
- Install Tailwind CSS (via `django-tailwind` or standalone CLI — pick one approach and stick with it)
- Create `templates/base.html` with: HTML head (meta, Tailwind stylesheet, Google Fonts), navbar, main content block, footer, flash messages block
- Build a reusable navbar partial (`_navbar.html`): logo, Discover link, login/signup or user dropdown (conditional on `request.user.is_authenticated`)
- Build a reusable footer partial (`_footer.html`)
- Configure `STATICFILES_DIRS` and `django.contrib.staticfiles` if not already done
- Set up `{% load static %}` pattern for all templates
- Install `django-widget-tweaks` or `django-crispy-forms` (with Tailwind pack) for form rendering

**Test:** `python manage.py runserver` — landing page renders with Tailwind styling, navbar, footer. No 404s on static assets.

---

### 2. Landing / Discover Page

**Do:**
- Replace stub landing page in `core` app with a real discover page
- Sections: hero banner, featured agencies grid (query `Agency.objects.filter(is_active=True).order_by('featured_order')[:6]`), call-to-action for models to sign up, brief "how it works" section
- Each agency card: logo, name, city, tagline, link to detail page
- URL: `/` (keep as root)

**Test:** Visit `/` — see hero, featured agencies (create a few via admin first), CTA links work.

---

### 3. Agency Index + Filtering

**Do:**
- View in `agencies` app: list all active agencies with pagination
- URL: `/agencies/`
- Template: grid/list of agency cards
- Filters (use `django-filter` or manual query params):
  - city
  - accepting applications (`is_accepting_applications`)
  - category / market focus (via related AgencyRequirement)
  - search by name
- Filters rendered as a sidebar or top bar, state preserved in URL query params so links are shareable

**Test:** `/agencies/` shows all agencies. Filtering by city narrows results. Search by name works. Pagination works when >12 agencies.

---

### 4. Agency Detail Page

**Do:**
- View in `agencies` app: `AgencyDetailView` (or function view), lookup by slug
- URL: `/agencies/<slug>/`
- Template sections per scope §15:
  - Hero: logo, cover image, name, tagline, city
  - Description
  - Requirements (loop `agency.requirements.filter(is_current=True)`)
  - Highlights (loop `agency.highlights.all()`)
  - Website / socials links
  - Application status badge (`is_accepting_applications`)
  - **Apply CTA button** — links to application flow (step 9), or prompts login if anonymous
  - Save agency toggle (wired in step 11)

**Test:** `/agencies/test-agency/` renders all sections. Requirements and highlights display. Apply button visible.

---

### 5. Model Onboarding Flow

**Do:**
- After signup, if `user.role == 'MODEL'` and `user.onboarding_completed == False`, redirect to onboarding
- Multi-step form or single long form in `accounts` (or `models_app`):
  - Step 1: Basic info — display name, city, date of birth, gender, bio
  - Step 2: Measurements — height, bust, waist, hips, shoe size (all optional for MVP)
  - Step 3: Profile photo upload, availability toggles, social links
- On completion: create `ModelProfile`, set `user.onboarding_completed = True`, redirect to model dashboard
- URL: `/onboarding/`
- Add middleware or decorator to enforce onboarding redirect for incomplete MODEL users on protected pages

**Test:** Sign up as MODEL → redirected to `/onboarding/` → fill form → ModelProfile created in DB → lands on dashboard. Returning to `/onboarding/` after completion redirects away.

---

### 6. Public Model Profile Page

**Do:**
- View in `models_app`: lookup by slug, check `is_public == True`
- URL: `/models/<slug>/`
- Template per scope §14:
  - Hero/profile image, cover image
  - Name, city, stats (height, measurements — display tastefully)
  - Bio
  - Represented / independent badge
  - Social/contact links
  - Portfolio grid (loop `profile.portfolio_posts.filter(is_public=True)`)
  - Follow button (wired in step 11)

**Test:** Create a ModelProfile via admin with `is_public=True`, visit `/models/<slug>/` — profile renders, portfolio grid shows posts.

---

### 7. Model Explore / Index Page

**Do:**
- View in `models_app` or `discovery`: list public, discoverable model profiles with pagination
- URL: `/models/`
- Template: card grid (profile image, name, city, category)
- Filters (per scope §11.2):
  - city
  - gender
  - height range
  - availability type
  - represented vs independent
  - search by name

**Test:** `/models/` shows model cards. Filters narrow results via query params.

---

### 8. Portfolio CRUD (Authenticated Models)

**Do:**
- Views in `portfolio` app, all `@login_required` + must be MODEL role:
  - **Create:** form with title, caption, cover image, is_public toggle. After creating post, allow adding PortfolioAsset images (inline formset or separate upload step). URL: `/portfolio/new/`
  - **Edit:** same form, prefilled. URL: `/portfolio/<slug>/edit/`
  - **Delete:** confirmation page. URL: `/portfolio/<slug>/delete/`
  - **Detail (public):** show post with image gallery, caption, credits. URL: `/portfolio/<slug>/`
- Portfolio post detail page: image gallery (all PortfolioAssets), caption, credits section (PortfolioPostCredit if implemented, or plain text for MVP)

**Test:** Log in as MODEL → create post with 3 images → post appears on profile page → edit title → delete one post → confirm removed.

---

### 9. Application Submission Flow

**Do:**
- View in `applications` app, `@login_required` + MODEL role + must have completed onboarding:
  - URL: `/agencies/<agency_slug>/apply/`
  - Pre-check: agency `is_accepting_applications`, user hasn't already submitted to this agency (or allow re-apply if withdrawn)
  - Form: cover note (textarea), optional: select featured portfolio posts to highlight
  - Profile summary auto-displayed (prefilled from ModelProfile — not editable here, just shown)
  - On submit:
    - Create `Application` with status `submitted`
    - Create `ApplicationSnapshot` capturing current profile data as JSON
    - Redirect to success/confirmation page
- Success page: "Application submitted" with link to track in dashboard

**Test:** Log in as MODEL with completed profile → go to agency detail page → click Apply → fill cover note → submit → Application row in DB with status `submitted` + Snapshot created → re-visiting apply page shows "already applied" message.

---

### 10. Model Dashboard

**Do:**
- Views in `dashboard` app, `@login_required` + MODEL role
- URL: `/dashboard/` (detect role and route accordingly)
- Sections per scope §16.1:
  - **Profile summary card** — photo, name, city, completeness indicator, "Edit Profile" link
  - **Portfolio manager** — list of own posts with edit/delete links, "New Post" button
  - **Submitted applications** — table: agency name, date submitted, status badge, link to agency page
  - **Saved agencies** — list with unsave action
  - **Followed profiles** — list with unfollow action
- Edit profile page (reuses onboarding form fields but as an update form): URL `/dashboard/profile/edit/`

**Test:** Log in as MODEL → `/dashboard/` shows all sections with real data. Edit profile updates ModelProfile. Application list reflects submitted applications.

---

### 11. SavedAgency + Follow Toggles

**Do:**
- Views in `discovery` app (or use HTMX for inline toggle without full page reload):
  - **Save agency:** POST `/agencies/<slug>/save/` — creates or deletes `SavedAgency` row (toggle)
  - **Follow model:** POST `/models/<slug>/follow/` — creates or deletes `Follow` row (toggle)
- Both require login; redirect to login if anonymous
- On agency detail page: Save button shows filled/unfilled state
- On model profile page: Follow button shows filled/unfilled state
- Counts: show follower count on model profiles, save count on agencies (optional for MVP)

**Test:** Log in → save an agency → appears in dashboard saved list → unsave → removed. Same for follow.

---

### 12. Agency Dashboard

**Do:**
- Views in `dashboard` app, `@login_required` + AGENCY_STAFF role + linked via `AgencyStaff`
- URL: `/dashboard/` (same URL, role-routed) or `/dashboard/agency/`
- Sections per scope §16.2:
  - **Application inbox** — table of applications to this agency: model name, city, height, date, status badge
  - **Filters:** status, city, height range, category
  - **Applicant detail view** — click into an application: see full ModelProfile snapshot, portfolio posts, cover note, status actions
  - **Status actions:** buttons/dropdown to move application to `under_review`, `shortlisted`, `contacted`, `rejected`. Updates `Application.status` and `reviewed_at` / `reviewed_by`

**Test:** Create an AgencyStaff user linked to an agency in admin → log in → `/dashboard/` shows agency inbox → submitted applications appear → click one → see profile snapshot → change status to "shortlisted" → status updates in list.

---

### 13. Resources / Transparency Section (Lightweight)

**Do:**
- Views in a `resources` app (or `core`):
  - Article list: `/resources/` — published ResourceArticles
  - Article detail: `/resources/<slug>/`
- Template: clean editorial layout, hero image, content body, author, date
- Admin already supports CRUD from Phase 1

**Test:** Create a ResourceArticle in admin → visit `/resources/` → article appears → click through to detail.

---

## Testing Plan

Run these yourself after each step:

| Step | Command / Action | Expected |
|------|-----------------|----------|
| 1 | `python manage.py runserver`, visit `/` | Tailwind-styled page with navbar + footer |
| 2 | Visit `/` | Hero, featured agencies, CTA render |
| 3 | Visit `/agencies/`, apply filters | Filtered, paginated agency list |
| 4 | Visit `/agencies/<slug>/` | Full agency detail with requirements, highlights, Apply CTA |
| 5 | Sign up as MODEL → `/onboarding/` | Multi-step form creates ModelProfile, sets `onboarding_completed` |
| 6 | Visit `/models/<slug>/` | Public profile with portfolio grid |
| 7 | Visit `/models/`, apply filters | Filtered, paginated model cards |
| 8 | Log in as MODEL → `/portfolio/new/` | Create post + assets, appears on profile |
| 8 | Edit and delete a portfolio post | Changes reflect correctly |
| 9 | Log in as MODEL → Apply to agency | Application + Snapshot created, success page shown |
| 9 | Re-visit apply page | "Already applied" guard works |
| 10 | Log in as MODEL → `/dashboard/` | All dashboard sections with real data |
| 10 | Edit profile from dashboard | ModelProfile updated |
| 11 | Save/unsave agency, follow/unfollow model | Toggle works, reflected in dashboard lists |
| 12 | Log in as AGENCY_STAFF → `/dashboard/` | Inbox shows applications, filters work |
| 12 | Click application → change status | Status updates, `reviewed_by` populated |
| 13 | Visit `/resources/`, `/resources/<slug>/` | Articles render |

Optional but recommended: write `tests.py` in each app with view tests (status codes, template used, context data) and form tests.

---

## What's Done After Phase 2

- ✅ Tailwind CSS template system with shared base layout
- ✅ Landing / discover page with featured agencies
- ✅ Agency index with search and filtering
- ✅ Agency detail pages with requirements, highlights, Apply CTA
- ✅ Model onboarding flow (profile creation after signup)
- ✅ Public model profiles with portfolio grids
- ✅ Model explore / index with filtering
- ✅ Portfolio CRUD for authenticated models
- ✅ Application submission with profile snapshot
- ✅ Model dashboard (profile, portfolio, applications, saves, follows)
- ✅ SavedAgency + Follow toggle system
- ✅ Agency dashboard (inbox, filters, status actions)
- ✅ Resources / transparency section

---

## What's Coming in Phase 3

- Add agency dashboard view for staff, and editing capability. similar to model view.
- Add phone number field to model profile, add contact information and applicant profile picture in applicant detail view.
- Add ability to switch from model to agency and vice versa.
- Add ability to delete model/agency
- Add contacting capability to applicant detail view page (email)
- Add ability for model agency to provide feedback to applicants (free text field in application model, visible to model in dashboard)
- Profile completeness indicator logic
- Email notifications (application submitted, status changed)
- Image optimization (thumbnails, compression, lazy loading)
- Add ability for models and agencies to crop photos akin to instagram's free cropping tool, with a minimum required resolution.

## Future Improvements
- Polish and UX refinement (animations, loading states, empty states, error pages)
- Resources section fleshing out
- Production deployment prep (whitenoise, S3 storage, `production.py` settings)
- Security hardening (rate limiting, CSRF review, input sanitization audit)
- Performance (query optimization, select_related/prefetch_related audit, caching)
