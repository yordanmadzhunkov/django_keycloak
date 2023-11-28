from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import FactoryListing, InvestementInListing
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CreateInvestmentForm, EditInvestmentForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

#from decimal import Decimal, DecimalException
#from datetime import date
#from django import template


def view_investment_opportunity(request, pk):
    context = common_context(request)
    listing = FactoryListing.objects.get(pk=pk)
    factory = listing.factory
    form = None
    if request.user:
        if request.user.is_authenticated:
            if request.method == 'POST':
                form = CreateInvestmentForm(request.POST)
                if form.is_valid():
                    amount = form.cleaned_data['amount']
                    profile = get_user_profile(request.user)        
                    investment = InvestementInListing(
                        amount= amount,
                        listing=listing,
                        investor_profile=profile,
                        status=InvestementInListing.InvestementStatus.INTERESTED
                    )
                    investment.save()
                    messages.success(request, "Заявихте инвестиционнен интерес в размер на %d в %s" % (amount, factory.name))
                else:
                    messages.error(request, "Невалидни данни, моля опитайте отново")
            else:
                form = CreateInvestmentForm()
    context['show_invest_form'] = True
    context['factory'] = factory
    context['listing'] = listing
    context['investors'] = listing.get_investors(show_users=True)
    context['invest_form'] = form
    return render(request, "invest_listing.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_investment(request, pk):
    context = common_context(request)
    investment = InvestementInListing.objects.get(pk=pk)
    context['factory'] = investment.listing.factory
    context['listing'] = investment.listing
    context['investment'] = investment
    context['show_invest_form'] = True
    if request.method == "POST":
        if 'save' in request.POST.keys():
            if investment.status == InvestementInListing.InvestementStatus.INTERESTED:
                form = EditInvestmentForm(request.POST)
                if form.is_valid():
                    investment.amount = form.cleaned_data['amount']
                    investment.save()
                    messages.success(request, 'Сумата е променена на %d' % investment.amount)    
                else:
                    messages.error(request, 'Грешна сума')    

        if 'cancel' in request.POST.keys():
            if investment.status == InvestementInListing.InvestementStatus.INTERESTED:
                investment.status = InvestementInListing.InvestementStatus.CANCELED
                investment.save()
                messages.success(request, 'Вашата заявка за инвестиране в централата е отменена')    
            else:
                messages.error(request, 'Не може да се откажете от инвестицията в този етап')
    
    if investment.status == InvestementInListing.InvestementStatus.CANCELED:
        return redirect('invest_opportunity', pk=investment.listing.pk)
    context['invest_form'] = EditInvestmentForm(instance=investment)
    return render(request, "investment.html", context)