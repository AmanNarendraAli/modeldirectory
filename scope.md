# The Modelling Directory — Django MVP Workplan

## 1. Product Summary

**The Modelling Directory** is a platform for models in the Indian fashion industry to:
- discover agencies,
- build public portfolios,
- apply to agencies directly on-platform,
- gain more transparency into an otherwise fragmented market.

This MVP is **model-first**. Agencies are the supply-side/scouting-side, but in the first version, agency pages and agency data will be created and managed by the platform owner/admin. The system should still be designed so agency-managed dashboards and verification can be added later without reworking the whole architecture.

---

## 2. Core MVP Goal

The single most important thing this product should do in version 1:

> Help models discover agencies and apply to them using a professional on-platform portfolio.

Everything else should support that core workflow.

---

## 3. MVP Scope

## In Scope

### Public-facing
- Landing page
- Discover/browse agencies
- Agency detail pages
- Public model profiles
- Public model portfolios
- Search and filtering for agencies/models

### Authenticated user features
- User signup/login/logout
- Model onboarding/profile creation
- Portfolio post creation and editing
- Save/follow lightweight discovery actions
- Apply to agencies through the platform
- Application tracking from the model side

### Agency-side MVP
- Agency-facing dashboard/view
- View incoming applications
- Review applicant portfolio/profile
- Update application status

### Admin-side
- Create/edit/delete agencies
- Mark agencies as featured or verified-ready
- Moderate basic content if needed
- Manage relational data like cities, categories, tags, specialties

---

## Out of Scope for MVP

Do **not** build these in version 1:
- Full social feed/news homepage
- Direct messaging/chat
- Comments
- Real-time notifications
- Video uploads
- Automated fashion news aggregation
- Full moderation queue/review workflow
- Agency self-serve onboarding
- Payments/subscriptions
- Complex recommendation engine
- Casting call marketplace

These should be left for phase 2+.

---

## 4. Key User Types

## 4.1 Model
Primary user in MVP.

Main actions:
- create account,
- build profile,
- upload portfolio,
- browse agencies,
- apply to agencies,
- save agencies,
- follow models,
- make profile publicly discoverable.

---

## 4.2 Agency User
Secondary user, but important.

Main actions:
- log in to agency-side dashboard,
- review applicants,
- view applicant model cards and portfolios,
- move applications through statuses.

Note: in MVP, agencies may not create their own agency profile pages yet. Instead, the platform admin creates agency listings, while agency staff get dashboard access tied to that agency.

---

## 4.3 Admin
Platform owner/operator.

Main actions:
- manage agencies,
- manage agency staff access,
- manage tags/categories/requirements,
- manage featured/verified flags,
- review platform usage and quality.

---

## 5. Product Architecture Philosophy

The system should be built in a way that is:
- beautiful and functional,
- startup-ready,
- modular,
- extensible.

Key principle:

> Even if admin manages agency pages for now, the data model should assume agencies will eventually own and edit their own records.

That means you should separate:
- `Agency` data,
- `AgencyStaff` access,
- `AgencyApplicationRequirements`,
- `Application` records,
- `ModelProfile` and `PortfolioPost`.

---

## 6. Proposed Information Architecture

## Main public pages
- Home / Discover
- Agencies index
- Agency detail
- Models index / Explore
- Model profile
- Portfolio post detail
- About / Transparency section
- Resource centre (lightweight MVP)
- Login / Signup
- Onboarding
- Dashboard

## Authenticated dashboard areas
### Model dashboard
- edit profile,
- manage portfolio,
- submitted applications,
- saved agencies,
- followed profiles.

### Agency dashboard
- overview,
- applications inbox,
- applicant detail view,
- application filters/statuses.

### Admin dashboard
Use Django admin initially, customized where needed.

---

## 7. Core User Flows

## 7.1 Model signup to application flow
1. User lands on platform
2. Browses agencies publicly
3. Signs up to apply
4. Completes model profile
5. Uploads portfolio media/posts
6. Views an agency page
7. Clicks apply
8. Fills application form
9. Submits application
10. Tracks status from dashboard

---

## 7.2 Agency review flow
1. Agency staff logs in
2. Views dashboard
3. Sees incoming applications
4. Filters by city/height/category/status
5. Opens application
6. Reviews profile + portfolio
7. Moves status to reviewed/shortlisted/rejected/etc.
8. Optional future step: contact applicant externally or on-platform

---

## 7.3 Public discovery flow
1. Visitor lands on discover page
2. Filters agencies or models
3. Opens detailed public profile
4. Saves/follows if logged in
5. Signs up if wants to apply or interact

---

## 8. Django App Structure

Recommended project organization:

- `core`
- `accounts`
- `models_app` (or `talent`)
- `agencies`
- `applications`
- `portfolio`
- `discovery`
- `resources`
- `social`
- `dashboard`
- `common` or `utils`

### Suggested responsibilities

## `core`
- base templates
- landing page
- shared views
- site config

## `accounts`
- custom user model
- auth
- onboarding
- permissions/roles

