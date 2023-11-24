from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import FactoryListing, InvestementInListing
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import DecalareInterestListingForm

#from django.contrib.auth.decorators import login_required
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
                form = DecalareInterestListingForm(request.POST)
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
                form = DecalareInterestListingForm()
    context['show_invest_form'] = True
    context['factory'] = factory
    context['listing'] = listing
    context['invest_form'] = form
    return render(request, "invest_listing.html", context)