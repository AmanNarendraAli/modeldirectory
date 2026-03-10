# The Modelling Directory — Phase 3 Workplan

## Goal

Enhance the platform with agency self-management, richer application workflows, communication tools, and image optimization. By end of Phase 3: agency staff can edit their own agency profile, models receive feedback on applications, both parties can communicate via email, users can switch roles and delete accounts, and all images are optimized with cropping support.

---

## Prerequisites (from Phase 2)

- ✅ Tailwind CSS template system with shared base layout
- ✅ Landing / discover page with featured agencies
- ✅ Agency index with search and filtering + detail pages
- ✅ Model onboarding, public profiles, explore/index with filtering
- ✅ Portfolio CRUD for authenticated models
- ✅ Application submission with profile snapshot
- ✅ Model dashboard (profile, portfolio, applications, saves, follows)
- ✅ SavedAgency + Follow toggle system
- ✅ Agency dashboard (inbox, filters, status actions)
- ✅ Resources / transparency section

---

## Phase 3 Steps

### 1. Schema Changes — Phone Number + Feedback Field

**Do:**
- Add `phone_number = models.CharField(max_length=20, blank=True)` to `ModelProfile` in `apps/models_app/models.py`, after `contact_email` (line 44)
- Add `feedback = models.TextField(blank=True)` and `feedback_updated_at = models.DateTimeField(null=True, blank=True)` to `Application` in `apps/applications/models.py`, after `cover_note` (line 27)
- Run `python manage.py makemigrations models_app applications` then `python manage.py migrate`
- Add `"phone_number"` to `OnboardingForm.Meta.fields` in `apps/accounts/forms.py`
- Add phone_number field widget to the "Links & Contact" section in `templates/dashboard/edit_profile.html`
- Register the new fields in the admin classes for both models

**Test:** Edit a model profile → phone number saves. Create an application in admin → feedback field is editable.

---

### 2. Contact Info + Profile Picture in Applicant Detail View

**Do:**
- Modify `templates/dashboard/applicant_detail.html`:
  - Add a profile picture next to the applicant name in the header (line 9-10 area), using `application.applicant_profile.profile_image`
  - Add a "Contact Information" card in the sidebar (below the status update form), showing:
    - `application.applicant_profile.contact_email` (or `application.applicant_profile.user.email` as fallback)
    - `application.applicant_profile.phone_number`
    - `application.applicant_profile.instagram_url`
  - Show dashes for empty fields

**Test:** View an applicant detail as agency staff → profile image shows next to name → contact card shows email, phone, instagram.

---

### 3. Agency Feedback on Applications

**Do:**
- Create `FeedbackForm` in `apps/applications/forms.py` — ModelForm for Application with only `feedback` field, Textarea widget with Tailwind styling
- Add `submit_feedback` view in `apps/dashboard/views.py`:
  - POST only, requires agency staff permission for the application's agency
  - Validates FeedbackForm, saves feedback + sets `feedback_updated_at = timezone.now()`
  - Redirects back to applicant detail
- Pass `FeedbackForm(instance=application)` from `applicant_detail` view to template context
- Add URL: `path("applications/<int:application_id>/feedback/", views.submit_feedback, name="submit-feedback")` in `apps/dashboard/urls.py`
- Add "Feedback" card in `templates/dashboard/applicant_detail.html` (below cover note section), containing the form
- In `templates/dashboard/model_dashboard.html`, show feedback text under each application's status badge: `{% if app.feedback %}<p class="text-xs text-stone-500 mt-1 italic">"{{ app.feedback|truncatewords:20 }}"</p>{% endif %}`

**Test:** As agency staff, add feedback on applicant detail → feedback persists on refresh. As model, check dashboard → feedback shows under the relevant application.

---

### 4. Agency Dashboard Editing

