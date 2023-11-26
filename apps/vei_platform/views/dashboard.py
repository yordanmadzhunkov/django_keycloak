from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.finance_modeling import InvestementInListing, FactoryListing
from vei_platform.models.profile import get_user_profile

def view_dashboard(request):
    context = common_context(request)
    if request.user:
        context['my_legal_entity'] = find_legal_entity(user=request.user)
        if request.user.is_authenticated:
            profile = get_user_profile(request.user)
            my_investments = InvestementInListing.objects.filter(investor_profile=profile)
            context['my_investments'] = my_investments
    return render(request, "dashboard.html", context)