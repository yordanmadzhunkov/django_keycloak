#!/bin/bash

./manage.py collectstatic --noinput
# i commit my migration files to git so i dont need to run it on server
# ./manage.py makemigrations show_users
./manage.py migrate

gunicorn --bind :8000 --workers 3 show_users.wsgi:application
