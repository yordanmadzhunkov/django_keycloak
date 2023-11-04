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
