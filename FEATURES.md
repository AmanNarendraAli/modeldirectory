# Feature Documentation

Reference for agents and developers working on this codebase. Covers features built on the `dev` branch that are not yet merged to `main`.

---

## Notifications (`apps/notifications/`)

Real-time notification system with navbar bell icon and full-page list.

### Models

**Notification** (`apps/notifications/models.py`)
- `user` (FK to User) - who receives the notification
- `notification_type` - one of: `follow`, `message_request`, `new_message`
- `actor` (FK to User) - who triggered it
- `target_profile` (FK to ModelProfile, nullable) - for follow notifications
- `target_conversation` (FK to Conversation, nullable) - for messaging notifications
- `is_read` (bool, default False)
- `created_at` (auto)
- `display_text` property returns human-readable text based on type

### Signals (`apps/notifications/signals.py`)

- `post_save` on `Follow` (created only) -> creates FOLLOW notification for the followed profile's user
- Message notifications (MESSAGE_REQUEST, NEW_MESSAGE) are created directly in `apps/messaging/views.py` rather than via signals, to handle agency auto-accept logic cleanly

### Context Processor (`apps/notifications/context_processors.py`)

- `unread_notification_count(request)` injects `{{ unread_notification_count }}` into every template
- Registered in `modeldirectory/settings/base.py` under TEMPLATES context_processors

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
| Agency -> Model | status=accepted immediately, is_agency_initiated=True |
| Model -> Agency | Not allowed (no Message button on agency pages) |
| Existing accepted conv | Messages added directly, no request flow |
| Blocked user | Message button hidden, start_conversation returns error |

### URLs

| URL | View | Name | Method |
|-----|------|------|--------|
| `/messages/` | `inbox` | `message-inbox` | GET |
| `/messages/new/<slug>/` | `start_conversation` | `start-conversation` | POST |
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
- `_attach_other_participant(conversations, user)` - pre-computes `other_participant` on each conversation for templates (Django templates can't call methods with arguments)

**Views:**
- `inbox` - Messages tab (accepted convos) + Requests tab (pending received) + "Waiting for response" (pending sent)
- `conversation_detail` - Full thread, marks other user's messages as read, shows accept/decline/block for pending recipient
- `start_conversation` - Creates conversation + first message. Handles: self-prevention, block checking, existing conversation reuse, declined re-request, agency auto-accept
- `send_message` - Only works for accepted conversations. Creates notification for other participant
- `accept_request` / `decline_request` / `block_user` - Status changes with permission checks (only recipient can accept/decline, either party can block)

### Templates

| Template | Purpose |
|----------|---------|
| `templates/messaging/inbox.html` | Two-tab inbox (Messages/Requests), conversation list with other participant name, last message preview, timestamps |
| `templates/messaging/conversation_detail.html` | Chat bubbles (dark=sender, light=received), pending request banner with Accept/Decline/Block, message input form, auto-scroll to bottom |

### Entry Points

**Model profile page** (`templates/models_app/model_detail.html`):
- "Message" button next to Follow button
- Shows: "Message" link (accepted conv exists), "Request Pending" badge (pending conv), or "Message" button -> modal with textarea (no conv)
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
| `modeldirectory/settings/base.py` | Added `apps.notifications` and `apps.messaging` to INSTALLED_APPS, added notification context processor |
| `modeldirectory/urls.py` | Added `notifications/` and `messages/` URL includes |
| `templates/partials/_navbar.html` | Added Messages link, notification bell include, mobile menu entries |
| `apps/models_app/views.py` | `model_detail` passes messaging context (can_message, existing_conversation, is_blocked) |
| `apps/dashboard/views.py` | `applicant_detail` passes applicant_conversation context |

---

## Test Settings

`modeldirectory/settings/test.py` - Uses SQLite in-memory for fast tests without Postgres dependency.

Run tests:
```bash
.venv/bin/python manage.py test apps.notifications apps.messaging --settings=modeldirectory.settings.test -v2
```

88 tests covering: models, signals, context processors, all views, permission checks, edge cases (blocking, re-requesting, agency auto-accept), and template content verification.

---

## Migrations

- `apps/notifications/migrations/0001_initial.py` - Notification model
- `apps/messaging/migrations/0001_initial.py` - Conversation, Message, MessageBlock models + constraints

Run after starting Postgres:
```bash
.venv/bin/python manage.py migrate
```
