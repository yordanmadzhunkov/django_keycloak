from django.core.paginator import Paginator
from django.http import HttpResponse

from . import common_context
from vei_platform.models.factory import (
    ElectricityFactory,
    ElectricityFactoryComponents,
)
from vei_platform.models.factory_production import ElectricityFactoryProduction

from vei_platform.models.electricity_price import ElectricityPricePlan, ElectricityPrice
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import (
    FactoryModelForm,
    ElectricityFactoryComponentsForm,
)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.views import View

from decimal import Decimal, DecimalException
from datetime import date
from django import template
from django.forms import BaseModelForm, formset_factory
from django.forms.models import model_to_dict

from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money


class FactoriesList(ListView):
    title = _("Electrical factories from renewable sources")
    model = ElectricityFactory
    template_name = "factories_list.html"
    paginate_by = 5

    def get_queryset(self):
        factories_list = ElectricityFactory.objects.all().order_by("pk")
        return factories_list

    def get_context_data(self, **kwargs):
        context = super(FactoriesList, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context["head_title"] = self.title
        return context


class FactoriesOfUserList(LoginRequiredMixin, FactoriesList):

    login_url = "/oidc/authenticate/"  # reverse_lazy('oidc_authentication_init')
    title = _("My Factories")

    def get_queryset(self):
        return ElectricityFactory.objects.filter(manager=self.request.user).order_by(
            "pk"
        )

    def get_context_data(self, **kwargs):
        context = super(FactoriesOfUserList, self).get_context_data(**kwargs)
        context["add_button"] = True
        return context


# @login_required(login_url='/oidc/authenticate/')
class FactoryDetail(View):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = ElectricityFactory.objects.get(pk=pk)
        context["factory"] = factory

        components = ElectricityFactoryComponents.objects.filter(factory=factory)
        context["components"] = components
        if factory.manager is None:
            context["manager"] = None
        else:
            # profile = get_user_profile(factory.manager)
            context["manager_profile"] = get_user_profile(factory.manager)
        return render(request, "factory.html", context)


def extract_error_messages_from(request, formset):
    for f in formset:
        if not f.is_valid():
            if "docfile" in f.errors.keys():
                s = str(f.errors["docfile"])
                if s.find("Filetype not supported") > 0:
                    messages.error(request, "Грешен тип на прикачения файл")
                elif s.find("Please keep filesize under") > 0:
                    messages.error(request, "Прикачения файл е прекаленно голям")
                else:
                    messages.error(request, "Файлът го няма - изчезнал е")


class FactoryEdit(UpdateView):
    model = ElectricityFactory
    template_name = "factory_components.html"
    form_class = FactoryModelForm
    success_url = None
    formset_fields = [
        "component_type",
        "power_in_kw",
        "count",
        "docfile",
        "name",
        "description",
    ]

    def get_context_data(self, **kwargs):
        context = super(FactoryEdit, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context["factory"] = self.object
        if self.request.POST:
            form = FactoryModelForm(self.request.POST, instance=self.object)
            context["form"] = form
            FactoryComponentsFormSet = inlineformset_factory(
                ElectricityFactory,
                ElectricityFactoryComponents,
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields,
                can_delete=True,
            )
            context["formset"] = FactoryComponentsFormSet(
                data=self.request.POST, files=self.request.FILES, instance=self.object
            )

        else:
            context["form"] = FactoryModelForm(instance=self.object)
            FactoryComponentsFormSet = inlineformset_factory(
                ElectricityFactory,
                ElectricityFactoryComponents,
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields,
                extra=2,
                can_delete=True,
            )
            context["formset"] = FactoryComponentsFormSet(instance=self.object)
        for f in context["formset"]:
            formset_helper = f.helper
            context["formset_helper"] = formset_helper
            # print(formset_helper)
            break
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if context["form"].save(commit=True):
            messages.info(self.request, _("Updated factory information"))
        else:
            messages.error(self.request, _("Failed to save factory form"))

        formset = context["formset"]
        for component_form in formset:
            if component_form.is_valid():
                d = component_form.cleaned_data
                # DELETE HARD
                do_delete = "DELETE" in d.keys() and d["DELETE"]
                if "id" in d.keys():
                    id = d["id"]
                    if id is not None and do_delete:
                        id.delete()
                    else:
                        component_form.save()

        extract_error_messages_from(self.request, formset)
        return super(FactoryEdit, self).form_valid(form)

    # def form_invalid(self, form: BaseModelForm) -> HttpResponse:
    #    return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("view_factory", kwargs={"pk": self.object.pk})


class FactoryCreate(CreateView):
    model = ElectricityFactory
    template_name = "factory_create.html"
    form_class = FactoryModelForm
    success_url = None
    formset_fields = [
        "component_type",
        "name",
        "power_in_kw",
        "count",
        "docfile",
        "description",
    ]

    def get_context_data(self, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("login")

        context = super(FactoryCreate, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context["factory"] = self.object
        if self.request.POST:
            form = FactoryModelForm(
                data=self.request.POST, files=self.request.FILES, instance=self.object
            )
            context["form"] = form
        else:
            context["form"] = FactoryModelForm(instance=self.object)
            FactoryComponentsFormSet = inlineformset_factory(
                ElectricityFactory,
                ElectricityFactoryComponents,
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields,
                extra=2,
                can_delete=True,
            )
            context["formset"] = FactoryComponentsFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        created_factory = form.save(commit=True)
        created_factory.manager = self.request.user
        created_factory.save()
        messages.success(self.request, _("Electrical factory added"))

        FactoryComponentsFormSet = inlineformset_factory(
            ElectricityFactory,
            ElectricityFactoryComponents,
            form=ElectricityFactoryComponentsForm,
            fields=self.fields,
            can_delete=True,
        )
        formset = FactoryComponentsFormSet(
            data=self.request.POST, files=self.request.FILES, instance=created_factory
        )
        if formset.is_valid():
            formset.save()
        extract_error_messages_from(self.request, formset)
        return super(FactoryCreate, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Invalid data, please try again"))
        return super(FactoryCreate).form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("view_factory", kwargs={"pk": self.object.pk})


class FactoryProduction(View):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = ElectricityFactory.objects.get(pk=pk)
        context["factory"] = factory

        components = ElectricityFactoryComponents.objects.filter(factory=factory)
        context["components"] = components
        if factory.manager is None:
            context["manager"] = None
        else:
            # profile = get_user_profile(factory.manager)
            context["manager_profile"] = get_user_profile(factory.manager)
        return render(request, "factory_production.html", context)


def datetime_to_chartjs_format(dt, tz):
    return str(dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"))


import pytz
from django.http import JsonResponse


class FactoryProductionChart(View):
    def get(self, request, *args, **kwargs):
        factory_slug = request.GET.get("factory")
        factory = get_object_or_404(ElectricityFactory, slug=factory_slug)
        num_days = 7
        production = ElectricityFactoryProduction.objects.filter(
            factory=factory
        ).order_by("-start_interval")[: 24 * num_days]
        x = []
        y1 = []
        y2 = []
        prices = ElectricityPrice.objects.filter(plan=factory.plan)
        display_currency = factory.currency
        requested_timezone = factory.timezone
        if requested_timezone is None:
            requested_timezone = "UTC"
        tz = pytz.timezone(requested_timezone)
        x_scale = requested_timezone + " timezone"
        x_min = None
        x_max = datetime_to_chartjs_format(production[0].end_interval, tz)
        for p in production:
            x.append(datetime_to_chartjs_format(p.start_interval, tz))
            y1.append(p.energy_in_kwh)
            p2 = prices.filter(start_interval=p.start_interval)
            if len(p2) > 0:
                y2.append(Decimal(convert_money(p2[0].price, display_currency).amount))
            else:
                y2.append(None)
        x_min = datetime_to_chartjs_format(p.start_interval, tz=tz)
        y1 = y1[::-1]
        y2 = y2[::-1]
        x = x[::-1]
        #y1.append(y1[-1])
        y2.append(y2[-1])
        x.append(x_max)
        y_scale = "kWh"
        return JsonResponse(
            data={
                "x_values": x,
                "y1_values": y1,
                "y2_values": y2,
                "y1_label": factory.name + " Production in " + y_scale,
                "y2_label": factory.plan.name,
                "y_scale": y_scale,
                "x_scale": x_scale,
                "x_min": x_min,
                "x_max": x_max,
            }
        )
