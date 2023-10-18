from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render


@login_required(login_url='/oidc/authenticate/')
def view_home(request):
    context = common_context()
    if request.user.is_authenticated:
        context['profile'] = get_user_profile(request.user)
    return render(request, "home.html", context)