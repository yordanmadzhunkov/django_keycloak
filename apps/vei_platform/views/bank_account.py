from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render


@login_required(login_url='/oidc/authenticate/')
def view_bank_accounts(request):
    context = common_context()
    avatar_url = None
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        context['profile'] = profile
        avatar_url = profile.get_avatar_url

    context['accounts'] = [
        {
            'iban':'LU130107645115151684',
            'currency': 'EUR',
            'status': 'Active',
            'owner': 'John Doe',
            'avatar_url': avatar_url,
            'actions': ['Withdraw', 'Deposit',]
         },
        {
            'iban':'IR547132577934248129248933',
            'currency': 'Iranian rial',
            'status': 'Inactive',
            'owner': 'Al shamany',
            'avatar_url': avatar_url,
            'actions': [],
         },
        {
            'iban':'BG58UNCR70005276158923',

            'currency': 'BGN',
            'status': 'Unverified',
            'owner': 'Ivan Ivanov',
            'avatar_url': avatar_url,
            'actions': ['Verify', ],
         },

    ]
    return render(request, "bank_accounts.html", context)