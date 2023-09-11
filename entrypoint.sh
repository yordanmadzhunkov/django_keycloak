#!/bin/sh

cd $APP_PATH

gunicorn --bind 0.0.0.0:8000 show_users.wsgi:application
