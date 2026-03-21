# Future Features — TODO

Features planned but not yet implemented. For context on what's already built, see `FEATURES.md`.

---

## 1. Message Attachments (Images + Documents)

**Status:** Next up

Models and agencies need to share images and documents in conversations.

### Requirements
- **Images**: JPEG/PNG/WEBP only, max 8MB per file, lightbox zoom on click
- **Documents**: PDF, DOCX, XLSX/CSV only, download on click
- **Access control**: files must NOT be accessible by anyone outside the conversation, even with a direct URL
- **Storage**: Cloudflare R2 (same as portfolio images)
- **UI**: attachment button next to message input, inline preview for images, file card for documents

### Security
- Serve files through a Django view that checks conversation membership before streaming
- Never expose direct S3/R2 URLs to the client
- Validate file type server-side (don't trust content-type header alone — check magic bytes)
- Rate limit uploads

---

## 2. Email Notifications

**Status:** Not started, SMTP is configured

- Notify users via email when they get a new follower, message request, agency request, or application status change
- Respect user preferences (opt-in/opt-out per notification type)
- Add notification preferences to edit profile

---

## 3. Social Features (Future)
- Group creation in messaging
- Instagram integration (pull portfolio from IG)

---

## 4. Custom Profile URLs (LinkedIn-style)
Allow models to have `/models/@username` or `/@username` URLs instead of the auto-generated slug:
- Add URL pattern for `/@<username>/`
- Keep slug-based URLs working as redirects
- Allow users to edit their username (with cooldown to prevent abuse)
- Update all internal links (messaging, notifications, follows) to use username URLs

---

## Ideas / Backlog

- **Agency self-assignment guard**: currently models can add themselves to any agency via edit-profile (`represented_by_agency` field). This is fine at current scale but should be locked down when user count grows — make roster membership agency-staff-only, remove the field from `OnboardingForm`, add an "agency invitation" flow instead.
- **Deleted account PII cleanup**: `delete_account` anonymizes user email but not `ModelProfile.contact_email` and `phone_number`. Should clear those too for GDPR compliance.
- **Portfolio slug uniqueness**: `PortfolioPost.slug` is not unique per owner — duplicate-title posts silently collide. Add `unique_together = [("owner_profile", "slug")]`.
- **Agency slug collision handling**: `Agency.save()` does `slugify(name)` with no counter suffix. Two agencies with same name = `IntegrityError`. Copy the `ModelProfile.save()` pattern.
