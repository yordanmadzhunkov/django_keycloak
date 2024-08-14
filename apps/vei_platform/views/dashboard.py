from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.campaign import InvestementInCampaign, Campaign
from vei_platform.models.profile import get_user_profile
from vei_platform.models.factory import ElectricityFactory
from django.utils.translation import gettext as _

from django.views import View


class Dashboard(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        if request.user and request.user.is_authenticated:
            self.add_my_legal_entity(request, context)
            self.add_my_investments(request, context)
            self.add_my_campaigns(request, context)
            return render(request, "dashboard.html", context)
        return redirect("home")

    def add_my_legal_entity(self, request, context):
        if request.user and request.user.is_authenticated:
            context["my_legal_entity"] = find_legal_entity(user=request.user)

    def add_my_investments(self, request, context):
        if request.user and request.user.is_authenticated:
            profile = get_user_profile(request.user)
            my_investments = InvestementInCampaign.objects.filter(
                investor_profile=profile
            )
            context["my_investments"] = my_investments

    def add_my_campaigns(self, request, context):
        if request.user and request.user.is_authenticated:
            factories_list = ElectricityFactory.objects.filter(
                manager=request.user
            ).order_by("pk")
            campaigns = []
            for factory in factories_list:
                factory_campaigns = Campaign.objects.filter(factory=factory)
                for c in factory_campaigns:
                    campaigns.append(c)
            context["campaigns"] = campaigns
