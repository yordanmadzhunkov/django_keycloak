from . import common_context, generate_formset_table

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.forms import formset_factory

from vei_platform.models.profile import get_user_profile
from vei_platform.models.electricity_price import ElectricityPricePlan, ElectricityPrice
from vei_platform.forms import PricePlanForm, NumberPerMonthForm

from decimal import Decimal, DecimalException
from django.utils.translation import gettext as _

import pytz

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from vei_platform.forms import ElectricityPlanForm


class ElectricityPlanView(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        plan_slug = request.GET.get("plan")
        plans = ElectricityPricePlan.objects.all()
        initial_timezone = (
            get_user_profile(self.request.user).timezone
            if self.request.user.is_authenticated
            else "Europe/Sofia"
        )
        p = None
        for p in plans:
            if p.name == "BG Day ahead":
                plan_slug = p.slug

        form = ElectricityPlanForm(
            plans, initial_timezone=initial_timezone, initial_plan=plan_slug
        )
        context["form"] = form
        return render(request, "electricity_plan.html", context)

    def post(self, request, *args, **kwargs):
        context = common_context(request)
        form = ElectricityPlanForm(
            plans=ElectricityPricePlan.objects.all(), data=request.POST
        )
        if form.is_valid():
            context["form_data"] = form.cleaned_data
            context["plan_slug"] = form.cleaned_data["plan"]
            context["display_currency"] = form.cleaned_data["currency"]
            context["timezone"] = form.cleaned_data["timezone"]
            context["days"] = form.cleaned_data["days"]

            # print(context)
        context["form"] = form
        return render(request, "electricity_plan.html", context)


def datetime_to_chartjs_format(dt, tz):
    return str(dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"))


from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money


class ElectricityPriceChart(View):
    def get(self, request, *args, **kwargs):
        plan_slug = request.GET.get("plan")
        plan = get_object_or_404(ElectricityPricePlan, slug=plan_slug)
        display_currency = request.GET.get("display_currency")
        if display_currency is None:
            display_currency = "EUR"
        num_days = request.GET.get("days")
        if num_days is None:
            num_days = 1
        else:
            num_days = int(num_days)
            if num_days < 1 or num_days > 30:
                num_days = 1

        prices = ElectricityPrice.objects.filter(plan=plan).order_by("-start_interval")[
            : 24 * num_days
        ]
        labels = []
        data = []
        requested_timezone = request.GET.get("timezone")
        if requested_timezone is None:
            requested_timezone = "UTC"
        tz = pytz.timezone(requested_timezone)
        # pytz.tzinfo.StaticTzInfo
        # offset_str = datetime.datetime.now().astimezone(pytz_tz).strftime("%z")
        x_scale = requested_timezone + " timezone"
        x_min = None
        x_max = datetime_to_chartjs_format(prices[0].end_interval, tz)
        for p in prices:
            labels.append(datetime_to_chartjs_format(p.start_interval, tz))
            data.append(convert_money(p.price, display_currency).amount)
        x_min = datetime_to_chartjs_format(p.start_interval, tz=tz)
        data = data[::-1]
        labels = labels[::-1]
        data.append(data[-1])
        labels.append(x_max)
        y_scale = display_currency + "/" + plan.electricity_unit
        return JsonResponse(
            data={
                "labels": labels,
                "data": data,
                "plan_name": plan.name + " " + y_scale,
                "y_scale": y_scale,
                "x_scale": x_scale,
                "x_min": x_min,
                "x_max": x_max,
            }
        )
