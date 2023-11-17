from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render


def view_home(request):
    context = common_context(request)
    return render(request, "home.html", context)