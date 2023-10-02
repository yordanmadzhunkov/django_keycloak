import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'vei_platform.settings.local')

application = get_wsgi_application()
