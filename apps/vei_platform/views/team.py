from django.shortcuts import render
from . import common_context
from vei_platform.models.team import TeamMember
from django.utils.translation import gettext as _
from django.views import View


class Team(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        context["members"] = TeamMember.objects.all().order_by("order")
        return render(request, "team.html", context)
