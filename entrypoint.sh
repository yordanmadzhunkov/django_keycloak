#!/bin/sh

./manage.py collectstatic --noinput
# i commit my migration files to git so i dont need to run it on server
./manage.py migrate

gunicorn --bind :8000 --workers ${NUM_WORKERS} vei_platform.wsgi:application
