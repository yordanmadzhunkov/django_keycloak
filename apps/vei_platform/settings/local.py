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
