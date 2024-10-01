from .base import *
from decouple import config
from pathlib import Path

DEBUG = config("DEBUG", default=False, cast=bool)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")], default="*"
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    cast=lambda v: [s.strip() for s in v.split(",")],
    default="http://*,https://*",
)
CORS_ORIGIN_WHITELIST = config(
    "CORS_ORIGIN_WHITELIST",
    cast=lambda v: [s.strip() for s in v.split(",")],
    default="http://*,https://*",
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TIME_ZONE = "UTC"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DJANGO_POSTGRES_DB"),
        "USER": config("DJANGO_POSTGRES_USER"),
        "PASSWORD": config("DJANGO_POSTGRES_PASSWORD"),
        "HOST": config("DJANGO_POSTGRES_HOST"),
        "PORT": config("DJANGO_POSTGRES_PORT"),
    }
}


SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


EMAIL_HOST          = config("EMAIL_HOST", default='smtp.gmail.com')  # SMTP server host
EMAIL_PORT          = config("EMAIL_PORT", default=465)  # SMTP server port (587 for TLS, 465 for SSL)
EMAIL_USE_TLS       = config("EMAIL_USE_TLS", default=True)  # True for TLS, False for SSL
#EMAIL_USE_SSL       = config("EMAIL_USE_SSL", default=True)  # Set to True if using SSL

EMAIL_HOST_USER     = config("EMAIL_HOST_USER", default='your_email@example.com')  # SMTP server username
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default='your_password')  # SMTP server password
DEFAULT_FROM_EMAIL  = config("DEFAULT_FROM_EMAIL", default='your_email@example.com')  # Default sender email address