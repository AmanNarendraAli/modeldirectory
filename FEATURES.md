# Feature Documentation

Reference for agents and developers working on this codebase. Covers features built on the `dev` branch that are not yet merged to `main`.

---

## Notifications (`apps/notifications/`)

Real-time notification system with navbar bell icon and full-page list.

### Models

**Notification** (`apps/notifications/models.py`)
- `user` (FK to User) - who receives the notification
- `notification_type` - one of: `follow`, `message_request`, `new_message`, `application_status_updated`
- `actor` (FK to User) - who triggered it
- `target_profile` (FK to ModelProfile, nullable) - for follow notifications
- `target_conversation` (FK to Conversation, nullable) - for messaging notifications
- `is_read` (bool, default False)
- `created_at` (auto)
- `target_application` (FK to Application, nullable) - for application status notifications
- `display_text` property returns human-readable text based on type. For `application_status_updated`, shows agency name (from `target_application.agency.name`) rather than the staff member's name.

### Signals (`apps/notifications/signals.py`)

- `post_save` on `Follow` (created only) -> creates FOLLOW notification for the followed profile's user
- Message notifications (MESSAGE_REQUEST, NEW_MESSAGE) are created directly in `apps/messaging/views.py` rather than via signals, to handle agency auto-accept logic cleanly

### Context Processor (`apps/notifications/context_processors.py`)

- `unread_notification_count(request)` injects `{{ unread_notification_count }}` into every template
- `unread_message_indicator(request)` injects `{{ has_unread_messages }}` (bool) into every template — used for red dot on Messages nav link
- Both registered in `modeldirectory/settings/base.py` under TEMPLATES context_processors

### URLs

| URL | View | Name |
|-----|------|------|
| `/notifications/` | `notification_list` | `notification-list` |
| `/notifications/mark-read/` | `mark_notifications_read` | `mark-notifications-read` |

### Views (`apps/notifications/views.py`)

- `notification_list` - Full page (paginated, 20 per page) OR partial HTML fragment (last 5, for dropdown) when `?format=partial`
- `mark_notifications_read` - POST only, marks all unread as read for current user, returns JSON

### Templates

| Template | Purpose |
|----------|---------|
| `templates/partials/_notification_bell.html` | Bell icon + dropdown. Loads notifications via fetch to `?format=partial`. JS marks as read on open. |
| `templates/notifications/_notification_items.html` | Partial for dropdown items (links to profile or conversation) |
| `templates/notifications/notification_list.html` | Full page paginated list with unread indicators |

### Navbar Integration (`templates/partials/_navbar.html`)

- Bell icon with red badge (unread count) between Messages link and Logout
- Mobile menu: "Notifications" link with badge count
- Red dot next to "Messages" link (desktop + mobile) when `has_unread_messages` is true — disappears when conversations are opened

---

## Messaging (`apps/messaging/`)

Model-to-model messaging with request/accept flow. Agency-to-model messaging auto-accepted.

### Models (`apps/messaging/models.py`)

**Conversation**
- `participant_one`, `participant_two` (FK to User)
- `status` - one of: `pending`, `accepted`, `declined`, `blocked`
- `initiated_by` (FK to User)
- `is_agency_initiated` (bool)
- `created_at`, `updated_at` (auto)
- UniqueConstraint on `(participant_one, participant_two)` prevents duplicate conversations
- `get_other_participant(user)` returns the other user
- `is_participant(user)` checks membership
- `last_message` property returns most recent Message

**Message**
- `conversation` (FK to Conversation)
- `sender` (FK to User)
- `content` (TextField)
- `is_read` (bool, default False)
- `created_at` (auto)
- Ordered chronologically (oldest first)

**MessageBlock**
- `blocker`, `blocked` (FK to User)
- `unique_together` on `(blocker, blocked)`
- Checked in views to prevent messaging between blocked users

### Conversation Rules

