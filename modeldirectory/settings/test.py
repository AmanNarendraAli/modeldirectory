from .base import *  # noqa

DEBUG = False

# Use SQLite for fast test execution (no Postgres dependency)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@test.com"

# Disable imagekit processing in tests
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = "imagekit.cachefiles.strategies.Optimistic"
