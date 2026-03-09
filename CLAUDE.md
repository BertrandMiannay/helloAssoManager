# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application that imports and manages sports club membership data from the [HelloAsso](https://www.helloasso.com/) platform. Managed with Poetry (Python 3.13).

## Commands

```bash
# Install dependencies
poetry install

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Reset dev database (deletes db.sqlite3, re-migrates, creates admin/admin superuser)
python manage.py init_dev_db

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

A `.env` file is required at the project root with:
```
HELLO_ASSO_API_CLIENT_ID=...
HELLO_ASSO_API_CLIENT_SECRET=...
ORGANIZATION_SLUG=...
```

These are loaded by `common/api/helloAssoApi.py` via `python-dotenv`.

## Architecture

### Django Apps

- **`helloAssoImporter/`** — Core data import app. Models: `MemberShipForm` → `MemberShipFormOrder` → `Member` (cascade). All three are registered in Django admin.
- **`userManagement/`** — Custom user model (`CustomUser` extends `AbstractUser`), group-based role system (`admin`, `manager`, `viewer`), invitation-only registration flow.
- **`common/api/helloAssoApi.py`** — Shared `HelloAssoApi` class wrapping the `helloasso-apiv5` library. Handles token auth and all API calls to HelloAsso.
- **`config/`** — Django project settings, root URL conf, ASGI/WSGI.
- **`tpmanagement/`** — Stub directory, currently unused.

### Data Import Flow

`HelloAssoApi` drives a three-step import cascade:
1. `refresh_membership_forms()` — fetches Membership forms from HelloAsso and saves `MemberShipForm` records.
2. `get_form_orders(form)` — fetches orders for a form, saves `MemberShipFormOrder`, then calls step 3 for each.
3. `get_member_registry(order)` — fetches order details, parses custom fields (birth date, email, licence number, sex — field names are in French), saves `Member` records.

The `index` view in `helloAssoImporter/views.py` has the import calls commented out; imports are currently triggered manually or via admin.

### Authentication & Authorization

- `django-allauth` handles login/signup; signup is invitation-only (`INVITATIONS_INVITATION_ONLY = True`).
- `AdminRequiredMixin` restricts views to users in the Django `admin` group.
- All views require login. The home page shows/hides sections based on group membership.
- Email backend is set to console for development.

### URL Structure

| Prefix | App |
|---|---|
| `/` | Home (`userManagement.HomeView`) |
| `/admin/` | Django admin |
| `/accounts/` | allauth auth |
| `/invitations/` | django-invitations |
| `/hello_asso/` | helloAssoImporter |
| `/users/` | userManagement |