| Scenario | Behavior |
|----------|----------|
| Model -> Model (new) | status=pending, first message saved, sender can't send more until accepted |
| Recipient accepts | status=accepted, both can message freely |
| Recipient declines | status=declined, removed from recipient's inbox, sender can re-request later |
| Recipient blocks | MessageBlock created, status=blocked, sender can never request again |
| Agency -> Model (new) | status=accepted immediately, is_agency_initiated=True. No modal/request flow — direct redirect to chat |
| Agency hits pending conv | Auto-accepts the conversation regardless of who initiated it |
| Agency hits declined conv | Resets to accepted (not pending) |
| Model -> Agency | Not allowed (no Message button on agency pages) |
| Existing accepted conv | Messages added directly, no request flow |
| Blocked user | Message button hidden, start_conversation returns error |

### URLs

| URL | View | Name | Method |
|-----|------|------|--------|
| `/messages/` | `inbox` | `message-inbox` | GET |
| `/messages/search/` | `search_users_for_messaging` | `search-users-for-messaging` | GET |
| `/messages/new/<slug>/` | `start_conversation` | `start-conversation` | POST |
| `/messages/new-by-user/<user_id>/` | `start_conversation_with_user` | `start-conversation-with-user` | POST |
| `/messages/<pk>/` | `conversation_detail` | `conversation-detail` | GET |
| `/messages/<pk>/send/` | `send_message` | `send-message` | POST |
| `/messages/<pk>/accept/` | `accept_request` | `accept-request` | POST |
| `/messages/<pk>/decline/` | `decline_request` | `decline-request` | POST |
| `/messages/<pk>/block/` | `block_user` | `block-user` | POST |

### Views (`apps/messaging/views.py`)

**Helpers:**
- `_get_user_conversations(user)` - returns all conversations for a user
- `_get_or_normalize_conversation(user_a, user_b)` - finds existing conversation between two users (order-independent)
- `_is_blocked(user_a, user_b)` - checks if either user blocked the other
- `_attach_other_participant(conversations, user)` - pre-computes `other_participant`, `other_role_label`, `other_profile_url`, `other_avatar_url`, `other_avatar_full_url` on each conversation. Batch-fetches AgencyStaff for efficiency.

**Views:**
- `inbox` - Messages tab (accepted convos) + Requests tab (pending received) + "Waiting for response" (pending sent). Includes search bar for finding models to message.
- `conversation_detail` - Full thread, marks other user's messages as read, shows accept/decline/block for pending recipient. Pending initiators can send first message if conversation was created via search (no initial message).
- `start_conversation` - Creates conversation + first message (from model profile page). Handles: self-prevention, block checking, existing conversation reuse, declined re-request, agency auto-accept of any pending conversation.
- `start_conversation_with_user` - Creates conversation by user ID (from search). No initial message — user types first message on the conversation detail page. Same checks as `start_conversation`.
- `search_users_for_messaging` - GET endpoint returning JSON. Searches models by `public_display_name`. Excludes self and blocked users. Returns conversation status for each result so frontend knows whether to open existing chat or create new one.
- `send_message` - Works for accepted conversations and first message in pending conversations (from search flow). Creates MESSAGE_REQUEST notification for first message in pending conversations.
- `accept_request` / `decline_request` / `block_user` - Status changes with permission checks (only recipient can accept/decline, either party can block)

### Templates

| Template | Purpose |
|----------|---------|
| `templates/messaging/inbox.html` | Two-tab inbox (Messages/Requests) with search bar (right-aligned). Conversation rows show avatar (lightbox-zoomable), name (clickable to profile), role label pill, last message preview, timestamps. Search dropdown with debounced fetch (250ms). |
| `templates/messaging/conversation_detail.html` | Chat header with clickable avatar + name linking to profile, role label. Message thread, pending request banner with Accept/Decline/Block, message input form, auto-scroll to bottom. |

### Entry Points

**Model profile page** (`templates/models_app/model_detail.html`):
- "Message" button next to Follow button
- Shows: "Message" link (accepted conv exists), "Request Pending" badge (pending conv), or "Message" button (no conv)
- For regular users: opens modal with textarea and "Send Request" button
- For agency staff: direct POST form — no modal, creates accepted conversation and redirects to chat immediately
- Hidden for: own profile, anonymous users, blocked users
- View context from `apps/models_app/views.py` `model_detail`: `can_message`, `existing_conversation`, `is_blocked`

