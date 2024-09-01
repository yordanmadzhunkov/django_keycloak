from django.core.paginator import Paginator
from django.http import HttpResponse

from . import common_context
from vei_platform.models.factory import (
    ElectricityFactory,
    ElectricityFactoryComponents,
)
from vei_platform.models.factory_production import ElectricityFactoryProduction

from vei_platform.models.campaign import Campaign
from vei_platform.models.electricity_price import ElectricityPricePlan
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import (
    CampaignCreateForm,
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


class FactoriesList(ListView):
    title = _("Electrical factories from renewable sources")
    model = ElectricityFactory
    template_name = "factories_list.html"
    paginate_by = 5

    def get_queryset(self):
        listed = self.view_offered_factories()
        factories_list = ElectricityFactory.objects.filter(pk__in=listed).order_by("pk")
        return factories_list

    def get_context_data(self, **kwargs):
        context = super(FactoriesList, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context["head_title"] = self.title
        return context

    def view_offered_factories(self):
        campaigns = Campaign.objects.filter(status=Campaign.Status.ACTIVE).order_by(
            "factory"
        )
        prev = None
        listed = []
        for l in campaigns:
            if prev != l.factory.pk:
                # print(l.factory.name)
                listed.append(l.factory.pk)
            prev = l.factory.pk
        return listed


class FactoriesForReview(FactoriesList):
    def view_offered_factories(self):
        campaigns = Campaign.objects.filter(
            status=Campaign.Status.INITIALIZED
        ).order_by("factory")
        prev = None
        listed = []
        for l in campaigns:
            if l.get_last_campaign(l.factory):
                if prev != l.factory.pk:
                    listed.append(l.factory.pk)
                prev = l.factory.pk
        return listed


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


class CampaignCreate(CreateView):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        # factory = ElectricityFactory.objects.get(pk=pk)
        context["factory"] = factory
        context["manager_profile"] = get_user_profile(factory.manager)
        # Check if user is manager
        if context["profile"].pk == context["manager_profile"].pk:
            capacity = factory.get_capacity_in_kw()
            fraction = Decimal(0.5)
            form = CampaignCreateForm(
                initial={
                    "amount_offered": Money(
                        Decimal(1500) * capacity * fraction, currency="BGN"
                    ),
                    "persent_from_profit": fraction * Decimal(100),
                    "start_date": date(2024, 12, 1),
                    "duration": Decimal(15 * 12),
                    "commision": Decimal(1.5),
                }
            )
            context["new_campaign_form"] = form
            context["hide_link_buttons"] = True
        else:
            messages.error(request, _("Only factory manager can initiate campaign"))
            return redirect(factory.get_absolute_url())
        return render(request, "campaign_create.html", context)

    def post(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        form = CampaignCreateForm(data=request.POST)
        if form.is_valid():
            context["form_data"] = form.cleaned_data
            amount = form.cleaned_data["amount_offered"]
            persent_from_profit = form.cleaned_data["persent_from_profit"]
            start_date = form.cleaned_data["start_date"]
            duration = form.cleaned_data["duration"]
            commision = form.cleaned_data["commision"]
            campaign = Campaign(
                start_date=start_date,
                amount=amount,
                persent_from_profit=Decimal(persent_from_profit).quantize(
                    Decimal("99.99")
                ),
                duration=Decimal(duration).quantize(Decimal("1.")),
                commision=Decimal(commision).quantize(Decimal("99.99")),
                factory=factory,
            )
            campaign.save()
            messages.success(
                request,
                _(
                    "You have successfully started a campaign to collect investors until %s"
                )
                % (start_date),
            )
            return redirect(campaign.get_absolute_url())
        else:
            messages.error(request, _("Invalid data, please try again"))

        context["factory"] = factory
        context["new_campaign_form"] = form
        context["hide_link_buttons"] = True
        return render(request, "campaign_create.html", context)


# @login_required(login_url='/oidc/authenticate/')
class FactoryDetail(View):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = ElectricityFactory.objects.get(pk=pk)
        context["factory"] = factory

        campaigns = Campaign.objects.filter(
            factory=factory
        )  # .exclude(status=Campaign.Status.CANCELED)
        context["campaigns"] = campaigns

        components = ElectricityFactoryComponents.objects.filter(factory=factory)
        context["components"] = components
        context["price_plans"] = ElectricityPricePlan.objects.all()
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
        context["price_plans"] = ElectricityPricePlan.objects.all()
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
        num_days = 3
        production = ElectricityFactoryProduction.objects.filter(factory=factory).order_by("-start_interval")[
            : 24 * num_days
        ]
        x = []
        y = []
        requested_timezone = request.GET.get("timezone")
        if requested_timezone is None:
            requested_timezone = "UTC"
        tz = pytz.timezone(requested_timezone)
        # pytz.tzinfo.StaticTzInfo
        # offset_str = datetime.datetime.now().astimezone(pytz_tz).strftime("%z")
        x_scale = requested_timezone + " timezone"
        x_min = None
        x_max = datetime_to_chartjs_format(production[0].end_interval, tz)
        for p in production:
            x.append(datetime_to_chartjs_format(p.start_interval, tz))
            y.append(p.energy_in_kwh)
        x_min = datetime_to_chartjs_format(p.start_interval, tz=tz)
        y = y[::-1]
        x = x[::-1]
        y.append(y[-1])
        x.append(x_max)
        y_scale = "kWh"
        return JsonResponse(
            data={
                "x_values": x,
                "y1_values": y,
                "y2_values": y,
                "label": factory.name + " Production in " + y_scale,
                "y_scale": y_scale,
                "x_scale": x_scale,
                "x_min": x_min,
                "x_max": x_max,
            }
        )