**Do:**
- Create `apps/agencies/forms.py` with `AgencyEditForm(forms.ModelForm)`:
  - Fields: `name`, `short_tagline`, `description`, `city`, `headquarters_address`, `website_url`, `instagram_url`, `contact_email`, `logo`, `cover_image`, `is_accepting_applications`
  - Exclude sensitive fields: `slug`, `verification_status`, `is_featured`, `featured_order`, `is_active`, `created_by_admin`, `founded_year`
  - Tailwind widget styling matching OnboardingForm pattern
- Add `edit_agency` view in `apps/dashboard/views.py`:
  - Requires `AgencyStaff` record with `can_edit_agency=True`
  - GET: show form pre-filled with agency data
  - POST: validate and save, redirect to dashboard with success message
- Add URL: `path("agency/edit/", views.edit_agency, name="edit-agency")` in `apps/dashboard/urls.py`
- Create `templates/dashboard/edit_agency.html` following `edit_profile.html` pattern:
  - Sections: Basic Info (name, tagline, description, city, address), Online Presence (website, instagram, email), Images (logo with preview, cover with preview), Settings (accepting applications toggle)
- In `agency_dashboard` view, add `can_edit` boolean to context (check `can_edit_agency=True`)
- Add "Edit Agency" button in `templates/dashboard/agency_dashboard.html` header, conditionally shown when `can_edit` is true

**Test:** Set `can_edit_agency=True` for a staff member in admin → log in → "Edit Agency" button visible → edit name, tagline, upload logo → changes persist. Staff without `can_edit_agency` → no button, direct URL access redirects with error.

---

### 5. Email Infrastructure Setup

**Do:**
- Add to `modeldirectory/settings/development.py`:
  ```python
  EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
  DEFAULT_FROM_EMAIL = "noreply@modellingdirectory.com"
  ```
- Add to `modeldirectory/settings/production.py`:
  ```python
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
  EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
  EMAIL_PORT = env.int("EMAIL_PORT", default=587)
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
  EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
  DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@modellingdirectory.com")
  ```
- Create `apps/core/emails.py` with helper functions:
  - `send_application_submitted_email(application)` — notifies agency contact
  - `send_status_changed_email(application)` — notifies model
  - `send_contact_email(from_user, to_email, subject, body)` — agency staff to applicant
- Create `templates/emails/` directory with simple HTML email templates:
  - `application_submitted.html` — new application notification to agency
  - `status_changed.html` — status update notification to model
  - `contact_applicant.html` — agency-to-model email wrapper

**Test:** In Django shell: `from django.core.mail import send_mail; send_mail('Test', 'body', 'from@test.com', ['to@test.com'])` — verify it prints to console.

---

### 6. Email Contacting from Applicant Detail

**Do:**
- Create `ContactApplicantForm` in `apps/applications/forms.py` — regular Form (not ModelForm) with `subject` (CharField) and `body` (Textarea) fields, Tailwind styled
- Add `contact_applicant` view in `apps/dashboard/views.py`:
  - POST only, requires agency staff for the application's agency
  - Validates form, determines recipient: `applicant_profile.contact_email` or `applicant_profile.user.email`
  - Calls `send_contact_email()` from `apps/core/emails.py`
  - Shows success message, redirects to applicant detail
- Add URL: `path("applications/<int:application_id>/contact/", views.contact_applicant, name="contact-applicant")` in `apps/dashboard/urls.py`
- Pass `ContactApplicantForm()` from `applicant_detail` view to template context
- Add "Contact Applicant" card in `templates/dashboard/applicant_detail.html` sidebar (below status update), with subject + body fields and "Send Email" button

**Test:** As agency staff, open applicant detail → fill subject and body → "Send Email" → console shows the email output → success message displays.

---

### 7. Email Notifications (Application Submitted + Status Changed)

**Do:**
- In `apps/applications/views.py`, after application creation in `apply()` view, call `send_application_submitted_email(application)`
- In `apps/dashboard/views.py`, after status update in `update_application_status()`, call `send_status_changed_email(application)`
- `send_application_submitted_email()` logic:
  - Recipient: `application.agency.contact_email` or primary contact staff's email
  - Subject: "New Application from [name]"
  - Body: applicant name, city, height, link to review
