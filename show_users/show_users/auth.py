from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from urllib.parse import urlencode
from pprint import pprint

from show_users.settings import base as settings


def update_user_from_claims(user, claims):
    user.first_name = claims.get("given_name", '')
    user.last_name = claims.get("family_name", '')
    user.is_staff = "admins" in claims.get("groups", [])
    user.is_superuser = "admins" in claims.get("groups", [])
    user.save()
    return user


class MyOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        pprint(claims)
        return super().verify_claims(claims)

    def create_user(self, claims):
        user = super().create_user(claims)
        user = update_user_from_claims(user, claims)
        return user

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
