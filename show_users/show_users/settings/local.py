from .base import *
from decouple import config
from pathlib import Path

DEBUG = config("DEBUG", default=True, cast=bool)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, 'data/db.sqlite3')
    }
}

SECRET_KEY = '-05sgp9!deq=q1nltm@^^2cc+v29i(tyybv3v2t77qi66czazj'

