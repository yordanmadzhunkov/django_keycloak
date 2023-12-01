from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import Campaign, InvestementInCampaign
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CreateInvestmentForm, EditInvestmentForm, CampaingEditForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from decimal import Decimal#, DecimalException
#from datetime import date
#from django import template


def view_campaign_as_manager(request, pk, context, campaign, factory):
    if campaign.accept_investments():
        form = CampaingEditForm()
        if request.method == 'POST':
            if 'cancel' in request.POST:
                form = CampaingEditForm(request.POST)
                campaign.status = Campaign.Status.CANCELED;
                campaign.save()
                messages.success(request, "Кампанияте беше прекратена")

            if 'complete' in request.POST:
                form = CampaingEditForm(request.POST)
                if campaign.progress()['percent'] >= Decimal(100):
                    campaign.status = Campaign.Status.COMPLETED;
                    campaign.save()
                    messages.success(request, "Приключване")
                else:
                    messages.error(request, "Все още няма достатъчно предварителен интерес от инвеститорите")

        context['invest_form'] = form
    context['show_invest_form'] = campaign.accept_investments()
    context['factory'] = factory
    context['campaign'] = campaign
    context['investors'] = campaign.get_investors(show_users=True)
    return render(request, "campaign.html", context)


def view_campaign_as_investor(request, pk, context, campaign, factory):
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
                    amount = form.cleaned_data['amount']
                    investment = InvestementInCampaign(
                                amount= amount,
                                campaign=campaign,
                                investor_profile=profile,
                                status=InvestementInCampaign.Status.INTERESTED
                    )
                    investment.save()
                    form = EditInvestmentForm(instance=investment)

                    messages.success(request, "Заявихте инвестиционнен интерес в размер на %d в %s" % (amount, factory.name))
                else:
                    messages.error(request, "Невалидни данни, моля опитайте отново")        
    else:
        form = EditInvestmentForm(instance=my_investments[0])
        if request.method == 'POST':
            if 'cancel' in request.POST:
                my_investments[0].status = InvestementInCampaign.Status.CANCELED
                my_investments[0].save()
                messages.success(request, "Инвестиционния ви интерес беше отменен")
                form = CreateInvestmentForm()

                
            if 'save' in request.POST:
                form = EditInvestmentForm(request.POST)
                if form.is_valid():
                    my_investments[0].amount = form.cleaned_data['amount']
                    my_investments[0].save()
                    messages.success(request, "Инвестиционния ви интерес беше променен на %d" % my_investments[0].amount)
                else:
                    messages.error(request, "Възникна грешка при промяна на сумата")

    context['show_invest_form'] = True
    context['factory'] = factory
    context['campaign'] = campaign
    context['investors'] = campaign.get_investors(show_users=False)
    context['invest_form'] = form
    return render(request, "campaign.html", context)
    
    
def vire_campaign_as_anon(request, pk, context, campaign, factory):
    return render(request, "campaign.html", context)

def view_campaign(request, pk):
    context = common_context(request)
    campaign = Campaign.objects.get(pk=pk)
    factory = campaign.factory
    form = None
    if request.user:
        if request.user.is_authenticated:
            is_manager = factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager:
                return view_campaign_as_manager(request, pk, context, campaign, factory)
            else:
                return view_campaign_as_investor(request, pk, context, campaign, factory)
    return vire_campaign_as_anon(request, pk, context, campaign, factory)

