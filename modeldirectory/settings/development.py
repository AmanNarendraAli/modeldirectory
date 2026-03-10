from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += []  # noqa: F405 - add dev-only apps here if needed

# In development, serve media files via Django
# (handled in urls.py with static() helper)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@modellingdirectory.com"
