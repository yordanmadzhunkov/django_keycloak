from django.core.paginator import Paginator

from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import SolarEstateListing
from vei_platform.models.finance_modeling import ElectricityPricePlan, BankLoan
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import SolarEstateListingForm, FactoryFinancialPlaningForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from decimal import Decimal, DecimalException
from datetime import date
from django import template


@login_required(login_url='/oidc/authenticate/')
def view_factories_list(request):
    factories_list = ElectricityFactory.objects.all().order_by('pk')
    paginator = Paginator(factories_list, 5)  # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = common_context(request)
    context['page_obj'] = page_obj
    return render(request, "factories_list.html", context)

@login_required(login_url='/oidc/authenticate/')
def view_factory_offer_shares(request, pk=None):
    context = common_context(request)
    factory = ElectricityFactory.objects.get(pk=pk)
    context['factory'] = factory
    context['manager_profile'] = None if factory.manager is None else get_user_profile(factory.manager)
    context['factory_is_listed'] = SolarEstateListing.is_listed(factory)

    listings = SolarEstateListing.objects.filter(factory=factory)
    total_amount = Decimal(0)
    total_listed_persent = Decimal(0)
    total_available = Decimal(0)
    for listing in listings:
        total_amount += listing.amount
        total_listed_persent += listing.persent_from_profit
        total_available += 0

    context['listings_total'] = {
        'amount': total_amount,
        'available': total_available,
        'listed': total_listed_persent,
    }

    context['listings'] = listings

    if context['manager_profile']:
        capacity = factory.get_capacity_in_kw()
        fraction = Decimal(0.5)
        form = SolarEstateListingForm(initial={
            'amount': Decimal(1500) * capacity * fraction,
            'persent_from_profit': fraction * Decimal(100),
            'start_date': date(2023,12,1),
            'duration': Decimal(15*12),
            'commision': Decimal(1.5),
        })

    if request.method == 'POST':
        form = SolarEstateListingForm(data=request.POST)
        if form.is_valid():
            context['form_data'] = form.cleaned_data
            amount = form.cleaned_data['amount']
            persent_from_profit = form.cleaned_data['persent_from_profit']
            start_date = form.cleaned_data['start_date']
            duration = form.cleaned_data['duration']
            commision = form.cleaned_data['commision']
            listing = SolarEstateListing(
                    start_date=start_date, 
                    amount=Decimal(amount).quantize(Decimal('1.')), 
                    persent_from_profit=Decimal(persent_from_profit).quantize(Decimal('99.99')),
                    duration=Decimal(duration).quantize(Decimal('1.')), 
                    commision=Decimal(commision).quantize(Decimal('99.99')),
                    factory=factory
            )
            listing.save()
            messages.success(request, "You listed your factory")
        else:
            messages.error(request, "Form is not valid, please retry")

    context['create_listing_form'] = form
    return render(request, "factory_offer_shares.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_factory_detail(request, pk=None):
    context = common_context(request)
    factory = ElectricityFactory.objects.get(pk=pk)
    context['factory'] = ElectricityFactory.objects.get(pk=pk)
    context['production_plans'] = FactoryProductionPlan.objects.filter(
        factory=factory)
    context['price_plans'] = ElectricityPricePlan.objects.all()
    if factory.manager is None:
        context['manager'] = None
    else:
        profile = get_user_profile(factory.manager)
        context['manager_profile'] = get_user_profile(factory.manager)

    if request.method == 'POST':
        form = FactoryFinancialPlaningForm(factory=factory, data=request.POST)
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

        if '_become_manager' in request.POST:
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

            #print(form.cleaned_data)

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
        form = FactoryFinancialPlaningForm(factory=factory, data=None)
    context['form'] = form
    return render(request, "factory.html", context)





@login_required(login_url='/oidc/authenticate/')
def view_factory_production(request, pk=None):
    context = common_context(request)
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
    return render(request, "factory_production.html", context)