**Applicant detail page** (`templates/dashboard/applicant_detail.html`):
- "Message Applicant" button in sidebar (or "View Messages" if conversation exists)
- Opens modal with textarea, POSTs to start-conversation
- Agency conversations auto-accept
- View context from `apps/dashboard/views.py` `applicant_detail`: `applicant_conversation`

---

## Modified Existing Files

| File | Changes |
|------|---------|
| `modeldirectory/settings/base.py` | Added `apps.notifications` and `apps.messaging` to INSTALLED_APPS, added notification + unread message context processors |
| `modeldirectory/urls.py` | Added `notifications/` and `messages/` URL includes |
| `templates/partials/_navbar.html` | Messages link with unread red dot, notification bell include, mobile menu entries with red dot |
| `apps/models_app/views.py` | `model_detail` passes messaging context (can_message, existing_conversation, is_blocked) |
| `apps/dashboard/views.py` | `applicant_detail` passes applicant_conversation context |
| `apps/accounts/admin.py` | UserAdmin with ModelProfile and AgencyStaff inlines (collapsible) for viewing all user details |

---

## Password & Email Features (`apps/accounts/`)

### Change Password

Uses Django's built-in `PasswordChangeView` — no custom views needed. Just styled templates.

- `templates/registration/password_change_form.html` — 3-field form (old, new, confirm)
- `templates/registration/password_change_done.html` — success card
- Entry points: "Password" section on both `edit_profile.html` and `edit_agency.html` (before Danger Zone)

### Email Verification

Sends verification email on signup with a tokenized link. Persistent amber banner on all pages until verified.

**Views** (`apps/accounts/views.py`):
- `verify_email(uidb64, token)` — no login required, checks already-verified first, then validates token
- `resend_verification()` — POST only, rate-limited, guards against already-verified

**Helper** (`apps/accounts/emails.py`):
- `send_verification_email(user, request)` — generates token via `default_token_generator`, sends HTML email, wrapped in try/except

**Templates:**
- `templates/accounts/emails/verify_email.html` — branded HTML email with verify button
- `templates/accounts/verify_email_done.html` — success card
- `templates/accounts/verify_email_invalid.html` — error card with resend link

**Banner** in `templates/base.html` — amber bar with "Please verify your email" + resend button

**URLs** (`apps/accounts/urls.py`):
- `/accounts/verify-email/<uidb64>/<token>/` → `verify-email`
- `/accounts/resend-verification/` → `resend-verification`

### Forgot Password

Custom `VerifiedPasswordResetView` subclass that gates password reset behind `is_verified_email`. Shows the same neutral "check inbox" page for verified, unverified, and nonexistent accounts (no info leak).

**URL:** Custom `password_reset` path in `modeldirectory/urls.py` BEFORE `django.contrib.auth.urls` to override Django's default.

**Templates** (`templates/registration/`):
- `password_reset_form.html` — email input
- `password_reset_done.html` — "check inbox" card
- `password_reset_confirm.html` — set new password (handles expired links)
- `password_reset_complete.html` — success + login link

**Email:** `templates/accounts/emails/password_reset_email.html` — branded HTML with reset button

**Login page:** "Forgot password?" link added to `templates/registration/login.html`

---

## Test Settings

`modeldirectory/settings/test.py` - Uses SQLite in-memory for fast tests without Postgres dependency.

Run tests:
```bash
.venv/bin/python manage.py test apps.notifications apps.messaging apps.accounts --settings=modeldirectory.settings.test -v2
```

114 tests total: 88 notifications/messaging + 26 accounts (change password, email verification, forgot password, banner, edge cases).

---

## Migrations

- `apps/notifications/migrations/0001_initial.py` - Notification model
- `apps/messaging/migrations/0001_initial.py` - Conversation, Message, MessageBlock models + constraints

Run after starting Postgres:
```bash
.venv/bin/python manage.py migrate
```
