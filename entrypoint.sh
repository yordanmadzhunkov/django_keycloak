#!/bin/sh

python manage.py collectstatic --noinput
python manage.py compilemessages 
python manage.py migrate --noinput
python manage.py update_rates

gunicorn --bind :8000 --workers ${NUM_WORKERS} vei_platform.wsgi:application
