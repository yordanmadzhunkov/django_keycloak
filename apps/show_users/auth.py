from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from urllib.parse import urlencode
from pprint import pprint

from show_users.settings import base as settings
#import time

def update_user_from_claims(user, claims):
    user.first_name = claims.get("given_name", '')
    user.last_name = claims.get("family_name", '')
    user.is_staff = "admins" in claims.get("groups", [])
    user.is_superuser = "admins" in claims.get("groups", [])
    user.email = claims.get('email')
    user.username = claims.get('preferred_username')
    user.save()
    return user


class MyOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    # def verify_claims(self, claims):
    #    pprint(claims)
    #    return super().verify_claims(claims)

    # https://github.com/mozilla/mozilla-django-oidc/issues/435
    # TO bypass the session not stored bug
    #def get(self, request):
    #    time.sleep(1) 
    #    super().get(request)

    def create_user(self, claims):
        user = super().create_user(claims)
        user = update_user_from_claims(user, claims)
        return user

    def filter_users_by_claims(self, claims):
        """ Return all users matching the specified email.
            If nothing found matching the email, then try the username
        """
        email = claims.get('email')

        if not email:
            return self.UserModel.objects.none()
        users = self.UserModel.objects.filter(email__iexact=email)
        return users

    def update_user(self, user, claims):
        user = super().update_user(user, claims)
        user = update_user_from_claims(user, claims)
        return user


def provider_logout(request):
    """ Create the user's OIDC logout URL."""
    # User must confirm logout request with the default logout URL
    # and is not redirected.
    logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT

    # If we have the oidc_id_token, we can automatically redirect
    # the user back to the application.
    oidc_id_token = request.session.get('oidc_id_token', None)
    if oidc_id_token:
        logout_url = (
            settings.OIDC_OP_LOGOUT_ENDPOINT
            + "?"
            + urlencode(
                {
                    "id_token_hint": oidc_id_token,
                    "post_logout_redirect_uri": request.build_absolute_uri(
                        location=settings.LOGOUT_REDIRECT_URL
                    )
                }
            )
        )

    return logout_url
