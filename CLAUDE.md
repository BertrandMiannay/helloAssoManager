# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application that imports and manages sports club (plongée) membership data and events from the [HelloAsso](https://www.helloasso.com/) platform. Managed with Poetry (Python 3.13). UI is in French.

## Commands

```bash
# Install dependencies
poetry install

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Reset dev database (deletes db.sqlite3, re-migrates, creates admin/admin superuser)
python manage.py init_dev_db [--username admin] [--email admin@example.com] [--password admin]

# Create migrations after model changes
python manage.py makemigrations helloAssoImporter
python manage.py makemigrations userManagement

# Revert all migrations for an app
python manage.py migrate helloAssoImporter zero

# Run tests
python manage.py test

# Run tests for a single app
python manage.py test helloAssoImporter
```

## Environment Variables

A `.env` file is required at the project root. All variables are loaded by `common/api/helloAssoApi.py` via `python-dotenv` and by `config/settings.py`.

```
HELLO_ASSO_API_CLIENT_ID=...
HELLO_ASSO_API_CLIENT_SECRET=...
ORGANIZATION_SLUG=...
DEBUG=True
SECRET_KEY=...
DATABASE_URL=postgres://...        # Optional: defaults to SQLite in dev
SESSION_COOKIE_SECURE=False        # Set True in production (HTTPS)
CSRF_COOKIE_SECURE=False           # Set True in production (HTTPS)
ALLOWED_HOSTS=localhost,127.0.0.1  # Comma-separated
```

## Architecture

### Django Apps

- **`helloAssoImporter/`** — Core data import app. Models cascade: `MemberShipForm` → `MemberShipFormOrder` → `Member` and `EventForm` → `EventFormOrder` → `EventRegistration`. Also has `Season` for grouping membership periods. All models registered in Django admin.
- **`userManagement/`** — Custom user model (`CustomUser` extends `AbstractUser`), group-based role system, invitation-only registration flow. `CustomUser` registered in Django admin via `CustomUserAdmin`.
- **`common/api/helloAssoApi.py`** — Shared `HelloAssoApi` class wrapping the `helloasso-python` SDK (OpenAPI/Pydantic). Handles token auth, automatic token refresh on 401, and all API calls to HelloAsso.
- **`config/`** — Django project settings, root URL conf, ASGI/WSGI.
- **`tpmanagement/`** — Stub directory, currently unused.

### Role System

Group-based via Django Groups. The `_create_default_groups` signal (`post_migrate`) in `userManagement/apps.py` creates them automatically.

| Groupe | Label affiché | Accès |
|--------|---------------|-------|
| `admin` | Administrateur | Gestion utilisateurs + toutes les sections |
| `member` | Membre | Inscriptions (lecture) |
| `instructor` | Formateur | Inscriptions (lecture) |
| `dive_director` | Directeur de plongée | Inscriptions (lecture) |

**Permission helpers** (defined in `helloAssoImporter/views.py` and `userManagement/views.py`):
- `_is_administrator(user)` — group `admin` or `is_superuser`
- `_is_club_staff(user)` — groups `admin`, `instructor`, `dive_director`, or `is_superuser`
- `AdminRequiredMixin` / `@admin_required` decorator — restricts to admins
- `ClubStaffRequiredMixin` / `@club_staff_required` decorator — restricts to club staff
- `CustomUser.is_administrator` — cached property checking group membership

### Models

#### `userManagement` app
- **`CustomUser`** — extends `AbstractUser`. Fields: `invite_token` (UUIDField), `invite_expires_at` (DateTimeField). Cached property `is_administrator`.

