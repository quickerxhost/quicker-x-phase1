# Quicker-X Backend — Phase 1

Production-grade Django REST Framework backend for the Quicker-X marketplace platform.
This delivery covers **Phase 1 scope only**: project foundation, authentication, customer
registration/profile, shop-owner registration + admin approval workflow, admin/role
management, Cloudinary integration, and API documentation.

## Stack

Python 3.12 · Django 5.2 · DRF · PostgreSQL (Neon) · SimpleJWT · Cloudinary · drf-spectacular (Swagger/OpenAPI)

## Project layout

```
quicker_x_backend/
├── config/                    # settings, root urls, wsgi/asgi
│   └── settings/
│       ├── base.py            # shared settings
│       ├── development.py
│       └── production.py
├── apps/
│   ├── core/                  # BaseModel, response envelope, exception handler,
│   │                          # pagination, permissions, request-id middleware
│   ├── users/                 # User model (single auth table), auth flows,
│   │                          # admin user-management, JWT customization
│   ├── profiles/               # UserProfile (1:1), "me" serializer
│   ├── roles/                 # Role, Permission, RolePermission, UserRole (RBAC)
│   ├── otp/                    # OTPVerification model + generate/verify service
│   ├── devices/                # UserDevice, RefreshToken (session management)
│   ├── addresses/              # Address (customer + reusable elsewhere)
│   ├── shop_owner/             # Registration request, documents, images,
│   │                          # Cloudinary service, admin approval workflow
│   └── audit/                  # LoginHistory (append-only)
├── docs/
│   ├── DATABASE_SCHEMA.md      # ER diagram + table-by-table notes
│   └── API_DOCUMENTATION.md    # full endpoint reference
├── postman/
│   └── QuickerX.postman_collection.json
├── requirements.txt
└── .env.example
```

## Getting started

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in DB_*, CLOUDINARY_*, EMAIL_*, DJANGO_SECRET_KEY

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Swagger UI: `http://localhost:8000/api/docs/`
Django Admin: `http://localhost:8000/django-admin/`

## Architecture decisions worth knowing

1. **Single `users` table, no separate login tables.** `account_type` distinguishes
   Customer / Shop Owner / Admin / Super Admin, and `apps.roles` layers RBAC on top for
   finer-grained permission checks — matches the spec exactly.

2. **Standard response envelope everywhere.** `apps.core.responses.success_response` /
   `error_response`, enforced for errors via a custom DRF exception handler, so every
   client (Flutter x2, React) can parse one shape.

3. **Soft delete by default.** `BaseModel` never hard-deletes; `objects` (default
   manager) filters `is_deleted=False` automatically, `all_objects` sees everything.
   Admin's "Delete User" is soft-delete only, per spec.

4. **Shop Owner gating.** A `User` row + `ShopOwnerRegistrationRequest` are created
   together at submission time (single transaction), but `shop-owner/login/` and the
   `IsApprovedShopOwner` permission both check `status == APPROVED` — so the account
   *exists* immediately (clean pending/rejected error messages) but can't actually
   authenticate into shop-owner-only endpoints until an admin approves it.

5. **Cloudinary metadata-only storage.** `apps.shop_owner.services.cloudinary_service`
   is the single code path that talks to the Cloudinary SDK; only `public_id`,
   `secure_url`, `resource_type`, `width`, `height`, `bytes`, `folder`, `version`,
   `format` are ever persisted in Postgres.

6. **Session management.** Every login binds a `RefreshToken` row to a `UserDevice`
   row. Deactivating a user, admin-resetting a password, or a user-initiated password
   reset revokes every outstanding refresh token for that user — a real "log out
   everywhere," on top of SimpleJWT's own rotate/blacklist mechanics.

## What still needs your input before this goes to production

- **Shop Owner form fields**: `ShopOwnerRegistrationRequest` currently models a
  best-practice superset of fields (owner identity, business identity, GSTIN/PAN/FSSAI,
  address, bank details). It has **not** been reconciled against your actual Flutter
  Shop Owner UI screens field-by-field — do that before running `makemigrations` for real.
- **SMS OTP provider**: `apps.otp.services._deliver_otp` has an email path wired to
  Django's SMTP backend; the SMS branch is a no-op placeholder — plug in
  Twilio/MSG91/etc.
- **Migrations**: not generated in this delivery (no network/DB access in this
  environment) — run `makemigrations`/`migrate` yourself against your Neon instance.
- **Permission/module seed data**: `roles`/`permissions` tables are empty by default
  beyond the four auto-created roles (Customer/Shop Owner/Admin/Super Admin) — write a
  data migration or management command to seed your actual permission catalog.

## Next natural steps (Phase 2 candidates)

Product catalog, cart/orders, payments, notifications, shop-owner dashboard endpoints,
search, and the `permissions` module actually being enforced with fine-grained checks
(currently role-level checks are wired; permission-level checks have the table but no
consuming logic yet — add `HasPermission("module.action")` alongside `HasRole` once
Phase 2 defines the real action list).
