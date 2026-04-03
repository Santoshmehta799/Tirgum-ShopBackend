from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "www.tirgumpanel.pl",
    "tirgumpanel.pl",
    "shop.tirgum.pl",
    "*.tirgum.pl",
    "164.92.130.1",
    # ".ngrok-free.app",
    # ".ngrok.io",
]

CSRF_TRUSTED_ORIGINS = [
    "https://www.tirgumpanel.pl",
    "https://tirgumpanel.pl",
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://www.tirgumpanel.pl",
    "https://tirgumpanel.pl",
    "https://shop.tirgum.pl",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0",
]

# Email settings (should be set in .env on server)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "biuro2.tirgum@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "change-me")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "ravichovatiya121@gmail.com")
CLIENT_NOTIFICATION_EMAIL = os.getenv("CLIENT_NOTIFICATION_EMAIL", "biuro2.tirgum@gmail.com")

# Security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