#### `helloAssoImporter` app
- **`Season`** — `label` (CharField), `current` (BooleanField).
- **`MemberShipForm`** — PK: `form_slug`. Fields: title, form_type, description, start/end dates, `season` (FK → Season), `field_mapping` (JSONField, maps standardized field names to HelloAsso custom field names).
- **`MemberShipFormOrder`** — PK: `item_id`. FK → `MemberShipForm`, FK → `Member` (nullable). Fields: payer info, category, sex, licence_number, dive_level, dive_teaching_level, apnea_level, apnea_teaching_level, underwater_shooting_level, underwater_shooting_teaching_level, birthdate, caci_expiration, timestamps.
- **`Member`** — auto PK. Fields: email, first_name, last_name. Unique constraint on `(email, first_name, last_name)`.
- **`EventForm`** — PK: `form_slug`. Fields: title, form_type, description, start/end dates, `last_registration_updated` (nullable, used for incremental refresh).
- **`EventFormOrder`** — PK: `order_id`. FK → `EventForm`. Fields: payer email/name, timestamps.
- **`EventRegistration`** — PK: `item_id`. FK → `EventFormOrder`. Fields: name, first_name, last_name, `state` (choices: Waiting/Processed/Registered/Deleted/Refunded/Canceled/Refused/Contested/Abandoned/Unknown).

### Data Import Flow

#### Events
1. `refresh_event_forms()` — fetches all Event forms from HelloAsso, upserts `EventForm` records.
2. `get_event_form_orders(form, since=...)` — fetches orders filtered by `last_registration_updated`, creates `EventFormOrder` and `EventRegistration` records (atomic).
3. The "Rafraîchir" button on `/inscriptions/` runs both steps for all forms and has a **60-second rate-limit cooldown** (using Django cache).

#### Memberships
1. `refresh_membership_forms()` — fetches membership forms, upserts `MemberShipForm` records.
2. `save_membership_form_members(form)` — paginated fetch, parses HelloAsso custom fields using `form.field_mapping`, creates `Member` + `MemberShipFormOrder` records (atomic).
3. Not exposed in the main UI — accessible via admin or `/saison/` routes.

#### Field Mapping
`MemberShipForm.field_mapping` is a JSONField that maps standardized level field names (e.g., `"dive_level"`) to HelloAsso custom field names (e.g., `"Niveau plongée"`). The editor is on the membership form detail page.

### HelloAsso API Client (`common/api/helloAssoApi.py`)

- Uses `helloasso-python` SDK (OpenAPI auto-generated, Pydantic models).
- Token fetched via `client_credentials` OAuth2 flow.
- All SDK calls go through `_call(fn, *args, **kwargs)`: catches `ApiException(401)`, reauthenticates once, retries. Second failure raises `HelloAssoApiError`.
- Singleton: `_hello_asso_api_instance` global, initialized at startup via `init_hello_asso_api()` (called by `helloAssoImporter/apps.py`). Retrieved via `get_hello_asso_api()`.
- **Creating events** via `create_event_form()` requires the `FormAdministration` API privilege (not yet activated). The UI button is present but shows "WIP".

### Authentication & Authorization

- `django-allauth` handles login/signup. Signup is invitation-only (`INVITATIONS_INVITATION_ONLY = True`).
- Custom invitation flow: admin invites user → `CustomUser` created inactive with a UUID token + 7-day expiry → user visits `/users/accept/<token>/` to set username/password → account activated, token cleared.
- Email backend: console in development.
- All views require login. Home page and navbar show/hide sections based on `user.is_administrator`.

### Audit Logging

Audit events are logged via Python `logging` (module `userManagement.views` or `helloAssoImporter`). Events logged:
- `ROLE_CHANGE`, `INVITE_SENT`, `INVITE_ACCEPTED`, `USER_DELETE` (userManagement)
- `MEMBER_EMAIL_CHANGE`, `MEMBER_MERGE`, `ADMIN_DELETE`, `SEASON_DELETE` (helloAssoImporter)
- `DeleteAuditAdminMixin` in `helloAssoImporter/admin.py` logs cascade deletions from Django admin.

### Member Duplicate Management

- `member_duplicates` view groups members with identical names.
- `member_detail` view shows a member's orders and suggests merge candidates (matching name).
- `member_merge` view merges two members (atomic): reassigns orders from source to target, deletes source. Protected against open-redirect via `url_has_allowed_host_and_scheme`.

### URL Structure

| Prefix | App / Purpose |
|---|---|
| `/` | Home (`userManagement.HomeView`) |
| `/admin/` | Django admin |
| `/accounts/` | allauth auth (login/logout) |
| `/invitations/` | django-invitations |
| `/inscriptions/` | helloAssoImporter — events list, refresh, create (WIP) |
| `/saison/` | helloAssoImporter — seasons, membership forms, members |
| `/users/` | userManagement — user list, invite, role, password |