- `send_status_changed_email()` logic:
  - Recipient: `applicant_profile.contact_email` or `applicant_profile.user.email`
  - Subject: "Application Update — [agency name]"
  - Body: new status, agency name, feedback if present

**Test:** Submit application as model → console shows "new application" email. Change status as agency staff → console shows "status changed" email.

---

### 8. Profile Completeness Indicator (Proper Logic)

**Do:**
- Add `get_completeness()` method to `ModelProfile` in `apps/models_app/models.py`:
  - Check 12 fields: profile_image, bio, city, date_of_birth, gender, height_cm, bust_cm, waist_cm, contact info (email or phone), social link (instagram or website), at least one portfolio post, at least one availability flag
  - Returns `(percentage, missing_fields_list)` tuple
- In `model_dashboard` view in `apps/dashboard/views.py`, replace the ad-hoc calculation (lines 42-43) with `profile.get_completeness()`
- Pass `missing_fields` to template context
- In `templates/dashboard/model_dashboard.html`, update the completeness banner to show a bullet list of missing items when profile is not 100%

**Test:** Create model profile with only some fields → percentage reflects checks → missing fields listed. Fill all fields + create portfolio post → 100%, banner hidden.

---

### 9. Role Switching (Model ↔ Agency Staff)

**Do:**
- Add `switch_role` view in `apps/accounts/views.py`:
  - POST only, login required
  - If switching to MODEL: set role, if no ModelProfile exists → set `onboarding_completed=False` and redirect to onboarding; else redirect to dashboard
  - If switching to AGENCY_STAFF: check `AgencyStaff` record exists → if not, show error "Contact an admin to be linked to an agency"; else set role and redirect to dashboard
- Add URL: `path("switch-role/", views.switch_role, name="switch-role")` in `apps/accounts/urls.py`
- In `templates/partials/_navbar.html`, add a role switch button in the authenticated user dropdown:
  - MODEL users see "Switch to Agency Staff" form (hidden input `role=AGENCY_STAFF`)
  - AGENCY_STAFF users see "Switch to Model" form (hidden input `role=MODEL`)

**Test:** As MODEL, switch to AGENCY_STAFF → with AgencyStaff record: redirects to agency dashboard; without: error message. As AGENCY_STAFF, switch to MODEL → with ModelProfile: model dashboard; without: onboarding.

---

### 10. Account Deletion

**Do:**
- Add `delete_account` view in `apps/accounts/views.py`:
  - GET: show confirmation page
  - POST: require user to type "delete my account" to confirm
  - On confirm: soft-delete (set `is_active=False`, anonymize email/name), logout, redirect to home with success message
  - Preserves referential integrity for agency review history
- Add URL: `path("delete-account/", views.delete_account, name="delete-account")` in `apps/accounts/urls.py`
- Create `templates/accounts/delete_account.html`:
  - Red warning banner explaining consequences
  - Text input requiring "delete my account"
  - Danger-styled submit button + cancel link
- Add "Danger Zone" section at bottom of `templates/dashboard/edit_profile.html` with link to delete account page
- Add similar link in `templates/dashboard/edit_agency.html` (from step 4)

**Test:** Go to edit profile → "Danger Zone" → click delete → type wrong text → error → type correct text → logged out → user `is_active=False` in admin → cannot log in again.

---

### 11. Image Optimization (Thumbnails, Compression, Lazy Loading)

**Do:**
- Install `django-imagekit`: `pipenv install django-imagekit`
- Add `"imagekit"` to `INSTALLED_APPS` in `settings/base.py`
- Add `ImageSpecField` to models (no migrations needed — specs are generated on demand):
  - `ModelProfile`: `profile_image_thumbnail` (150×150, WEBP), `cover_image_optimized` (1200×600, WEBP)
  - `Agency`: `logo_thumbnail` (200×200, WEBP), `cover_image_optimized` (1200×600, WEBP)
  - `PortfolioPost`: `cover_image_thumbnail` (400×400, WEBP)
  - `PortfolioAsset`: `image_thumbnail` (400×400, WEBP), `image_display` (1200×1200, WEBP)