## `models_app`
- model-specific public profile
- measurements
- discoverability settings
- verification state

## `agencies`
- agency listings
- agency requirements
- agency detail pages
- agency staff relationships

## `applications`
- application submission
- application statuses
- application history
- review actions

## `portfolio`
- media uploads
- portfolio posts
- tagged collaborators/agencies/designers

## `discovery`
- search
- filters
- saved entities
- follow system

## `resources`
- blog/resource centre
- editorial content

## `social`
- follows
- saves
- contact links
- lightweight interaction features only

## `dashboard`
- model dashboard
- agency dashboard
- summary stats
- inbox views

---

## 9. Auth and Roles

Use a **custom Django user model from day one**.

Recommended base roles:
- `ADMIN`
- `MODEL`
- `AGENCY_STAFF`

Do not hardcode role logic all over the place. Centralize it in:
- permissions utilities,
- decorators,
- service layer functions,
- role-aware dashboards.

Potential future roles:
- `AGENCY_OWNER`
- `EDITOR`
- `MODERATOR`
- `PHOTOGRAPHER`
- `STYLIST`

---

## 10. Data Model Design

## 10.1 User
Custom user model with:
- email
- password
- full_name
- role
- phone_number
- is_active
- is_verified_email
- created_at
- updated_at

Optional:
- onboarding_completed

---

## 10.2 ModelProfile
One-to-one with User.

Suggested fields:
- user
- public_display_name
- slug
- profile_image
- cover_image
- bio
- city
- country (default India for MVP)
- date_of_birth or age range
- gender
- height_cm
- bust_cm
- waist_cm
- hips_cm
- shoe_size
- hair_color
- eye_color
- instagram_url
- website_url
- contact_email
- available_for_editorial
- available_for_runway
- available_for_commercial
- available_for_fittings
- represented_by_agency (nullable FK if applicable later)
- is_public
- is_discoverable
- verification_status
- created_at
- updated_at

Important:
- Some fields may be optional for MVP.
- Measurements should be handled carefully and respectfully in UX.

---

## 10.3 Agency
Suggested fields:
- name
- slug
- logo
- cover_image
- short_tagline
- description
- city
- headquarters_address_optional
- website_url
- instagram_url
- contact_email
- founded_year
- featured_order / featured flag
- verification_status
- is_active
- is_accepting_applications
- created_by_admin
- created_at
- updated_at

---

## 10.4 AgencyRequirement
This should be separated from the agency core model so requirements can evolve over time.

Suggested fields:
- agency (FK)
- category (menswear/womenswear/all/editorial/commercial/runway etc.)
- min_height_cm
- max_height_cm optional
- age_min optional
- age_max optional
- notes
- accepts_beginners
- application_guidance_text
- active_from
- active_to optional
- is_current

This lets agencies have multiple requirement sets later.

---

## 10.5 AgencyHighlight
For “what has the agency accomplished.”

Suggested fields:
- agency
- title
- description
- related_model_name
- related_brand_name
- year
- image optional
- display_order

---

## 10.6 AgencyStaff
Links users to agencies.

Suggested fields:
- user
- agency
- role_title
- can_review_applications
- can_edit_agency_in_future
- is_primary_contact

This is the bridge to self-serve agency management later.

---

## 10.7 PortfolioPost
Core feature.

Suggested fields:
- owner_profile
- title
- slug
- caption
- cover_image
- is_public
- published_at
- created_at
- updated_at

Better to keep post metadata modular rather than shoving everything into one huge table.

---

## 10.8 PortfolioAsset
For multiple images per post.

Suggested fields:
- portfolio_post
- image
- alt_text
- display_order

For MVP, image-only is enough.

---

## 10.9 PortfolioTagging / Relational Metadata
Since you want relational tagging, do not only use free text.

Potential related models:
- `Designer`
- `Brand`
- `Photographer`
- `Stylist`
- `MakeupArtist`
- `ShowEvent`
- `Publication`

For MVP, you can simplify and start with generic tagged entities or a few concrete models.

Suggested approach:
- `Brand`
- `Designer`
- `CreativeEntity` or `Collaborator`

Then a junction model like:
- `PortfolioPostCredit`
  - portfolio_post
  - entity_type
  - linked_object optional
  - display_name fallback
  - role_label

This balances structure and flexibility.

---

## 10.10 Application
This is one of the most important models.

Suggested fields:
- applicant_profile
- agency
- agency_requirement optional FK
- status
- cover_note
- submitted_at
- reviewed_at
- reviewed_by
- updated_at

Recommended statuses:
- draft
- submitted
- under_review
- shortlisted
- contacted
- rejected
- withdrawn

Optional future:
- archived

---

## 10.11 ApplicationSnapshot
Very useful if you want historical accuracy.

When an application is submitted, store a snapshot of relevant profile data:
- applicant_name
- city
- height_cm
- measurements
- portfolio_summary
- selected_portfolio_posts maybe JSON
- submission_payload JSON

This prevents applications from becoming inconsistent if users edit profiles later.

