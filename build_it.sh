python -c ""

echo "# automaticaly generated on $(date)" > .env
echo "" >> .env

# for older python
# SECRET=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

#for Python 3.6+
SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe())')
echo "DJANGO_SECRET_KEY=\"${SECRET}\"" >> .env

echo 'DJANGO_SETTINGS_MODULE="vei_platform.settings.production"' >> .env

DJANGO_GIT_TAG=$(git describe --tags --dirty --long)
echo "DJANGO_GIT_TAG=\"${DJANGO_GIT_TAG}\"" >> .env
cat oidc.env >> .env

echo "Starting build .. "
docker compose build vei_platform