- Update all `<img>` tags across templates to:
  - Add `loading="lazy"` attribute
  - Use thumbnail/optimized versions where appropriate (list views → thumbnails, detail views → display size)
- Key templates to update: `model_dashboard.html`, `applicant_detail.html`, `agency_dashboard.html`, `agency_list.html`, `agency_detail.html`, `model_list.html`, `model_detail.html`, `portfolio_detail.html`, `landing.html`

**Test:** Upload a profile image → verify `CACHE/` directory created under media with resized versions. Inspect page HTML → `loading="lazy"` present on images. Thumbnails are smaller file size than originals.

---

### 12. Photo Cropping (Cropper.js)

**Do:**
- Include Cropper.js via CDN (only on pages with image uploads, not globally):
  - CSS: `https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.css`
  - JS: `https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.js`
- Create `templates/partials/_crop_modal.html` — reusable crop modal:
  - Large preview area for selected image
  - Cropper.js initialized with `aspectRatio: NaN` (free crop, Instagram-style)
  - "Crop & Use" and "Cancel" buttons
  - JavaScript: listens for `change` on file inputs with `data-crop-min-width`/`data-crop-min-height`, shows modal, on crop replaces input file with cropped blob, shows preview thumbnail
- Add `data-crop-min-width` and `data-crop-min-height` attributes to image file inputs:
  - Profile image: 400×400 min
  - Cover image: 1200×400 min
  - Agency logo: 200×200 min
- Include the crop modal partial + Cropper.js in: `edit_profile.html`, `edit_agency.html`, `portfolio_form.html`
- Add server-side validation in form `clean_*` methods using Pillow to reject images below minimum dimensions

**Test:** On edit profile → select image → crop modal appears → free crop → confirm → cropped preview shown → submit → cropped image saved. Upload too-small image → server validation error.

---

## Testing Plan

Run these yourself after each step:

| Step | Command / Action | Expected |
|------|-----------------|----------|
| 1 | `python manage.py migrate`, edit model profile | Phone number field saves, feedback field in admin |
| 2 | View applicant detail as agency staff | Profile image + contact card visible |
| 3 | Add feedback as agency staff, check model dashboard | Feedback saves and shows on both sides |
| 4 | Log in as `can_edit_agency` staff → Edit Agency | Agency fields update, logo/cover upload works |
| 5 | Django shell: `send_mail(...)` | Email printed to console |
| 6 | Contact applicant from detail view | Email in console, success message shown |
| 7 | Submit application + change status | Notification emails in console for both events |
| 8 | Model dashboard with partial profile | Completeness % + missing fields list shown |
| 9 | Switch MODEL → AGENCY_STAFF and back | Correct redirects (dashboard/onboarding/error) |
| 10 | Delete account flow | Soft-delete, logout, cannot re-login |
| 11 | Upload images, check page source | Lazy loading, WEBP thumbnails generated |
| 12 | Upload image on edit profile | Crop modal, cropped result submitted |

---

## What's Done After Phase 3

- ✅ Agency staff can edit their agency profile from the dashboard
- ✅ Phone number on model profiles, contact info + photo in applicant review
- ✅ Agency feedback on applications, visible to models
- ✅ Agency dashboard editing capability
- ✅ Email infrastructure (console in dev, SMTP in prod)
- ✅ Agency staff can email applicants from the review page
- ✅ Email notifications for application submission and status changes
- ✅ Proper profile completeness indicator with missing field hints
- ✅ Role switching between Model and Agency Staff
- ✅ Account deletion (soft delete with anonymization)
- ✅ Image optimization (thumbnails, WEBP compression, lazy loading)
- ✅ Photo cropping with Cropper.js (free crop, minimum resolution)

