from .base import *  # noqa

DEBUG = False

# Production-specific overrides go here:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# STATIC_ROOT, whitenoise, S3 storage, etc.

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@modellingdirectory.com")
