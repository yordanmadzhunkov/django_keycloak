from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.models.legal import find_legal_entity

def view_dashboard(request):
    context = common_context(request)
    if request.user:
        context['my_legal_entity'] = find_legal_entity(user=request.user)
    return render(request, "dashboard.html", context)