# The Modelling Directory — Phase 1 Workplan

## Goal

Stand up the full data layer, project structure, custom auth, admin interface, and basic auth flows. By end of Phase 1 the database is fully modelled, admin can CRUD all entities, and users can sign up / log in / log out. No public-facing templates beyond a stub landing page.

---

## Phase 1 Steps

### 1. Project Restructure

Current state: default `startproject` scaffold with [modeldirectory/settings.py](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/modeldirectory/settings.py).

**Do:**
- Keep `modeldirectory/` as config package (no rename)
- Split settings into `modeldirectory/settings/base.py`, `development.py`, `production.py`
- Move secrets to [.env](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/.env), load via `django-environ`
- Update [manage.py](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/manage.py) to `DJANGO_SETTINGS_MODULE = 'modeldirectory.settings.development'`
- Create `docker-compose.yml` with Postgres service (see step 1b)
- Populate [.env](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/.env) with: `SECRET_KEY`, `DEBUG=True`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST=localhost`, `DB_PORT=5432`
- Create `.env.example` with placeholder values
- Update [.gitignore](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/.gitignore): add `media/`, `__pycache__/`, `*.pyc`, [.env](file:///c:/Users/wiztu/OneDrive/Documents/Coding%20Projects/DjangoPractice/modeldirectory/.env), `staticfiles/`
- Create top-level dirs: `apps/`, `templates/`, `static/`, `media/`
- Install deps: `django-environ`, `Pillow`, `psycopg2-binary`

**Test:** `python manage.py check` passes, `runserver` starts.

---

### 1b. Docker Compose + Postgres

Create `docker-compose.yml` at project root:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

In `base.py`, configure:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}
```

**Test:** `docker compose up -d`, then `python manage.py check` — should connect to Postgres.

---

### 2. Create Django Apps

Inside `apps/`:

| App | Purpose |
|-----|---------|
| `accounts` | Custom User model, auth, roles |
| `models_app` | ModelProfile, measurements |
| `agencies` | Agency, AgencyRequirement, AgencyHighlight, AgencyStaff |
| `applications` | Application, ApplicationSnapshot |
| `portfolio` | PortfolioPost, PortfolioAsset |
| `discovery` | SavedAgency, Follow (can be in `common` too) |
| `core` | Landing page stub, shared base templates, context processors |

Run `python manage.py startapp <name>` for each inside `apps/`. Add `apps.<name>` to `INSTALLED_APPS`.

**Test:** `python manage.py check` still passes.

---

### 3. Custom User Model

> [!CAUTION]
> Must be done **before** first `migrate`. If you've already migrated with default User, delete `db.sqlite3` and all migration files first.

In `apps/accounts/models.py`:

```python
class User(AbstractBaseUser, PermissionsMixin):
    email            # PK login field, unique
    full_name
    role             # CharField with choices: ADMIN, MODEL, AGENCY_STAFF
    phone_number     # optional
    is_active
    is_staff
    is_verified_email
    onboarding_completed
    created_at
    updated_at

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
```

- Write `UserManager` (extending `BaseUserManager`) with `create_user` / `create_superuser`.
- Set `AUTH_USER_MODEL = 'accounts.User'` in settings.
- Register in admin with `UserAdmin` subclass.

**Test:** `makemigrations`, `migrate`, `createsuperuser` with email login works, admin shows User list.

---

### 4. Core Data Models

Build in dependency order:

#### 4a. `agencies` app
- `Agency` — fields per scope §10.3
- `AgencyRequirement` — FK to Agency, fields per §10.4
- `AgencyHighlight` — FK to Agency, fields per §10.5
- `AgencyStaff` — FK to User + Agency, fields per §10.6

#### 4b. `models_app` app
- `ModelProfile` — OneToOne to User, fields per §10.2
  - nullable FK `represented_by_agency` → Agency

#### 4c. `portfolio` app
- `PortfolioPost` — FK to ModelProfile, fields per §10.7
- `PortfolioAsset` — FK to PortfolioPost, fields per §10.8

#### 4d. `applications` app
- `Application` — FK to ModelProfile + Agency, optional FK AgencyRequirement, fields per §10.10
  - Status choices: draft, submitted, under_review, shortlisted, contacted, rejected, withdrawn
