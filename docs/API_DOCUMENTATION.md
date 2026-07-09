# Quicker-X API Documentation — Phase 1

Base URL: `/api/v1/`
Interactive docs (once running): `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc), raw schema at `/api/schema/`.

## Standard response envelope

Every endpoint — success or failure — returns this shape:

```json
{
  "success": true,
  "message": "Human-readable summary",
  "data": { },
  "errors": null,
  "timestamp": "2026-07-05T12:00:00.000000+00:00",
  "request_id": "b3f1c2e4-...-uuid"
}
```

`request_id` is generated per-request by `RequestIDMiddleware`, echoed in the `X-Request-ID` response header, and included in server logs — pass it back to support/engineering when debugging a specific call.

## Authentication

JWT via `Authorization: Bearer <access_token>`. Access tokens are short-lived (15 min default); use `/auth/refresh/` to rotate.

---

## Customer Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register/` | Public | Body: `phone_number`, `full_name`, `password`. Creates a Customer account. Sends a 4-digit SMS OTP for phone verification. |
| POST | `/auth/login/` | Public | Body: `phone_number`, `password`, optional `device_id`/`device_type`/`fcm_token`. Returns `access` + `refresh` tokens. |
| POST | `/auth/logout/` | Bearer | Blacklists the given `refresh` token. |
| POST | `/auth/refresh/` | Public (refresh token in body) | Rotates the refresh token, returns new `access` + `refresh`. |
| POST | `/auth/forgot-password/` | Public | Body: `phone_number`. Sends a 4-digit SMS OTP if the account exists (response is identical either way, to avoid account enumeration). |
| POST | `/auth/reset-password/` | Public | Body: `phone_number`, `otp` (4 digits), `new_password`. Revokes all existing sessions on success. |
| POST | `/auth/verify-otp/` | Public | Generic OTP verification. Body: `target` (phone number), `purpose`, `otp` (4 digits). |
| POST | `/auth/change-password/` | Bearer | Body: `current_password`, `new_password`. |

> **Identifier note:** every customer-facing auth screen in the delivered mockups (Login, Register, Forgot Password, OTP) collects a mobile number and never an email — so `phone_number` is the JWT `USERNAME_FIELD` and the only required identifier at signup. `email` still exists on the `User` model but is optional and unused by any Phase 1 screen.
>
> **SMS delivery note:** no SMS provider is wired up yet (`apps.otp.services._deliver_otp` is a stub for the SMS channel). In `DEBUG` mode the generated OTP is written to the Django server log so it can be used for local Flutter testing — plug in Twilio/MSG91/etc. before shipping.

## Customer Profile

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/me/` | Bearer | Full profile: identity, `profile` sub-object, `addresses`, `roles`. |
| PATCH | `/users/me/` | Bearer | Partial update; nested `profile` object is merged. |
| GET / POST | `/users/me/addresses/` | Bearer | List / add delivery addresses. |
| GET / PATCH / DELETE | `/users/me/addresses/{id}/` | Bearer | Manage a single address (delete = soft delete). |
| POST | `/users/me/devices/` | Bearer | Register/update a device for push notifications + session tracking. |

## Shop Owner

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/shop-owner/register-request/` | Public (multipart) | Full registration form + documents/images. Creates a login-gated account + a `PENDING` request. |
| POST | `/shop-owner/login/` | Public | Only succeeds if the linked request is `APPROVED`. |

## Admin — Shop Owner Approval

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/admin/shop-owner/pending/` | Admin/Super Admin | List all pending requests with full document/image metadata. |
| PATCH | `/admin/shop-owner/{id}/approve/` | Admin/Super Admin | Approves; shop owner can now log in. |
| PATCH | `/admin/shop-owner/{id}/reject/` | Admin/Super Admin | Body: `reason`. |

## Admin — User Management

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/admin/users/` | Admin/Super Admin | Filter with `?account_type=`, `?is_active=`, search via `?search=`. |
| PATCH | `/admin/users/{id}/activate/` | Admin/Super Admin | |
| PATCH | `/admin/users/{id}/deactivate/` | Admin/Super Admin | Also revokes all active sessions. |
| DELETE | `/admin/users/{id}/` | Admin/Super Admin | Soft delete only. Blocked for superuser accounts. |
| POST | `/admin/users/{id}/reset-password/` | Admin/Super Admin | Issues a temporary password (wire up email delivery in Phase 2). |
| GET | `/admin/users/{id}/login-history/` | Admin/Super Admin | Read-only audit trail. |

## Admin — Roles & Permissions

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/POST | `/roles/` | Admin/Super Admin | List/create roles. |
| GET/PATCH/DELETE | `/roles/{id}/` | Admin/Super Admin | |
| POST | `/roles/assign-permission/` | Admin/Super Admin | Body: `role_id`, `permission_id`. |
| GET/POST | `/roles/permissions/` | Admin/Super Admin | List/create fine-grained permissions. |
| GET/PATCH/DELETE | `/roles/permissions/{id}/` | Admin/Super Admin | |

## Admin authentication

Per spec, Admin/Super Admin sign in with Django Admin credentials at `/django-admin/` for back-office work (approving shops, managing roles). For the React Admin Panel to call the same JWT-protected `/api/v1/admin/...` endpoints, use `/auth/login/` with an Admin/Super Admin account — `is_staff` users get both Django Admin access *and* API access through the same `users` row (single source of truth, no separate login table, per spec).

## Error format

Validation errors, auth failures, permission errors, and 404s are all normalized through `apps.core.exceptions.custom_exception_handler` into the same envelope, with `success: false`, a human `message`, and DRF's field-level detail under `errors`.