---
## Urgent bugs to fix
- When onboarding or editing image, if you close rather than pressing use, you can get images that are too small to pass through the validation. make it so you can't click out of the image - you have to close or press use.
- When onboarding, if you set measurements to inches and save, they won't get converted to cm in the db - the values just get saved. eg. 1 inch will be saved as 1, and the db base unit is cm, so that's wrong lol. When editing measurements, this issue seems to be even worse - it seems to double divide and stuff. Also, not being allowed to save non-whole numbers for measurements.
- Turns out that for the custom agency name (when an agency is not on the site), we need to reflect that in the backend as well, or it's not consistent across interfaces.

## Phase 4
- Call on whether to do email sending or use live messaging on app linkedin style.
- Add ability to filter models by verification status (e.g. verified models get a "verified" badge on their profile and in search results). Should set up page for verification as well, but actual verification process can be manual for now (admin sets `is_verified=True` in admin).
- Polish and UX refinement (animations, loading states, empty states, error pages)
- Production deployment prep (whitenoise, S3 storage, `production.py` settings)
- Security hardening (rate limiting, CSRF review, input sanitization audit)
- Performance (query optimization, select_related/prefetch_related audit, caching)

## Future improvements
- Resources section fleshing out
- Email verification flow (is_verified_email field exists but unused)
- Model/agency verification workflows
- In-platform messaging between agencies and models
- Social features on portfolios (likes, comments)

---

## Phase 3 Addendum — Post-Phase Improvements

### Crop Modal Enhancements
- **Rotation button** added to the crop interface (90° per click, uses Cropper.js `rotate()`)
- **Fixed size minimum enforcement bug**: `getCroppedCanvas()` no longer passes `minWidth`/`minHeight` (which silently upscaled tiny images past the check); canvas now reflects true cropped-area pixel dimensions
- **Event delegation** replaces per-element file input listeners, so dynamically added portfolio asset inputs trigger the modal automatically

### Portfolio Crop Support
- Crop modal included on `portfolio_form.html`; cover image and all asset inputs have `data-crop`
- Existing asset photos now show a recrop button alongside their preview thumbnail
- No minimum dimensions enforced for portfolio images (per design decision)

### Portfolio Detail Carousel
- `portfolio_detail.html` redesigned as a scrollable carousel (cover image first, then assets in display order)
- Prev/Next arrow buttons, dot indicators, keyboard arrows, and touch swipe supported
- No external dependencies

### Agency Roster on Public Page
- `Agency.is_roster_public` field (migration `0002`); toggle in Edit Agency → Settings
- Public models grid shown on the agency detail page when enabled

### Agency/Independent on Model Public Page
- "Represented by [Agency]" or "Independent" shown above the About section on model public profiles

### Ban System (`AgencyBan` model, migration `0002`)
- Agency removing a model creates an `AgencyBan` record
- Model cannot self-add back to a banning agency; error names the agency: _"You were removed by [Name]. Only they can add you back."_
- Agency re-adding a banned model clears the ban; voluntary independence does not create a ban

### Roster Search Dropdown
- New endpoint `GET /dashboard/agency/<id>/search-models/?q=` returns JSON (name, height, city, avatar)
- Agency dashboard roster form replaced with live-search dropdown (debounced, GitHub-collaborator style)
- `link_model` accepts `model_id` (PK) instead of name string

### "Other" Representation Option
- JS-injected "Signed to an agency not on this platform" option on edit profile
- Reveals a free-text field (UI-only, not persisted); clears select to null on submit

### Agency List Application Status
- Logged-in model users see their application status badge instead of "Accepting Applications"
- Colour-coded by status value; draft applications excluded

### Email Logging & Fix
- `fail_silently=True` removed; errors caught and logged via `logging`
- `LOGGING` config in `settings/base.py` routes `apps.core.emails` to console at DEBUG level
