from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += []  # noqa: F405 - add dev-only apps here if needed

# In development, serve media files via Django
# (handled in urls.py with static() helper)

_email_host = env("EMAIL_HOST_USER", default="")
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@modellingdirectory.com")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = "noreply@modellingdirectory.com"