---

## 10.12 SavedAgency
For lightweight discovery.

Fields:
- user
- agency
- created_at

Unique together.

---

## 10.13 Follow
For model discovery.

Fields:
- follower_user
- followed_model_profile
- created_at

Unique together.

---

## 10.14 ResourceArticle
For the transparency/help centre.

Fields:
- title
- slug
- summary
- content
- hero_image
- is_published
- published_at
- author
- category
- created_at
- updated_at

Keep simple.

---

## 11. Search and Filtering

## 11.1 Agency filters
- city
- category / market focus
- menswear/womenswear/all
- minimum height expectations
- accepting applications
- verified
- featured

## 11.2 Model filters
- city
- gender/category
- height range
- verification
- portfolio tags
- represented vs independent
- availability types

Use query params in URLs cleanly from the start so filtered discovery pages are shareable.

---

## 12. Public vs Private Rules

## Public
- agency directory
- agency detail pages
- public model profiles
- public portfolio posts
- resources/articles
- discover pages

## Requires login
- apply to agency
- save agency
- follow model
- create/edit profile
- upload portfolio
- view personal dashboard
- review agency applications

---

## 13. Application UX Design Notes

The application experience should feel polished and low-friction.

Recommended structure:

### On agency page
- clear CTA: **Apply**
- show current requirements
- show whether user meets basic requirements where possible
- prompt signup/login if not authenticated

### Application form
- prefilled from model profile
- editable cover note
- optional selection of featured portfolio posts
- clear summary before submit

### After submit
- success screen
- application confirmation in dashboard
- status badge

Important:
Do not make users repeatedly type information already on their profile.

---

## 14. Portfolio UX Design Notes

Portfolio should feel more professional than Instagram.

Model profile page:
- hero/profile image
- name + city + stats
- bio
- represented/independent status
- contact links
- clean grid of portfolio work

Portfolio post page:
- image gallery
- caption/story
- structured credits
- linked designer/team/agency where applicable

---

## 15. Agency Detail Page Requirements

Each agency page should include:

- name
- logo / hero image
- tagline
- description
- city
- website / socials
- current application status
- specific requirements
- notable models/highlights
- apply CTA
- maybe FAQ section
- optional “what they look for” text
- verification badge placeholder

This page is central to the product.

---

## 16. Dashboards

## 16.1 Model dashboard
Sections:
- profile completion
- portfolio manager
- submitted applications
- saved agencies
- followed profiles
- account settings

Nice extra:
- profile completeness indicator

---

## 16.2 Agency dashboard
Sections:
- application inbox
- filters by status/city/height/category
- applicant detail page
- recent activity
- shortlist/reject/review actions

Do not overbuild analytics in v1.

---

## 17. Admin / Operations Plan

Use Django admin heavily in MVP.

Admin should be able to:
- create agencies
- manage requirements
- manage highlights
- assign agency staff
- edit resource content
- inspect applications
- toggle verification flags
- feature agencies/models

Build custom admin panels and list filters where needed.

---

## 18. Media Handling

Users will upload media directly, so plan this properly.

### MVP approach
- image uploads only
- store via cloud object storage in production
- local media volume in development
- generate thumbnails if possible
- enforce size/compression limits
- validate file type

### Dev environment
- local Docker volume for media
- `.env` for storage credentials later

### Production-ready direction
- S3-compatible storage
- django-storages or equivalent
- CDN later

---

## 19. Tech Stack Recommendations

Backend:
- Django
- Django ORM
- PostgreSQL

Infra/dev:
- Docker
- docker-compose
- Pipenv
- `.env` files

Frontend:
- Django templates for MVP, or Django + HTMX for richer interactions
- Tailwind CSS strongly recommended
- Alpine.js optional for tiny interactions

Other helpful tools:
- Pillow for image handling
- django-allauth or custom auth flows
- django-filter
- crispy forms optional
- whitenoise for static files in simple deployments
- celery/redis only if background jobs become necessary later

Recommended philosophy:
> Keep the backend and product logic strong first. Do not prematurely split into Django API + separate frontend unless there is a very clear reason.

---

## 20. Environment and Config Plan

Use `.env` files for:
- `DJANGO_SECRET_KEY`
- `DEBUG`
- `DATABASE_URL` or DB credentials
- `ALLOWED_HOSTS`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- storage credentials later
- optional Sentry key later

Development setup assumptions:
- working inside Pipenv shell
- Docker for Postgres and possibly Redis later
- environment-specific settings split:
  - `base.py`
  - `development.py`
  - `production.py`

---

## 21. Suggested Repository Structure

```text
modelling-directory/
├── docker-compose.yml
├── Dockerfile
├── Pipfile
├── Pipfile.lock
├── .env
├── .env.example
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   ├── accounts/
│   ├── models_app/
│   ├── agencies/
│   ├── applications/
│   ├── portfolio/
│   ├── discovery/
│   ├── resources/
│   ├── dashboard/
│   └── common/
├── templates/
├── static/
├── media/
└── requirements_docs/