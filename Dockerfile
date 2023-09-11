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


RUN apk add --no-cache python3 \
    && python3 -m ensurepip \
    && pip3 install --upgrade pip gunicorn    

COPY ./requirements.txt $APP_PATH/requirements.txt

# Install  the application's dependencies.
RUN pip3 install -r $APP_PATH/requirements.txt

# Copy the application over into the container.
COPY ./show_users/ $APP_PATH

WORKDIR $APP_PATH/

EXPOSE 8000

ENTRYPOINT ["gunicorn", "--bind", ":8000", "--workers", "3",  "show_users.wsgi:application"]
