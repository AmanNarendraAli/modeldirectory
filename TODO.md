# Future Features — TODO

Features planned but not yet implemented. For context on what's already built, see `FEATURES.md`.

---

## 1. Unique Usernames

**Status:** Not started

Add a unique username system to the platform.

### Requirements
- Minimum 3 characters
- Allowed characters: letters (a-z), numbers (0-9), hyphens (-), periods (.)
- Case-insensitive (store lowercase, validate lowercase)
- Must be unique across all users
- No leading/trailing hyphens or periods
- No consecutive hyphens/periods (e.g. `a--b` or `a..b` not allowed)
- Reserved words list: `admin`, `staff`, `support`, `help`, `api`, `www`, `mail`, etc.

### Implementation Plan
- Add `username` field to `User` model in `apps/accounts/models.py` (CharField, unique, max_length=30, blank initially for existing users)
- Add regex validator: `^[a-z0-9][a-z0-9.\-]{1,28}[a-z0-9]$`
- Add to signup form (`apps/accounts/forms.py` SignupForm)
- Add to onboarding form or as a separate step
- Add to edit profile page
- Show on model profile pages and model list cards
- Use in messaging (display @username instead of full name where appropriate)

### Future: Custom Profile URLs (LinkedIn-style)
After usernames are stable, allow models to have `/models/@username` or `/@username` URLs instead of the auto-generated slug. This is a bigger change:
- Add URL pattern for `/@<username>/`
- Keep slug-based URLs working as redirects
- Allow users to edit their username (with cooldown to prevent abuse)
- Update all internal links (messaging, notifications, follows) to use username URLs

---

## 2. Email Verification Flow

**Status:** Blocked (need Gmail 2FA setup — see `passwordchange.md` for SMTP instructions)

### Requirements
- On signup, send verification email with a token link
- DIY with Django's `default_token_generator` + `uidb64` encoding
- Unverified users can still use the platform but see a banner prompting verification
- Required before: forgot password, email notifications

### Implementation Plan
- Add verification view that checks token + marks `is_verified_email = True`
- Add email template for verification link
- Add banner to base.html for unverified users
- Gate forgot-password behind verified email

---

## 3. Change Password + Forgot Password

**Status:** Planned (see `passwordchange.md` for full workplan)

- Change password: section on edit profile pages, uses Django's built-in `PasswordChangeView`
- Forgot password: requires email verification first, uses Django's `PasswordResetView`
- Styled templates for all password flow pages
- See `passwordchange.md` for step-by-step implementation details

---

## 4. Email Notifications

**Status:** Not started, depends on email verification + SMTP setup

- Notify users via email when they get a new follower, message request, or new message
- Respect user preferences (opt-in/opt-out per notification type)
- Add notification preferences to edit profile

---

## 5. Social Features (Future)

- Instagram integration (pull portfolio from IG)
- Share profile links
- Model-to-model connections (beyond messaging)
