# Password Change & Reset — Workplan

## Goal

Add password management to the app: a styled "Change Password" section in the model edit profile page, and a "Forgot password?" link + flow on the login page. No email verification required for the login flow yet — the templates and UI will be fully built, but actual email delivery depends on SMTP being configured (tracked in Future Improvements).

---

## Design Decisions

### Change Password — in Edit Profile
Placed as a standalone section between the last profile section and the Danger Zone. It's account security, not profile content, so it doesn't belong with the form fields above. Styled with a neutral `border-stone-200` border (not red) to visually separate it from the Danger Zone section below. Contains a single "Change Password" link-style button that routes to `/accounts/password_change/`.

### Forgot Password — on Login Page
A small "Forgot password?" link right-aligned below the password field, matching standard login UI convention (Gmail, Instagram, etc.). Unobtrusive — doesn't compete with the main Log In button. Routes to `/accounts/password_reset/`.

### No custom views needed
Django's `PasswordChangeView` and `PasswordResetView` are already wired up via `include("django.contrib.auth.urls")` in `urls.py`. The only work is:
1. Creating the missing styled templates
2. Adding entry points in the UI

### Email sending is deferred
`PasswordResetView` sends a reset link by email. In production, the email backend is currently `console` (no SMTP configured), so the email won't actually send. The full flow (templates, URL, form) will work end-to-end — it just silently logs instead of sending until SMTP is set up. Users will see the "check your email" confirmation page. This is intentional and noted in Future Improvements.

---

## Steps

### 1. Add "Forgot password?" link to login page

**File:** `templates/registration/login.html`

Add a right-aligned "Forgot password?" anchor between the password field and the submit button:

```html
<div class="flex justify-end mb-6">
    <a href="{% url 'password_reset' %}" class="text-xs text-stone-500 hover:text-stone-800">
        Forgot password?
    </a>
</div>
```

Remove the existing `mb-6` from the password `<div>` (it moves to the forgot password row).

---

### 2. Add "Change Password" section to edit profile

**File:** `templates/dashboard/edit_profile.html`

Insert a new section just above the existing Danger Zone `<section>` (before line 477). Style: neutral stone border, not red.

```html
<section class="border border-stone-200 rounded-xl p-6">
    <h2 class="font-semibold text-stone-900 text-lg mb-2">Password</h2>
    <p class="text-sm text-stone-500 mb-4">Change your account password.</p>
    <a href="{% url 'password_change' %}" class="text-sm font-medium text-stone-700 hover:text-stone-900 border border-stone-300 px-4 py-2 rounded-lg hover:bg-stone-50 transition-colors">
        Change Password
    </a>
</section>
```

---

### 3. Create password change templates

Django looks for these in `templates/registration/`. All styled to match the existing login card (white card, stone palette, `font-display` heading, same input classes).

#### `templates/registration/password_change_form.html`
- Card layout matching login page
- Three fields: current password, new password, confirm new password
- Submit button: "Update Password"
- Back link to edit profile (`{% url 'edit-profile' %}` or browser back)

#### `templates/registration/password_change_done.html`
- Same card layout
- Success message: "Password updated"
- Single link back to dashboard

---

### 4. Create password reset templates

#### `templates/registration/password_reset_form.html`
- Card layout
- Single email field
- Submit button: "Send Reset Link"
- Small note: "We'll send a link to your email if an account exists"
- Back link to login

#### `templates/registration/password_reset_done.html`
- Card layout
- Message: "Check your email — if an account exists for that address, we've sent a reset link"
- Back link to login
- No indication of whether the email exists (security best practice)

#### `templates/registration/password_reset_confirm.html`
- Card layout
- Two fields: new password, confirm new password
- Submit button: "Set New Password"
- Shown when user clicks the link in their email

#### `templates/registration/password_reset_complete.html`
- Card layout
- Message: "Password reset — you can now log in with your new password"
- Link to login page

---

### 5. Test

| Scenario | Steps | Expected |
|---|---|---|
| Change password (logged in) | Edit profile → Change Password → fill form | Redirects to done page, can log in with new password |
| Change password — wrong current | Enter wrong current password | Form error, no change |
| Forgot password — submit email | Login → Forgot password → enter email → submit | Redirect to "check your email" page |
| Forgot password — invalid link | Tamper with reset URL | "Link invalid or expired" message |
| Forgot password — complete flow | Submit email → check console logs → follow URL → set new password | Logs in with new password |
| Forgot password — logged out access | Visit `/accounts/password_change/` while logged out | Redirect to login |

---

## Future Improvements

- **Forgot password email delivery:** The reset email currently logs to console. Once a transactional email service is configured (Resend, Postmark, or Gmail SMTP — tracked in phase5.md Future Improvements under "Email service for production"), reset emails will actually send. No code changes needed beyond setting the SMTP env vars.

- **Email verification on password reset:** Add a check that the account's email is verified before allowing a reset, once the email verification flow is built (also tracked in phase5.md).
