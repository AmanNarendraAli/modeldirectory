# Password Change — Workplan

## Goal

Add a "Change Password" section to both the model and agency staff edit pages, backed by styled templates for Django's built-in password change flow. Forgot password / reset is deferred until the email verification flow is built (see Future Improvements).

---

## Design Decisions

### Change Password — in Edit Profile (both model and agency staff)
Placed as a standalone section between the last profile section and the Danger Zone on both `edit_profile.html` and `edit_agency.html`. It's account security, not profile content, so it sits naturally in this "account settings" zone. Styled with a neutral `border-stone-200` border (not red) to visually separate it from Danger Zone below. Contains a single "Change Password" button that routes to `/accounts/password_change/`.

### No custom view needed
Django's `PasswordChangeView` is already wired via `include("django.contrib.auth.urls")`. Requires login automatically. Only work needed: styled templates + entry point in both edit pages.

### After changing password, redirect back to edit profile
Django's default success redirect for password change is `/accounts/password_change/done/`. We'll override `PASSWORD_CHANGE_REDIRECT_URL` in settings (or use `success_url`) to go back to the relevant dashboard edit page. Since both model and agency staff use the same change view, we'll redirect to a neutral "password updated" confirmation card, with a link back to their dashboard.

---

## Steps

### 1. Add "Change Password" section to model edit profile

**File:** `templates/dashboard/edit_profile.html`

Insert before the Danger Zone `<section>` (currently at line 477):

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

### 2. Add "Change Password" section to agency staff edit page

**File:** `templates/dashboard/edit_agency.html`

Same section, insert before the Danger Zone `<section>` (currently at line 379). Identical markup.

---

### 3. Create password change templates

Styled to match the existing login card (white card, stone palette, `font-display` heading, same input/button classes). Django looks for these in `templates/registration/`.

#### `templates/registration/password_change_form.html`
- Card layout matching login page
- Three fields: current password, new password, confirm new password
- Submit button: "Update Password"
- Cancel link back to the referring edit page (use `Back` / `{% url 'edit-profile' %}`)

#### `templates/registration/password_change_done.html`
- Same card layout
- Heading: "Password updated"
- Short message confirming success
- Link back to dashboard (model or agency — since we can't know which, link to `/` and let the dashboard redirect handle it, or use `request.user` in template to pick the right URL)

---

### 4. Test

| Scenario | Steps | Expected |
|---|---|---|
| Model — change password | Edit profile → Change Password → fill all three fields correctly | Redirects to done page; can log in with new password |
| Agency staff — change password | Edit agency → Change Password → fill form | Same as above |
| Wrong current password | Enter incorrect current password | Form error shown, password unchanged |
| Weak new password | Enter a too-short or too-common password | Django validator error shown |
| Password mismatch | New password ≠ confirmation | Form error shown |
| Logged out access | Visit `/accounts/password_change/` while logged out | Redirected to login page |

---

## Future Improvements

- **Forgot password flow:** Deferred until email verification is built. The intended flow: user must have a verified email → "Forgot password?" on login page sends a reset link to that verified address → user clicks link → lands on password reset confirm page → sets new password → redirected to login. Requires: SMTP configured, email verification flow complete, and custom `PasswordResetView` that checks `is_verified_email` before sending. All reset templates (`password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`) to be built at that time.

---

## Email Setup (prerequisite for forgot password + email verification)

Email sending is required for the forgot password flow and for email verification on signup. The production settings are already wired to read SMTP credentials from env vars — nothing needs changing in code. It just needs the credentials to exist.

### Recommended approach: Gmail SMTP (free, good for early stage)

Use a dedicated Gmail account for the app (e.g., `themodellingdirectory@gmail.com`). Later, migrate to a custom domain + Resend/Postmark when you want `noreply@themodellingdirectory.com`.

---

### You do this (manual steps)

1. **Create a Gmail account** for the app — e.g., `themodellingdirectory@gmail.com`
   - Use a real account you control; don't use your personal Gmail

2. **Enable 2-Step Verification** on that Google account
   - Google Account → Security → 2-Step Verification → Turn on

3. **Create an App Password**
   - Google Account → Security → 2-Step Verification → App passwords (at the bottom)
   - Select app: "Mail", device: "Other" → name it "Django" → Generate
   - Copy the 16-character app password shown — this is your `EMAIL_HOST_PASSWORD`
   - Note: App passwords only work if 2FA is enabled

4. **Add these env vars on Render:**
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=themodellingdirectory@gmail.com
   EMAIL_HOST_PASSWORD=<16-char app password>
   DEFAULT_FROM_EMAIL=The Modelling Directory <themodellingdirectory@gmail.com>
   ```

5. **Update your local `.env`** with the same values for local testing

---

### Claude does this (code changes — none needed now)

`production.py` already reads all five env vars above and configures the SMTP backend when `EMAIL_HOST_USER` is set. No code changes required. When the forgot password and email verification flows are built, the email-sending code will be written at that time.

---

### Limitation to know about

Gmail SMTP has a **500 emails/day** cap on free accounts. For a directory with many users, you'd eventually want to migrate to Resend (3,000 emails/month free, custom domain, better deliverability). That migration is just a credentials swap — no code changes.

---

### Test (once env vars are set on Render)

| Scenario | Steps | Expected |
|---|---|---|
| Basic send | In Django shell on Render: `from django.core.mail import send_mail; send_mail('test', 'body', None, ['your@email.com'])` | Email arrives in inbox |
| From address | Check received email | Shows "The Modelling Directory" as sender name |
