from django.shortcuts import render
from . import common_context
from vei_platform.models.team import TeamMember
from django.utils.translation import gettext as _

def view_team(request):
    context = common_context(request)
    context['members'] = TeamMember.objects.all().order_by('order')
    return render(request, "team.html", context)