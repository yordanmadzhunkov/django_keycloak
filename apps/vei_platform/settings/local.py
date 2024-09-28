from .base import *

DEBUG = config("DEBUG", default=True, cast=bool)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

SECRET_KEY = config(
    "DJANGO_SECRET_KEY", "-05sgp9!deq=q1nltm@^^2cc+v29i(tyybv3v2t77qi66czazj"
)


# Add 'mozilla_django_oidc' authentication backend
AUTHENTICATION_BACKENDS = (
    "vei_platform.auth.MyOIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",  # default
    # 'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # ...
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    cast=lambda v: [s.strip() for s in v.split(",")],
    default="http://*,https://*",
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# SESSION_ENGINE = "django.contrib.sessions.backends.cache"

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# SESSION_COOKIE_HTTPONLY = True
# SESSION_COOKIE_AGE = 60*60*24
# SESSION_COOKIE_SECURE = False


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'  # SMTP server host
# EMAIL_PORT = 587  # SMTP server port (587 for TLS, 465 for SSL)
# EMAIL_USE_TLS = True  # True for TLS, False for SSL
# EMAIL_HOST_USER = 'your_email@example.com'  # SMTP server username
# EMAIL_HOST_PASSWORD = 'your_password'  # SMTP server password
# EMAIL_USE_SSL = False  # Set to True if using SSL
# DEFAULT_FROM_EMAIL = 'your_email@example.com'  # Default sender email address
