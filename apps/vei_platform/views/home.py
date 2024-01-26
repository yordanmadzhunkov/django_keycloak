from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render
from django.utils.translation import gettext as _

from django.views import View

class Home(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        return render(request, "home.html", context)