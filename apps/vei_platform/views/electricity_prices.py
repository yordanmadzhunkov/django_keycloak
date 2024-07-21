from . import common_context, generate_formset_table

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.forms import formset_factory

from vei_platform.models.profile import get_user_profile
from vei_platform.models.electricity_price import ElectricityPricePlan, ElectricityPrice
from vei_platform.forms import PricePlanForm, NumberPerMonthForm

from decimal import Decimal, DecimalException
from django.utils.translation import gettext as _


#@login_required(login_url='/oidc/authenticate/')
#def view_electricity_prices(request, pk=None):
#    context = common_context(request)
#    plan = ElectricityPricePlan.objects.get(pk=pk)
#    objects = ElectricityPrice.objects.filter(plan=plan)
#
#    # creating a formset
#    NumberPerMonthFormSet = formset_factory(NumberPerMonthForm, extra=0)
#    PricePlanFormSet = formset_factory(PricePlanForm, extra=0)
#    if request.POST:
#        numbers_formset = NumberPerMonthFormSet(request.POST, prefix='numbers')
#        plan_formset = PricePlanFormSet(request.POST, prefix='plan')
#        if numbers_formset.is_valid():
#            # All validation rules pass
#            # save to database :)
#            for form in numbers_formset:
#                number = form.cleaned_data['number']
#                month = form.cleaned_data['month']
#                try:
#                    val = Decimal(number)
#                    s = objects.filter(
#                        month__year=month.year).filter(month__month=month.month)
#                    if len(s) == 0:
#                        obj = ElectricityPrice(
#                            plan=plan, month=month, number=val)
#                        obj.save()
#                    else:
#                        if val != s[0].number:
#                            s[0].number = val
#                            s[0].save()
#                except (ValueError, DecimalException):
#                    pass
#        if plan_formset.is_valid():
#            # one form only
#            for form in plan_formset:
#                if plan.name != form.cleaned_data['name'] or plan.start_year != form.cleaned_data['start_year'] or plan.end_year != form.cleaned_data['end_year']:
#                    plan.name = form.cleaned_data['name']
#                    plan.start_year = form.cleaned_data['start_year']
#                    plan.end_year = form.cleaned_data['end_year']
#                    plan.save()
#
#    years = range(plan.start_year, plan.end_year + 1)
#    numbers_formset, table = generate_formset_table(
#        years, objects, NumberPerMonthFormSet, prefix='numbers')
#    plan_formset = PricePlanFormSet(
#        initial=[{'name': plan.name, 'start_year': plan.start_year, 'end_year': plan.end_year}], prefix='plan')
#    # print(plan_formset)
#    context['table'] = table
#    context['plan'] = plan
#    context['plan_formset'] = plan_formset
#    context['numbers_formset'] = numbers_formset
#    return render(request, "electricity_prices.html", context)

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from vei_platform.forms  import ElectricityPlanForm

class ElectricityPlanView(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        plan_slug = request.GET.get('plan')
        plans = ElectricityPricePlan.objects.all()
        form = ElectricityPlanForm(plans)
        context['form'] = form
        return render(request, "electricity_plan.html", context)

    def post(self, request, *args, **kwargs):
        context = common_context(request)
        form = ElectricityPlanForm(plans = ElectricityPricePlan.objects.all(), data=request.POST)
        if form.is_valid():
            context['form_data'] = form.cleaned_data
            context['plan_slug'] = form.cleaned_data['plan']
            print(context)
        context['form'] = form
        return render(request, "electricity_plan.html", context)
    

class ElectricityChart(View):
    def get(self, request, *args, **kwargs):

        plan_slug = request.GET.get('plan')
        plan = get_object_or_404(ElectricityPricePlan, slug=plan_slug)
        prices = ElectricityPrice.objects.filter(plan=plan)
        labels = []
        data = []
        for p in prices:
            labels.append(str(p.start_interval.strftime("%Y-%m-%d %H:%M:%S")))
            data.append(str(p.price).replace('BGN',''))
        print(data)
        #labels = ['11:00 pm', '12:00 pm', '13:00 pm']
        #data = [100.2, 230.48, 302]

        return JsonResponse(data={
            'labels': labels,
            'data': data,
            'title': 'You can\'t hit that'
        })