#### `/inscriptions/` routes
| URL | View | Name |
|---|---|---|
| `/inscriptions/` | EventFormListView | `inscriptions` |
| `/inscriptions/refresh/` | refresh_event_forms | `inscriptions-refresh` |
| `/inscriptions/create/` | create_event_form | `event-form-create` |
| `/inscriptions/<form_slug>/` | EventFormDetailView | `event-form-detail` |

#### `/saison/` routes
| URL | View | Name |
|---|---|---|
| `/saison/` | MemberShipFormListView | `saison-formulaires` |
| `/saison/refresh/` | refresh_membership_forms | `saison-refresh` |
| `/saison/assign-season/` | assign_season | `saison-assign` |
| `/saison/gestion/` | season_gestion | `saison-gestion` |
| `/saison/formation/` | formation | `saison-formation` |
| `/saison/set-current/<pk>/` | set_current_season | `saison-set-current` |
| `/saison/delete/<pk>/` | delete_season | `saison-delete` |
| `/saison/membres/` | member_list | `saison-membres` |
| `/saison/membres/doublons/` | member_duplicates | `saison-membres-doublons` |
| `/saison/membres/<pk>/` | member_detail | `saison-membre-detail` |
| `/saison/membres/fusionner/` | member_merge | `saison-membres-fusionner` |
| `/saison/<form_slug>/` | membership_form_detail | `saison-form-detail` |

### Templates

All templates use inline CSS defined in `templates/base.html` — there are no separate static CSS files. JavaScript for table sorting/filtering and clipboard copy is also inline in templates.

- `templates/base.html` — HTML5 base, embedded responsive CSS, navbar (shows/hides by role)
- `templates/home.html` — Dashboard with app cards
- `templates/account/` — allauth login/signup/logout
- `templates/userManagement/` — user_list, user_role_form, invite, accept_invite, change_password
- `helloAssoImporter/templates/helloAssoImporter/` — event_forms, event_form_detail, event_form_create, membership_forms, membership_form_detail, member_list, member_duplicates, member_detail, season_gestion, saison_base, formation

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| django | ^5.2.4 | Web framework |
| helloasso-python | ^1.0.8 | HelloAsso API SDK (OpenAPI/Pydantic) |
| django-allauth | ^65.14.3 | Auth (login/signup) |
| django-invitations | ^2.1.0 | Invitation system |
| django-tables2 | ^2.7.5 | Table rendering (dependency, minimal direct use) |
| requests | ^2.32.4 | HTTP (OAuth2 token fetch) |
| authlib | ^1.6.9 | Auth utilities |
| gunicorn | ^23.0.0 | WSGI server |
| psycopg2-binary | ^2.9.10 | PostgreSQL driver |
| dj-database-url | ^2.3.0 | Parse DATABASE_URL env var |
| whitenoise | ^6.9.0 | Static file serving |
| python-dotenv | (via dotenv ^0.9.9) | Load .env files |

### Database

- **Development**: SQLite (`db.sqlite3`), auto-used when `DATABASE_URL` is not set.
- **Production**: PostgreSQL via `DATABASE_URL` env var (parsed by `dj-database-url`).

### Static Files

Served by WhiteNoise (`CompressedManifestStaticFilesStorage`). Run `python manage.py collectstatic` before deploying.

## Known Issues / WIP

- **S11 (Open)**: Race condition on `Member` creation — `get_or_create` on `(email, first_name, last_name)` is not atomic under concurrent writes. Low risk in practice (no concurrent imports).
- **Event creation**: `create_event_form()` requires the `FormAdministration` HelloAsso API privilege, which is not yet activated. The UI button shows "WIP".
- **Tests**: Minimal test coverage — `userManagement/tests.py` is an empty placeholder. No tests in `helloAssoImporter`.

## Deployment

See `deploy/DEPLOY.md` for production deployment instructions (PostgreSQL, gunicorn, environment variables, collectstatic).
