from .base import *
from decouple import config
from pathlib import Path

DEBUG = config("DEBUG", default=False, cast=bool)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY              = config('DJANGO_SECRET_KEY')

ALLOWED_HOSTS           = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')], default='*')
CSRF_TRUSTED_ORIGINS    = config('CSRF_TRUSTED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')], default='*')
CORS_ORIGIN_WHITELIST   = config('CORS_ORIGIN_WHITELIST', cast=lambda v: [s.strip() for s in v.split(',')], default='*')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TIME_ZONE = 'UTC'

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DJANGO_POSTGRES_DB'),
        'USER': config('DJANGO_POSTGRES_USER'),
        'PASSWORD': config('DJANGO_POSTGRES_PASSWORD'),
        'HOST': config('DJANGO_POSTGRES_HOST'),
        'PORT': config('DJANGO_POSTGRES_PORT'),
    }
}


SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
