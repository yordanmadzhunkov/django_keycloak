from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.profile import get_user_profile
from vei_platform.models.factory import ElectricityFactory
from django.utils.translation import gettext as _

from django.views import View


class Dashboard(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        if request.user and request.user.is_authenticated:
            self.add_my_legal_entity(request, context)
            return render(request, "dashboard.html", context)
        return redirect("home")

    def add_my_legal_entity(self, request, context):
        if request.user and request.user.is_authenticated:
            context["my_legal_entity"] = find_legal_entity(user=request.user)

