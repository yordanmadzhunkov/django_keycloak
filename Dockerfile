# Fetching official base image for python
FROM python:3.10.13-alpine3.18 as web

# Setting up the work directory
WORKDIR /home/app/

# Preventing python from writing
# pyc to docker container
ENV PYTHONDONTWRITEBYTECODE 1

# Flushing out python buffer
ENV PYTHONUNBUFFERED 1
ENV APP_PATH=/opt/app

# Updating the os
RUN apk update 


RUN apk add --no-cache python3 gcc libc-dev linux-headers postgresql-dev \
    && apk add libffi-dev \
    && python3 -m ensurepip \
    && pip3 install --upgrade pip gunicorn    

COPY ./apps/requirements_django_oidc.txt $APP_PATH/requirements_django_oidc.txt

# Install  the application's dependencies.
RUN pip3 install -r $APP_PATH/requirements_django_oidc.txt

COPY ./apps/vei_platform/requirements/base.txt       $APP_PATH/requirements/base.txt
COPY ./apps/vei_platform/requirements/production.txt $APP_PATH/requirements/production.txt

RUN pip3 install -r $APP_PATH/requirements/production.txt

# Copy the application over into the container.
COPY ./apps/ $APP_PATH


# entrypoint, must be executable file chmod +x entrypoint.sh
COPY entrypoint.sh          /entrypoint/
COPY entrypoint_qcluster.sh /entrypoint/
COPY entrypoint_tests.sh    /entrypoint/


WORKDIR $APP_PATH/
EXPOSE 8000

# what happens when I start the container
ENTRYPOINT ["sh", "/entrypoint/entrypoint.sh"]

