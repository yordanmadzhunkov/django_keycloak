#!/bin/sh

python manage.py collectstatic --noinput
python manage.py compilemessages 
python manage.py migrate --noinput

gunicorn --bind :8000 --workers ${NUM_WORKERS} vei_platform.wsgi:application
