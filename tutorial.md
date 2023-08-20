# Using Keycloak authentication with Django

This tutorial is based on several other blog post which can be found here:

[Using Keycloak authentication with Django](https://blog.cyberspringboard.com/posts/20221021-keycloak/)

[Registering new users using Keycloak with Django](https://blog.cyberspringboard.com/posts/20221109-keycloakregisterlink/)

[Logging users out of their Keycloak session](https://blog.cyberspringboard.com/posts/20221111-keycloaklogouturl/)


## Introduction

Keycloak is an open source Identity and Access Management (IAM) system. 
Keycloak allows you to add authentication to applications and secure services easily as it handles storing and authenticating users. 
Keycloak provides user federation, strong authentication, user management, fine-grained authorization, and more. 
In particular, it supports multi-factor authentication (MFA), and WebAuthn using mobile apps and U2F Tokens such as Yubikeys. 
It supports the OpenID Connect standard, which builds on the OAuth 2.0 protocol.

## Setup keyclock instance
This tutorial assumes you have running keycloack instance, I used the following version in `docker-compose.yaml`:

```
...
  keycloak:
    container_name: keycloak
    command: ["start", "--spi-theme-static-max-age=-1", "--spi-theme-cache-themes=false", "--spi-theme-cache-templates=false"]
    image: "keycloak/keycloak:21.0"
...
```


## 


To authenticate using OpenID Connect, we use the mozilla-django-oidc library. Integration was mostly straightforward following their Quick Start guide. Once the changes in the Django application was complete, I found that creating a new OpenID Connect client and setting the following attributes was sufficient:
```
    Client ID (e.g. my-client-id)
    Root URL (e.g. http://localhost:8000)
    Home URL (e.g. http://localhost:8000)
    Valid redirect URIs (e.g. http://localhost:8000/*)
    Valid post logout redirect URIs (e.g. + to use valid redirect URIs)
    Client authentication (On)
```

These URL and URI settings need to match your environment, and a different client is required for each environment.

You then update the Django settings.py with the Client ID and Client secret obtained from the Credentials tab for the Client in Keycloak. If the Credentials tab is missing because you accepted the defaults when creating the client, you need to turn on Client authentication.

`app/settings.py`

```
OIDC_RP_CLIENT_ID="my-client-id",
OIDC_RP_CLIENT_SECRET="client-secret",
```

These settings are normally provided to the application through environment variables (see 12-factor apps) to allow client credentials to be easily changed for each environment.
Exploring the claims passed to the app

In integrating Keycloak and Django, I wanted to make use of groups for permissions within Cyber Springboard. Groups, along with other user information, is passed as claims with the authentication token.

To explore the claims provided you can use the following custom OIDCAuthenticationBackend. This will print the claims to the console, using Python’s pprint module. You can of course set entry to the `verify_claims(...)` function as a breakpoint, and explore in your debugger.

`app/auth.py`

```
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from pprint import pprint


class MyAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        pprint(claims)
        return super().verify_claims(claims)
```

`app/settings.py`

```
AUTHENTICATION_BACKENDS = (
    'app.auth.MyAuthenticationBackend',
)
```

You should see a dictionary of claims similar to that shown below printed in the console.

```
{'email': 'coffee_lover@gmail.com',
 'email_verified': False,
 'family_name': 'Lovel',
 'given_name': 'Coffee',
 'groups': ['offline_access',
            'default-roles-demo',
            'uma_authorization',
            'admins',
            'users'],
 'name': 'Coffee Lover',
 'preferred_username': 'coffee_lover',
 'sub': '221d878d-e647-4033-9082-6418d106856c'}
```

Configuring groups and adding them to the token’s claims

To ensure that groups configured in Keycloak are present in the claims presented in the token, you need to do the following:

```
    Add a Client scope for groups:

        Client scopes -> Create client scope
            Name: groups
            Description: Open ID groups for a user
            Type: Default
            Protocol: OpenID Connect
            Display on consent screen: Off
            Include in token scope: On

        Click Save

        Mappers -> click Add predefined mapper

        Search for groups

        Tick groups and click Add

    Add the Client scope to the Client:
        Clients -> select client (e.g. my-client-id)
        Client scopes -> Add client scope
        Tick groups
        Click Add and select Default

    Add the Roles you wish to use:
        Realm roles -> click Create role
        Name: my-role

    Add the Groups you wish to use:
        Groups -> click Create group
        Name: my-group
        Role mapping -> Assign role
        Tick my-role
        Click Assign

    Assign the Group to a User:
        Users -> click on the user
        Groups -> click Join Group
        Tick the group
        Click Join
```


When logging into the application now, the user’s claims should include the ‘groups’ element, as follows:

```
{'email': 'user@example.com'
 'email_verified': True,
 'family_name': 'User',
 'given_name': 'My',
 'groups': ['default-roles-my-client-id',
            'my-group',
            'offline_access',
            'uma_authorization'],
 'name': 'My User',
 'preferred_username': 'user@example.com',
 'sub': '12345678-1234-1234-1234-1234567890ab',
}
```

Using group membership to control access to Django’s admin interface

Django’s built-in admin interface doesn’t know how to authenticate against Keycloak. Attempts to log-in with the current setup will fail.

We could allow a normal Django superuser or staff account created outside of Keycloak to authenticate by adding a second backend to AUTHENTICATION_BACKENDS as follows:

`app/settings.py`

```
AUTHENTICATION_BACKENDS = (
    'app.auth.MyAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)
```

However, it is possible to make use of groups to allow our Keycloak authenticated users to use Django’s built-in admin functionality. Let’s say wish to use the groups staff and superuser to set the User’s is_staff and is_superuser attributes. We can achieve this by updating our custom OIDCAuthenticationBackend as follows:

`app/auth.py`


```
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

def update_user_from_claims(user, claims):
    user.first_name = claims.get("given_name", '')
    user.last_name = claims.get("family_name", '')
    user.is_staff = "staff" in claims.get("groups", [])
    user.is_superuser = "superuser" in claims.get("groups", [])
    user.save()
    return user


class MyAuthenticationBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims)
        user = update_user_from_claims(user, claims)
        return user

    def update_user(self, user, claims):
        user = super().update_user(user, claims)
        user = update_user_from_claims(user, claims)
        return user
```

To ensure the application’s permissions match the user’s current group membership, we need to set these attributes both when the user is created by `create_user(...)` and also whenever the user logs and `update_user(...)` is called.


## Logging out 

Earlier versions of Keycloak supported a redirectURI parameter, but since Keycloak 18 this is deprecated. The redirectURI parameter has been removed in Keycloak 19 and the Keycloak logout page will display an Invalid parameter: redirect_uri error. Instead we need to set two parameters:

* post_logout_redirect_uri to where we would like to redirect the user; and,
* id_token_hint to the OIDC ID token issued when the user authenticated.

We need to update settings.py to include the OIDC logout endpoint. We also need to tell mozilla-django-oidc to store the OIDC ID_TOKEN and the name of the function that will build our logout URL.

`app/settings.py`

```
# Your OIDC server
OIDC_HOST = "https://auth.example.com"

# Your OIDC realm
OIDC_REALM = "realm-name"

# Store the OIDC id_token for use with logout URL method
OIDC_STORE_ID_TOKEN = True

# URL for logout
OIDC_OP_LOGOUT_ENDPOINT = f"{OIDC_HOST}/realms/{OIDC_REALM}/protocol/openid-connect/logout"

# Specify the method responsible for building the OIDC logout URL
OIDC_OP_LOGOUT_URL_METHOD = 'app.auth.provider_logout'
```


We then need to implement the OIDC_OP_LOGOUT_URL_METHOD as shown below. You may wish to use urllib.parse.urlparse and urllib.parse.urlunparse to build the registration_url.


`app/auth.py`

```
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

```