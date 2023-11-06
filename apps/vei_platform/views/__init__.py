#from django.shortcuts import render, redirect
#from .models.factory import ElectricityFactory, ElectricityWorkingHoursPerMonth, FactoryProductionPlan
#from .models.legal import LegalEntity
#from .models.finance_modeling import BankLoan, BankLoanInterest, ElectricityPricePlan, ElectricityPrice
from vei_platform.models.profile import UserProfile, get_user_profile
#from .forms import FactoryFinancialPlaningForm, NumberPerMonthForm, PricePlanForm, BankLoanForm, UserProfileForm, FactoryScriperForm, SolarEstateListingForm
#from django.contrib.auth.decorators import login_required
#from django.core.paginator import Paginator
#from decimal import Decimal, DecimalException
#from django.forms import formset_factory
#from django.forms.models import model_to_dict
#from django.contrib import messages

#import re

#from django.contrib.auth.models import User

#from datetime import date

#from django_q.tasks import async_task
# Create your views here.

from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.finance_modeling import BankAccount
from decimal import Decimal
from vei_platform.templatetags.vei_platform_utils import balance_from_transactions


def get_balance(profile):
    legal_entities_pk = []
    entity = find_legal_entity(user=profile.user)
    if entity:
        legal_entities_pk.append(entity.pk)

    for factory in ElectricityFactory.objects.filter(manager=profile.user):
        if factory.primary_owner:
            legal_entities_pk.append(factory.primary_owner.pk)
    
    bank_accounts = BankAccount.objects.filter(owner__in=legal_entities_pk)
    amounts = {}
    for account in bank_accounts:
        cur = account.currency
        sum = amounts[cur] if cur in amounts.keys() else Decimal(0)
        balance = sum - balance_from_transactions(account)
        amounts[cur] = balance
    #amounts = {'BGN': Decimal(10), 'EUR': Decimal(20)}
    return amounts.items()

def common_context(request):
    context = {
        'platform_name': 'Solar Estates',
        'copyright': 'Data Intensive 2023',
    }
    if request:
        if request.user:
            if request.user.is_authenticated:
                profile = get_user_profile(request.user)
                context['profile'] = profile
                if profile.show_balance:
                    context['profile_balance'] = get_balance(profile)
    return context


def generate_formset_table(years, objects, NumberPerMonthFormSet, prefix):
    initial = []
    index = 0
    for year in years:
        for month in range(12):
            s = objects.filter(month__year=year).filter(
                month__month=month+1)
            if len(s) == 0:
                initial.append(
                    {'month': date(year=year, month=month+1, day=1)})
            else:
                initial.append({
                    'number': s[0].number,
                    'month': s[0].month
                })
            index = index + 1
    formset = NumberPerMonthFormSet(initial=initial, prefix=prefix)

    rows = []
    index = 0
    for year in years:
        row = []
        row.append(str(year))
        for month in range(12):
            val = formset[index].as_table()
            input = re.search(r'<td>(.*)</td>', val)
            if input:
                row.append(input.group(1))
            index = index + 1
        rows.append(row)
    table = {
        'labels': ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'rows': rows
    }
    return formset, table
