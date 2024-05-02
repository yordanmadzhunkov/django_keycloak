from pathlib import Path
from decouple import config
from django.contrib.messages import constants as messages

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'

ALLOWED_HOSTS = ['*']

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'django_extensions',
    'crispy_forms',
    "crispy_bootstrap4",
    
    # Health checks
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
    'health_check.contrib.psutil',

    'django_q',
    'djmoney',
    'djmoney.contrib.exchange',

    'rest_framework',
    'rest_framework.authtoken',  # TOKEN ACCESS

    'vei_platform'
]

HEALTH_CHECK = {
    'DISK_USAGE_MAX': 100.0,  # percent
    'MEMORY_MIN': 100,    # in MB
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', #right place
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'vei_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]


# Add 'mozilla_django_oidc' authentication backend
AUTHENTICATION_BACKENDS = (
    'show_users.auth.MyOIDCAuthenticationBackend',
    "django.contrib.auth.backends.ModelBackend",  # default
    # 'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # ...
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  # <-- And here
    ],
}


OIDC_RP_CLIENT_ID = config('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = config('OIDC_RP_CLIENT_SECRET')
OIDC_HOSTNAME = config('OIDC_HOSTNAME')
OIDC_REALM_NAME = config('OIDC_REALM_NAME')

OIDC_AUTH_URI = OIDC_HOSTNAME + '/realms/' + \
    OIDC_REALM_NAME + '/protocol/openid-connect/'

OIDC_OP_AUTHORIZATION_ENDPOINT = OIDC_AUTH_URI + 'auth'
OIDC_OP_TOKEN_ENDPOINT = OIDC_AUTH_URI + 'token'
OIDC_OP_USER_ENDPOINT = OIDC_AUTH_URI + 'userinfo'
OIDC_OP_JWKS_ENDPOINT = OIDC_AUTH_URI + 'certs'
OIDC_OP_LOGOUT_ENDPOINT = OIDC_AUTH_URI + 'logout'


# Specify the method responsible for building the OIDC logout URL
OIDC_OP_LOGOUT_URL_METHOD = 'vei_platform.auth.provider_logout'

# Store the OIDC id_token for use with logout URL method
OIDC_STORE_ID_TOKEN = True
OIDC_CALLBACK_PUBLIC_URI = config('PUBLIC_URL')


OIDC_VERIFY_SSL = True
OIDC_RP_SIGN_ALGO = 'RS256'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = '/'

SITE_ID = 1


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = config("LANGUAGE_CODE", default="en")
TIME_ZONE = config("TIME_ZONE", default="UTC")

ugettext = lambda s: s        
LANGUAGES = (
    ( 'en', ugettext( 'English' )),
    ( 'bg', ugettext( 'Български' )),
)        


STATICFILES_DIRS = (
    (BASE_DIR / 'static_to_collect'),
)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static/'

# Media filess (Documents, Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media/'


LOCALE_PATHS = ((BASE_DIR / 'locale' ), ) # translation files will be created into 'locale' folder from root project folder
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# example ORM broker connection
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 1,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}


DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240  # higher than the count of fields

VEI_PLATFORM_IMAGE = config("VEI_PLATFORM_IMAGE", default="unspecified image")


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

CRISPY_TEMPLATE_PACK = "bootstrap4"

CURRENCIES = ('EUR', 'BGN', 'USD')
CURRENCY_CHOICES = [('EUR', 'EUR €'), ('BGN', 'BGN лв'), ('USD', 'USD $')]

#BASE_CURRENCY = 'EUR'
#OPEN_EXCHANGE_RATES_URL = 'https://openexchangerates.org/api/latest.json?base=EUR'
OPEN_EXCHANGE_RATES_APP_ID = config('OPEN_EXCHANGE_RATES_APP_ID', default='d4d02b6623504e4ca51c588443e960d5')
EXCHANGE_BACKEND = 'djmoney.contrib.exchange.backends.OpenExchangeRatesBackend'