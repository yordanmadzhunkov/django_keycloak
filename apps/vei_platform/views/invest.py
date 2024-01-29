from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import Campaign as CampaignModel, InvestementInCampaign
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CreateInvestmentForm, EditInvestmentForm, CampaingEditForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from decimal import Decimal
from django.utils.translation import gettext as _
from django.views import View


def view_campaign_as_manager(request, pk, context, campaign, factory):
    if campaign.accept_investments():
        allow_finish = campaign.progress()['percent'] >= Decimal(100)
        form = CampaingEditForm(allow_finish)
        if request.method == 'POST':
            if 'cancel' in request.POST:
                form = CampaingEditForm(request.POST)
                campaign.status = Campaign.Status.CANCELED;
                campaign.save()
                messages.success(request, _("Campaign is canceled"))

            if 'complete' in request.POST:
                form = CampaingEditForm(request.POST)
                if allow_finish:
                    campaign.status = Campaign.Status.COMPLETED;
                    campaign.save()
                    messages.success(request, _("Campaign is completed"))
                else:
                    messages.error(request, _("Not enough acumulated interest to be able to finish the campaing"))

        context['invest_form'] = form
    context['show_invest_form'] = campaign.accept_investments()
    context['factory'] = factory
    context['campaign'] = campaign
    context['investors'] = campaign.get_investors(show_users=True)
    return render(request, "campaign.html", context)


def get_campaign_as_investor(request, pk, context, campaign, factory):
    profile = get_user_profile(request.user)        
    my_investments = InvestementInCampaign.objects.filter(campaign=campaign, 
                                                          investor_profile=profile, 
                                                          status=InvestementInCampaign.Status.INTERESTED)
    if len(my_investments) == 0:
        form = CreateInvestmentForm()
    else:
        form = EditInvestmentForm(instance=my_investments[0])

    context['show_invest_form'] = campaign.accept_investments()
    context['factory'] = factory
    context['campaign'] = campaign
    context['investors'] = campaign.get_investors(show_users=False, investor_profile=profile)
    context['invest_form'] = form
    return render(request, "campaign.html", context)


def post_campaign_as_investor(request, pk, context, campaign, factory):
    profile = get_user_profile(request.user)        
    my_investments = InvestementInCampaign.objects.filter(campaign=campaign, 
                                                          investor_profile=profile, 
                                                          status=InvestementInCampaign.Status.INTERESTED)
    if len(my_investments) == 0:
        form = CreateInvestmentForm()
        if request.method == 'POST':
            if 'invest' in request.POST:
                form = CreateInvestmentForm(request.POST)
                if form.is_valid():
                    print(form.cleaned_data)
                    amount = form.cleaned_data['amount']
                    investment = InvestementInCampaign(
                                amount= amount,
                                campaign=campaign,
                                investor_profile=profile,
                                status=InvestementInCampaign.Status.INTERESTED
                    )
                    investment.save()
                    form = EditInvestmentForm(instance=investment)

                    messages.success(request, _("You declared interest in amount %s to %s") % (amount, factory.name))
                else:
                    messages.error(request, _("Invalid data, please try again"))        
    else:
        form = EditInvestmentForm(instance=my_investments[0])
        if request.method == 'POST':
            if 'cancel' in request.POST:
                my_investments[0].status = InvestementInCampaign.Status.CANCELED
                my_investments[0].save()
                messages.success(request, _("Your interest have been canceled"))
                form = CreateInvestmentForm()

                
            if 'save' in request.POST:
                form = EditInvestmentForm(request.POST)
                if form.is_valid():
                    my_investments[0].amount = form.cleaned_data['amount']
                    my_investments[0].save()
                    messages.success(request, _("You declared interest in amount changed to %s") % my_investments[0].amount)
                else:
                    messages.error(request, _("Error occured when changing the amount"))

    context['show_invest_form'] = campaign.accept_investments()
    context['factory'] = factory
    context['campaign'] = campaign
    context['investors'] = campaign.get_investors(show_users=False, investor_profile=profile)
    context['invest_form'] = form
    return render(request, "campaign.html", context)
    
    
    
def vire_campaign_as_anon(request, pk, context, campaign, factory):
    return render(request, "campaign.html", context)

class Campaign(View):
    def get(self, request, pk, *args, **kwargs):
        context = common_context(request)
        campaign = CampaignModel.objects.get(pk=pk)
        factory = campaign.factory
        form = None
        if request.user and request.user.is_authenticated:
            is_manager = factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager:
                return view_campaign_as_manager(request, pk, context, campaign, factory)
            else:
                return get_campaign_as_investor(request, pk, context, campaign, factory)
        return vire_campaign_as_anon(request, pk, context, campaign, factory)
    
    def post(self, request, pk, *args, **kwargs):
        context = common_context(request)
        campaign = CampaignModel.objects.get(pk=pk)
        factory = campaign.factory
        form = None
        if request.user and request.user.is_authenticated:
            is_manager = factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager:
                return view_campaign_as_manager(request, pk, context, campaign, factory)
            else:
                return post_campaign_as_investor(request, pk, context, campaign, factory)
        return vire_campaign_as_anon(request, pk, context, campaign, factory)    