from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "dev@example.com"
CLIENT_NOTIFICATION_EMAIL = "client@example.com"
