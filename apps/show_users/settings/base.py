"""
Django settings for show_users project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mozilla_django_oidc",  # Load after auth
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
]

ROOT_URLCONF = "show_users.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DEBUG = config("DEBUG", default=True, cast=bool)

LOGGING = {
    "version": 1,  # the dictConfig format version
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "mozilla_django_oidc": {"handlers": ["console"], "level": "WARNING"},
    },
}

WSGI_APPLICATION = "show_users.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Add 'mozilla_django_oidc' authentication backend
AUTHENTICATION_BACKENDS = (
    "show_users.auth.MyOIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",  # default
    # 'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # ...
)


OIDC_RP_CLIENT_ID = config("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = config("OIDC_RP_CLIENT_SECRET")
OIDC_HOSTNAME = config("OIDC_HOSTNAME")
OIDC_REALM_NAME = config("OIDC_REALM_NAME")

OIDC_AUTH_URI = (
    OIDC_HOSTNAME + "/realms/" + OIDC_REALM_NAME + "/protocol/openid-connect/"
)

OIDC_OP_AUTHORIZATION_ENDPOINT = OIDC_AUTH_URI + "auth"
OIDC_OP_TOKEN_ENDPOINT = OIDC_AUTH_URI + "token"
OIDC_OP_USER_ENDPOINT = OIDC_AUTH_URI + "userinfo"
OIDC_OP_JWKS_ENDPOINT = OIDC_AUTH_URI + "certs"
OIDC_OP_LOGOUT_ENDPOINT = OIDC_AUTH_URI + "logout"


# Specify the method responsible for building the OIDC logout URL
OIDC_OP_LOGOUT_URL_METHOD = "show_users.auth.provider_logout"

# Store the OIDC id_token for use with logout URL method
OIDC_STORE_ID_TOKEN = True
OIDC_CALLBACK_PUBLIC_URI = config("PUBLIC_URL")


OIDC_VERIFY_SSL = True
OIDC_RP_SIGN_ALGO = "RS256"

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "/"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATICFILES_DIRS = ((BASE_DIR / "static_to_collect"),)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static/"

# Media filess (Documents, Images)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media/"


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
