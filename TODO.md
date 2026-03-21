# Future Features — TODO

Features planned but not yet implemented. For context on what's already built, see `FEATURES.md`.


### Future: Custom Profile URLs (LinkedIn-style)
Allow models to have `/models/@username` or `/@username` URLs instead of the auto-generated slug. This is a bigger change:
- Add URL pattern for `/@<username>/`
- Keep slug-based URLs working as redirects
- Allow users to edit their username (with cooldown to prevent abuse)
- Update all internal links (messaging, notifications, follows) to use username URLs

---

## 1. Email Notifications

**Status:** Not started, depends on SMTP setup (now complete)

- Notify users via email when they get a new follower, message request, agency request, or their application to an agency changes
- Respect user preferences (opt-in/opt-out per notification type)
- Add notification preferences to edit profile

---

## 2. Social Features (Future)
- GROUP CREATION in messaging
- Instagram integration (pull portfolio from IG)
