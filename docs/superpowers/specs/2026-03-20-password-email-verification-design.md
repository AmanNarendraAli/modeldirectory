# Design: Change Password, Email Verification, Forgot Password

## Problem

Users have no way to change their password, verify their email, or recover a lost account. These are table-stakes features for any platform handling user accounts.

## Decisions

- **Approach:** Django built-in auth views + minimal custom code for email verification
- **Email verification trigger:** On signup, with persistent banner until verified
- **Feature gating:** None — unverified users can use all features, just see a banner
- **Forgot password gate:** Only verified users can reset (prevents sending to mistyped emails)
- **Email style:** Branded and warm ("Welcome! Please verify your email")

---

## Feature 1: Change Password

**No new views, models, or URLs.** Django's `PasswordChangeView` is already available via `django.contrib.auth.urls` (included at `modeldirectory/urls.py:15`).

### Templates to create

`templates/registration/password_change_form.html`
- White card layout matching login page (stone palette, font-display heading)
- Fields: old_password, new_password1, new_password2
- "Update Password" submit button
- "Cancel" link back to dashboard

`templates/registration/password_change_done.html`
- Same card layout
- "Password updated" heading
- "Back to Dashboard" link (use `/dashboard/`)

### Entry points

`templates/dashboard/edit_profile.html` (before Danger Zone, ~line 468):
```html
<section class="border border-stone-200 rounded-xl p-6">
    <h2 class="font-semibold text-stone-900 text-lg mb-2">Password</h2>
    <p class="text-sm text-stone-500 mb-4">Change your account password.</p>
    <a href="{% url 'password_change' %}">Change Password</a>
</section>
```

`templates/dashboard/edit_agency.html` (before Danger Zone, ~line 373): identical section.

---

## Feature 2: Email Verification

### New file: `apps/accounts/emails.py`

`send_verification_email(user, request)`:
- Generate token: `default_token_generator.make_token(user)`
- Encode user ID: `urlsafe_base64_encode(force_bytes(user.pk))`
- Build absolute URL: `request.build_absolute_uri(reverse('verify-email', args=[uidb64, token]))`
- Render HTML email from `templates/accounts/emails/verify_email.html`
- Send via `send_mail` with `_get_from_email()` from `apps/core/emails.py`
- **Wrap in try/except** following existing pattern in `apps/core/emails.py` — log error but don't crash signup

### New views in `apps/accounts/views.py`

`verify_email(request, uidb64, token)`:
- Decode uidb64 → get user
- **If user already verified:** redirect to success page (handles repeat clicks)
- Check token via `default_token_generator.check_token(user, token)`
- If valid: set `user.is_verified_email = True`, save, show success page
- If invalid/expired: show error page with resend link. Note: changing password invalidates pending verification tokens (they share `default_token_generator`). Error page should say "Link expired or invalid — request a new one."
- No login required (user clicks link from email, may not be logged in)

`resend_verification(request)`:
- POST only, `@login_required`, rate-limited (`@ratelimit(key="user", rate="3/h")`)
- **If already verified:** redirect with info message, don't send email
- Call `send_verification_email(request.user, request)`
- Redirect back with success message

### Signup integration

In `SignupView.form_valid` (`apps/accounts/views.py`), after `login()`:
- Call `send_verification_email(user, self.request)`
- Email prints to terminal in dev (console backend), sends via Gmail in prod

### Verification banner

In `templates/base.html`, after the messages block (~line 63), before `<main>`:
```html
{% if user.is_authenticated and not user.is_verified_email %}
<div class="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-center text-sm text-amber-800">
    Please verify your email ({{ user.email }}).
    <form method="post" action="{% url 'resend-verification' %}" class="inline">
        {% csrf_token %}
        <button type="submit" class="underline font-medium">Resend</button>
    </form>
</div>
{% endif %}
```

### Email template

`templates/accounts/emails/verify_email.html`:
- Subject: "Welcome! Please verify your email"
- Body: short welcome message, "Verify Email" button (link), plain URL fallback
- Token valid for 3 days (`PASSWORD_RESET_TIMEOUT` default). Note: verification and reset tokens share this timeout since both use `default_token_generator`

### Verification success/error pages

`templates/accounts/verify_email_done.html` — "Email verified!" card with dashboard link
`templates/accounts/verify_email_invalid.html` — "Link expired or invalid" card with resend button

### URLs (in `apps/accounts/urls.py`)

- `verify-email/<uidb64>/<token>/` → `verify_email` (name: `verify-email`)
- `resend-verification/` → `resend_verification` (name: `resend-verification`)

