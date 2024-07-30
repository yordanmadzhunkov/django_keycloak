from .base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

SECRET_KEY = "-05sgp9!deq=q1nltm@^^2cc+v29i(tyybv3v2t77qi66czazj"


# Add 'mozilla_django_oidc' authentication backend
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
    # 'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # ...
)