- `ApplicationSnapshot` — OneToOne to Application, JSON fields per §10.11

#### 4e. `discovery` app
- `SavedAgency` — FK User + Agency, unique_together
- `Follow` — FK User + ModelProfile, unique_together

**For every model:**
- `__str__` method
- `Meta` with ordering, verbose names, constraints where needed
- Slug fields auto-populated via `slugify` (override `save()` or use signal)

**Test:** `makemigrations`, `migrate` succeeds. Shell spot-check: create instances, verify FK relationships, unique constraints.

---

### 5. Admin Configuration

For **every** model, register with:
- `list_display` (key fields)
- `list_filter` (city, status, role, is_active, etc.)
- `search_fields` (name, email, slug)
- `readonly_fields` (created_at, updated_at)
- Inline admins where useful:
  - `AgencyRequirementInline` on Agency
  - `AgencyHighlightInline` on Agency
  - `AgencyStaffInline` on Agency
  - `PortfolioAssetInline` on PortfolioPost

**Test:** Log into admin, create an Agency with requirements + highlights + staff. Create a ModelProfile. Create a PortfolioPost with assets. Create an Application. Verify everything saves and displays correctly.

---

### 6. Media Configuration

In `base.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

In `config/urls.py` (dev only):
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Test:** Upload an image via admin (e.g. Agency logo), verify it saves to `media/` and is accessible at the URL.

---

### 7. Basic Auth Flows

Use Django's built-in `LoginView`, `LogoutView` for now. No `django-allauth` yet.

- Create minimal templates: `registration/login.html`, `registration/logged_out.html`
- Settings: `LOGIN_REDIRECT_URL = '/'`, `LOGOUT_REDIRECT_URL = '/'`
- Wire URLs in `config/urls.py`
- **Stub landing page** in `core` app: single view + template showing "Welcome to The Modelling Directory" with login/logout links

**Test:** Sign up via `createsuperuser`, log in at `/accounts/login/`, get redirected to landing page, log out works.

---

### 8. Signup View (email-based)

In `accounts`:
- `SignupForm` extending `UserCreationForm` for the custom User model
- `SignupView` (FormView or CreateView)
- Template: `accounts/signup.html`
- URL: `/accounts/signup/`
- On success: log user in, redirect to landing page

**Test:** Visit `/accounts/signup/`, create account with email + password, verify user appears in admin, verify login works.

---

## Testing Plan

You should run these yourself after each step:

| Step | Command / Action | Expected |
|------|-----------------|----------|
| 1 | `python manage.py check` | No errors |
| 1 | `python manage.py runserver` | Starts on 8000 |
| 2 | `python manage.py check` | No errors, all apps recognized |
| 3 | `python manage.py makemigrations` then `migrate` | Clean migration |
| 3 | `python manage.py createsuperuser` | Prompts for email (not username) |
| 3 | Log into `/admin/` | See Users in admin |
| 4 | `python manage.py makemigrations` then `migrate` | All models created |
| 4 | Django shell: create Agency, ModelProfile, PortfolioPost, Application | No errors |
| 5 | `/admin/` — CRUD all models | All fields, filters, inlines work |
| 6 | Upload image in admin | File appears in `media/`, URL loads in browser |
| 7 | `/accounts/login/` and `/accounts/logout/` | Login/logout cycle works |
| 8 | `/accounts/signup/` | New user created, logged in, redirected |

Optional but recommended: write `tests.py` in each app with basic model creation tests.

---

## What's Done After Phase 1

- ✅ Project restructured (split settings, env vars, app dirs)
- ✅ Custom User model with email login + roles
- ✅ All core data models built and migrated
- ✅ Full admin interface for all models
- ✅ Media upload working in dev
- ✅ Basic login / logout / signup
- ✅ Stub landing page

---

## What's Coming in Phase 2

- Public-facing templates: agency index, agency detail, model profiles, portfolio pages
- Model onboarding flow (profile creation wizard after signup)
- Portfolio CRUD for authenticated models
- Application submission flow (from agency detail page)
- Agency dashboard (view/filter/action on applications)
- Model dashboard (edit profile, manage portfolio, track applications)
- Search & filtering (agency index, model explore)
- SavedAgency / Follow toggle views
- Template system + Tailwind CSS setup
- Static file pipeline
