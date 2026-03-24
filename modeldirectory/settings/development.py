from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += []  # noqa: F405 - add dev-only apps here if needed

# In development, serve media files via Django
# (handled in urls.py with static() helper)

_resend_key = env("RESEND_API_KEY", default="")
if _resend_key:
    INSTALLED_APPS += ["anymail"]  # noqa: F405
    ANYMAIL = {"RESEND_API_KEY": _resend_key}
    EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL_PROD", default="noreply@themodellingdirectory.in")
elif env("EMAIL_HOST_USER", default=""):
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