---

## Feature 3: Forgot Password

### Custom view: `VerifiedPasswordResetView`

Subclass Django's `PasswordResetView` in `apps/accounts/views.py`.

Set `email_template_name = "accounts/emails/password_reset_email.html"` on the class.

Override `form_valid`:
- Look up user by email
- If user exists and `is_verified_email == False`: show the same neutral "check your inbox" page (don't leak verified/unverified status). Optionally send a different email telling them to verify first.
- If user exists and `is_verified_email == True`: call `super().form_valid(form)` (Django sends reset email)
- If user doesn't exist: show the same "check your inbox" page (don't reveal whether account exists)
- **All three cases show the same page** to prevent account enumeration

### URL override

In `modeldirectory/urls.py` root `urlpatterns`, add as a standalone `path(...)` BEFORE line 15 (`django.contrib.auth.urls` include). Do NOT add inside `apps/accounts/urls.py` — it would never be reached since `django.contrib.auth.urls` is checked first.
```python
path("accounts/password_reset/", VerifiedPasswordResetView.as_view(), name="password_reset"),
```
This takes precedence over Django's default. The other 3 reset URLs (`done`, `confirm`, `complete`) use Django defaults — just need styled templates.

### Templates to create (in `templates/registration/`)

`password_reset_form.html` — "Enter your email" card with email field + submit
`password_reset_done.html` — "Check your inbox" card
`password_reset_confirm.html` — "Set new password" card (new_password1, new_password2)
`password_reset_complete.html` — "Password reset!" card + login link

### Reset email template

`templates/accounts/emails/password_reset_email.html`:
- Subject: "Reset your password"
- "Reset Password" button + plain URL fallback
- Token valid for 3 days

### Login page entry point

`templates/registration/login.html` (~line 63, after form):
- Add "Forgot password?" link to `/accounts/password_reset/`

---

## Files Summary

### New files
```
apps/accounts/emails.py                              — send_verification_email helper
templates/registration/password_change_form.html      — change password form
templates/registration/password_change_done.html      — change password success
templates/registration/password_reset_form.html       — forgot password form
templates/registration/password_reset_done.html       — "check inbox" page
templates/registration/password_reset_confirm.html    — set new password form
templates/registration/password_reset_complete.html   — reset success
templates/accounts/emails/verify_email.html           — verification email body
templates/accounts/emails/password_reset_email.html   — reset email body
templates/accounts/verify_email_done.html             — verification success
templates/accounts/verify_email_invalid.html          — verification failed
```

### Modified files
```
apps/accounts/views.py          — verify_email, resend_verification views, send email on signup, VerifiedPasswordResetView
apps/accounts/urls.py           — verify-email + resend-verification routes
modeldirectory/urls.py          — custom password_reset URL before auth.urls
templates/base.html             — verification banner
templates/registration/login.html — "Forgot password?" link
templates/dashboard/edit_profile.html — "Change Password" section
templates/dashboard/edit_agency.html  — "Change Password" section
```

### Existing code to reuse
- `apps/core/emails.py` → `_get_from_email()` helper
- `django.contrib.auth.tokens.default_token_generator` → token generation/validation
- `django.utils.http.urlsafe_base64_encode/decode` → user ID encoding
- `django.contrib.auth.views.PasswordChangeView` → change password (no custom view needed)
- `django.contrib.auth.views.PasswordResetView` → base class for forgot password

---

## Verification

| Test | Steps | Expected |
|------|-------|----------|
| Change password | Edit profile → Change Password → fill form correctly | Redirects to done page, can login with new password |
| Wrong current password | Enter incorrect current password | Form error shown |
| Weak password | Enter too-short password | Django validator error |
| Verification email on signup | Create new account | Email prints to terminal (dev) with verify link |
| Click verify link | Click link from email | `is_verified_email` set to True, banner disappears |
| Expired verify link | Wait or use invalid token | Error page with resend button |
| Resend verification | Click resend in banner | New email sent, success message |
| Forgot password (verified) | Login page → Forgot password → enter email | Reset email sent, can set new password |
| Forgot password (unverified) | Same flow but with unverified email | Same "check inbox" page (no info leak) |
| Forgot password (no account) | Enter email that doesn't exist | Same "check inbox" page (no info leak) |
| Click verify link twice | Click same link again after verifying | Redirects to success (not error) |
| Resend when already verified | POST to resend-verification | Redirect with info message, no email sent |
| Signup email failure | SMTP down during signup | Signup succeeds, email failure logged |
| Local dev email | All email flows in development | Emails print to terminal via console backend |
