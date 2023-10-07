from django.shortcuts import render, redirect
from .models.factory import ElectricityFactory, ElectricityWorkingHoursPerMonth, FactoryProductionPlan
from .models.legal import LegalEntity
from .models.finance_modeling import BankLoan, BankLoanInterest, ElectricityPricePlan, ElectricityPrice
from .models.profile import UserProfile, get_user_profile
from .forms import FactoryFinancialPlaning, NumberPerMonthForm, PricePlanForm, BankLoanForm, UserProfileForm, FactoryScriperForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from decimal import Decimal, DecimalException
from django.forms import formset_factory
from django.forms.models import model_to_dict
from django.contrib import messages

import re

from django.contrib.auth.models import User

from datetime import date

from django_q.tasks import async_task
# Create your views here.


def common_context():
    context = {
        'platform_name': 'Solar Estates',
        'copyright': 'Data Intensive 2023',
    }
    return context


@login_required(login_url='/oidc/authenticate/')
def view_home(request):
    context = common_context()
    if request.user.is_authenticated:
        context['profile'] = get_user_profile(request.user)
    return render(request, "home.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_factories_list(request):
    factories_list = ElectricityFactory.objects.all().order_by('pk')
    paginator = Paginator(factories_list, 5)  # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = common_context()
    context['page_obj'] = page_obj
    context['profile'] = get_user_profile(request.user)
    return render(request, "factories_list.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_dashboard(request):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    scripe_form = FactoryScriperForm(request.POST)
    if request.method == "POST":
        if 'scripe_page' in request.POST and scripe_form.is_valid():

            # messages.error(request, 'Profile error')
            page_number = int(scripe_form.cleaned_data.get('page_number'))
            limit = 1
            async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
            messages.success(
                request, 'Form is valid with number = %d' % page_number)

        if 'scripe_all' in request.POST:
            page_number = 1
            limit = 10000
            async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
            messages.success(request, 'Scriping all pages!')
    context['scripe_form'] = scripe_form
    return render(request, "dashboard.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_my_profile(request):
    context = common_context()
    avatar_form = UserProfileForm(request.POST or None, request.FILES or None)
    profile = get_user_profile(request.user)
    if avatar_form.is_valid():
        avatar = avatar_form.cleaned_data.get('avatar')
        if avatar is not None:
            if profile is None:
                profile = UserProfile(user=request.user, avatar=avatar)
            else:
                profile.avatar = avatar
            profile.save()
            messages.success(
                request, '%s uploaded and set as profile picture successfully' % avatar)

        first_name = avatar_form.cleaned_data.get('first_name')
        last_name = avatar_form.cleaned_data.get('last_name')
        user = User.objects.get(username=request.user)

        if (first_name is not None and first_name != user.first_name) or (last_name is not None and last_name != user.last_name):
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, 'Name set to %s %s' %
                             (first_name, last_name))
            context['user'] = user
    else:
        if request.method == "POST":
            messages.error(request, 'Profile error')
    context['avatar_form'] = avatar_form
    context['profile'] = get_user_profile(request.user)
    return render(request, "my_profile.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_user_profile(request, pk=None):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    context['user_profile'] = UserProfile.objects.get(pk=pk)
    return render(request, "user_profile.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_factory_detail(request, pk=None):
    context = common_context()
    factory = ElectricityFactory.objects.get(pk=pk)
    context['factory'] = ElectricityFactory.objects.get(pk=pk)
    context['production_plans'] = FactoryProductionPlan.objects.filter(
        factory=factory)
    context['price_plans'] = ElectricityPricePlan.objects.all()
    if factory.manager is None:
        context['manager'] = None
    else:
        profile = get_user_profile(factory.manager)
        # profile.get_avatar_url()
        context['manager'] = profile.user.first_name + \
            ' ' + profile.user.last_name
        context['manager_avatar_url'] = profile.avatar.url
        context['manager_profile'] = get_user_profile(factory.manager)

    if request.method == 'POST':
        form = FactoryFinancialPlaning(factory=factory, data=request.POST)
        if '_add_production' in request.POST:
            plan = FactoryProductionPlan(
                name="Работни часове на месец", factory=factory)
            plan.save()
            return redirect(plan.get_absolute_url())

        if '_add_price' in request.POST:
            prices = ElectricityPricePlan(
                name="Стандартна цена на тока", factory=factory)
            prices.save()
            return redirect(prices.get_absolute_url())

        if '_add_bank_loan' in request.POST:
            bank_loan = BankLoan(  # name="Банков заем",
                start_date=factory.opened,
                amount=factory.capacity_in_mw *
                Decimal(1700000),
                duration=12*15,
                factory=factory)
            bank_loan.save()
            return redirect(bank_loan.get_absolute_url())

        if '_become_manager':
            if factory.manager is None:
                factory.manager = request.user
                factory.save()
                messages.success(request, "You are now manager")
            else:
                messages.error(request, "Already taken")

        if form.is_valid():
            context['form_data'] = form.cleaned_data
            start_year = form.cleaned_data['start_year']
            end_year = form.cleaned_data['end_year']

            print(form.cleaned_data)

            plan = FactoryProductionPlan.objects.get(
                pk=int(form.cleaned_data['production_plan']))
            if '_edit_production' in request.POST:
                return redirect(plan.get_absolute_url())

            prices = ElectricityPricePlan.objects.get(
                pk=int(form.cleaned_data['electricity_prices']))
            if '_edit_price' in request.POST:
                return redirect(prices.get_absolute_url())

            loan = BankLoan.objects.get(
                pk=int(form.cleaned_data['bank_loan']))
            if '_edit_bank_loan' in request.POST:
                return redirect(loan.get_absolute_url())

            capacity = factory.capacity_in_mw
            capitalization = form.cleaned_data['capitalization']
            start_date = form.cleaned_data['start_date']

            rows = []
            labels = ['Месец', 'Приходи']
            for year in range(start_year, end_year + 1):
                for month in range(1, 13):
                    row = []
                    p = date(year, month, 1)
                    row.append(p.strftime('%b %y'))
                    row.append(
                        plan.get_working_hours(p) * factory.capacity_in_mw * prices.get_price(p))

                    rows.append(row)

            table = {'labels': labels, 'rows': rows}
            context['plan'] = {'table': table}
    else:
        form = FactoryFinancialPlaning(factory=factory, data=None)
    context['form'] = form
    context['profile'] = get_user_profile(request.user)
    return render(request, "factory.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_entity_detail(request, pk=None):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    if pk is not None:
        legal_entity = LegalEntity.objects.get(pk=pk)
        context['legal_entity'] = legal_entity
        factories_list = ElectricityFactory.objects.all().filter(
            primary_owner=legal_entity).order_by('pk')
        print(factories_list)
        paginator = Paginator(factories_list, 5)  # Show 25 contacts per page.
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
    return render(request, "legal_entity.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_factory_production(request, pk=None):
    context = common_context()
    plan = FactoryProductionPlan.objects.get(pk=pk)
    factory = plan.factory
    context['factory'] = factory
    context['plan'] = plan
    objects = ElectricityWorkingHoursPerMonth.objects.filter(plan=plan)

    # creating a formset
    NumberPerMonthFormSet = formset_factory(
        NumberPerMonthForm, extra=0)
    PricePlanFormSet = formset_factory(PricePlanForm, extra=0)
    plan_formset = PricePlanFormSet(
        initial=[{'name': plan.name, 'start_year': plan.start_year, 'end_year': plan.end_year}], prefix='plan')

    if request.POST:
        formset = NumberPerMonthFormSet(request.POST, prefix='numbers')
        plan_formset = PricePlanFormSet(request.POST, prefix='plan')

        if formset.is_valid():
            # All validation rules pass
            # save to database :)
            for form in formset:
                hours_str = form.cleaned_data['number']
                month = form.cleaned_data['month']
                try:
                    val = Decimal(hours_str)
                    s = objects.filter(
                        month__year=month.year).filter(month__month=month.month)
                    if len(s) == 0:
                        obj = ElectricityWorkingHoursPerMonth(
                            plan=plan, month=month, number=val)
                        obj.save()
                    else:
                        if val != s[0].number:
                            s[0].number = val
                            s[0].save()
                except (ValueError, DecimalException):
                    pass
        if plan_formset.is_valid():
            # one form only
            for form in plan_formset:
                if plan.name != form.cleaned_data['name'] or plan.start_year != form.cleaned_data['start_year'] or plan.end_year != form.cleaned_data['end_year']:
                    plan.name = form.cleaned_data['name']
                    plan.start_year = form.cleaned_data['start_year']
                    plan.end_year = form.cleaned_data['end_year']
                    plan.save()

            # return redirect(factory.get_absolute_url())
    # else:
    years = range(plan.start_year, plan.end_year + 1)
    formset, table = generate_formset_table(
        years, objects, NumberPerMonthFormSet, prefix='numbers')
    context['table'] = table
    context['formset'] = formset
    context['plan_formset'] = plan_formset
    context['profile'] = get_user_profile(request.user)

    return render(request, "factory_production.html", context)


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


@login_required(login_url='/oidc/authenticate/')
def view_electricity_prices(request, pk=None):
    context = common_context()
    plan = ElectricityPricePlan.objects.get(pk=pk)
    objects = ElectricityPrice.objects.filter(plan=plan)

    # creating a formset
    NumberPerMonthFormSet = formset_factory(NumberPerMonthForm, extra=0)
    PricePlanFormSet = formset_factory(PricePlanForm, extra=0)
    if request.POST:
        numbers_formset = NumberPerMonthFormSet(request.POST, prefix='numbers')
        plan_formset = PricePlanFormSet(request.POST, prefix='plan')
        if numbers_formset.is_valid():
            # All validation rules pass
            # save to database :)
            for form in numbers_formset:
                number = form.cleaned_data['number']
                month = form.cleaned_data['month']
                try:
                    val = Decimal(number)
                    s = objects.filter(
                        month__year=month.year).filter(month__month=month.month)
                    if len(s) == 0:
                        obj = ElectricityPrice(
                            plan=plan, month=month, number=val)
                        obj.save()
                    else:
                        if val != s[0].number:
                            s[0].number = val
                            s[0].save()
                except (ValueError, DecimalException):
                    pass
        if plan_formset.is_valid():
            # one form only
            for form in plan_formset:
                if plan.name != form.cleaned_data['name'] or plan.start_year != form.cleaned_data['start_year'] or plan.end_year != form.cleaned_data['end_year']:
                    plan.name = form.cleaned_data['name']
                    plan.start_year = form.cleaned_data['start_year']
                    plan.end_year = form.cleaned_data['end_year']
                    plan.save()

    years = range(plan.start_year, plan.end_year + 1)
    numbers_formset, table = generate_formset_table(
        years, objects, NumberPerMonthFormSet, prefix='numbers')
    plan_formset = PricePlanFormSet(
        initial=[{'name': plan.name, 'start_year': plan.start_year, 'end_year': plan.end_year}], prefix='plan')
    # print(plan_formset)
    context['table'] = table
    context['plan'] = plan
    context['plan_formset'] = plan_formset
    context['numbers_formset'] = numbers_formset
    context['profile'] = get_user_profile(request.user)
    return render(request, "electricity_prices.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_bank_loan_detail(request, pk=None):
    context = common_context()
    loan = BankLoan.objects.get(pk=pk)
    objects = BankLoanInterest.objects.filter(loan=loan)
    factory = loan.factory

    # creating a formset
    NumberPerMonthFormSet = formset_factory(
        NumberPerMonthForm, extra=0)
    PricePlanFormSet = formset_factory(BankLoanForm, extra=0)

    if request.POST:
        numbers_formset = NumberPerMonthFormSet(request.POST, prefix='numbers')
        loan_formset = PricePlanFormSet(request.POST, prefix='loan')

        if numbers_formset.is_valid():
            # All validation rules pass
            # save to database :)
            for form in numbers_formset:
                hours_str = form.cleaned_data['number']
                month = form.cleaned_data['month']
                try:
                    val = Decimal(hours_str)
                    s = objects.filter(
                        month__year=month.year).filter(month__month=month.month)
                    if len(s) == 0:
                        obj = BankLoanInterest(
                            loan=loan, month=month, number=val)
                        obj.save()
                    else:
                        if val != s[0].number:
                            s[0].number = val
                            s[0].save()
                except (ValueError, DecimalException):
                    pass
        if loan_formset.is_valid():
            # one form only
            for form in loan_formset:
                needs_save = False
                if loan.duration != form.cleaned_data['duration']:
                    loan.duration = form.cleaned_data['duration']
                    needs_save = True

                if loan.start_date != form.cleaned_data['start_date']:
                    loan.start_date = form.cleaned_data['start_date']
                    needs_save = True

                if loan.amount != form.cleaned_data['amount']:
                    loan.amount = form.cleaned_data['amount']
                    needs_save = True

                if needs_save:
                    loan.save()

        return redirect(factory.get_absolute_url())

    years = range(loan.start_year(), loan.end_year())
    numbers_formset, table = generate_formset_table(
        years, objects, NumberPerMonthFormSet, prefix='numbers')
    loan_formset = PricePlanFormSet(
        initial=[model_to_dict(loan)], prefix='loan')
    context['table'] = table

    rows = []
    labels = ['Месец', 'Вноска', 'Погасена лихва',
              'Погасена главница', 'Оставаща главница']
    amortization_schedule = loan.amortization_schedule()
    for row in amortization_schedule:
        number, payment, interest, principal, balance = row
        rows.append(
            [loan.offset_start_date(number).strftime(
                '%b %y'), payment, interest, principal, balance]
        )

    table = {'labels': labels, 'rows': rows}
    context['amortization_schedule'] = {'table': table}
    context['loan_formset'] = loan_formset
    context['numbers_formset'] = numbers_formset
    context['factory'] = factory
    context['profile'] = get_user_profile(request.user)

    return render(request, "bank_loan.html", context)
