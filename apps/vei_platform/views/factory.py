from django.core.paginator import Paginator
from django.http import HttpResponse

from . import common_context
from vei_platform.models.factory import (
    ElectricityFactory,
    ElectricityFactoryComponents,
)
from vei_platform.models.production import (
    ElectricityFactoryProduction,
    ElectricityFactoryUploadedProductionReport,
    ElectricityFactoryProductionReport,
    process_excel_report,
)
from vei_platform.models.schedule import MinPriceCriteria, ElectricityFactorySchedule

from vei_platform.models.electricity_price import ElectricityPrice

from vei_platform.models.profile import get_user_profile
from vei_platform.forms import (
    FactoryModelForm,
    ElectricityFactoryComponentsForm,
    FactoryScheduleForm,
    UploadFileForm,
)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, FormView
from django.views import View

from decimal import Decimal
from datetime import timedelta, datetime, timezone


from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money

from vei_platform.api.electricity_prices import (
    ElectricityFactoryScheduleSerializer,
    send_notifications,
)
import os

from vei_platform.api.electricity_prices import ElectricityProductionSerializer


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
            context["manager_profile"] = get_user_profile(factory.manager)
            if factory.manager == request.user:
                context["form"] = UploadFileForm()
                context["reports"] = self.get_production_reports(factory)
        return render(request, "factory_production.html", context)

    def get_production_reports(self, factory):
        res = []
        for r in (
            ElectricityFactoryProductionReport.objects.filter(factory=factory)
            .order_by("year")
            .order_by("month")
        ):
            res.append(
                {
                    "year": r.year,
                    "month": r.month,
                    "name": os.path.basename(r.report.docfile.name),
                    "status": r.report.updated_at,
                    "url": r.report.docfile.url,
                }
            )
        return res

    def create_excel_report(
        self, user, file_in_memory
    ) -> ElectricityFactoryUploadedProductionReport:
        filename = str(file_in_memory)
        path = "documents/user_{0}/{1}".format(str(user), filename)
        excel_report = ElectricityFactoryUploadedProductionReport.objects.create(
            docfile=path, owner=user
        )
        dir = excel_report.docfile.storage.path("documents/user_{0}".format(str(user)))
        os.makedirs(dir, exist_ok=True)
        with excel_report.docfile.open("wb+") as destination:
            for chunk in file_in_memory.chunks():
                destination.write(chunk)
            destination.close()
        return excel_report

    def post(self, request, pk=None, *args, **kwargs):
        # context = common_context(request)
        # print(request.FILES)
        # print(request.POST)
        if "upload" in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                for f in form.cleaned_data["files"]:
                    excel_report = self.create_excel_report(
                        user=request.user, file_in_memory=f
                    )
                    report = process_excel_report(excel_report.docfile.path)
                    if isinstance(report, dict) and "error" in report.keys():
                        messages.error(request, report["error"])
                    elif isinstance(report, list):
                        excel_report.save()
                        for factory_res in report:
                            errors = factory_res["errors"]
                            for e in errors:
                                messages.error(request, e)
                            self.update_production_of_factory(
                                request, excel_report, factory_res
                            )
                    else:
                        messages.error(
                            request,
                            "Unknown error from FactoryProduction View post method",
                        )
            else:
                messages.error(request, form.errors.as_text())
        return self.get(request, pk, args, kwargs)

    def update_production_of_factory(self, request, excel_report, factory_res):
        if factory_res["factory_slug"] is not None:
            factory = ElectricityFactory.objects.get(slug=factory_res["factory_slug"])
            if factory:
                month = factory_res["month"]
                year = factory_res["year"]
                try:
                    report_for_factory = ElectricityFactoryProductionReport.objects.get(
                        factory=factory, year=year, month=month
                    )
                    report_for_factory.report = excel_report
                except ElectricityFactoryProductionReport.DoesNotExist:
                    report_for_factory = (
                        ElectricityFactoryProductionReport.objects.create(
                            report=excel_report,
                            factory=factory,
                            year=year,
                            month=month,
                        )
                    )
                finally:
                    messages.info(
                        request,
                        "Production report updated for year %d month %d factory %s"
                        % (year, month, factory.name),
                    )
                    production_in_kwh = factory_res["production_in_kwh"]
                    production = ElectricityFactoryProduction.objects.filter(
                        factory=factory
                    )
                    new_production = 0
                    matched_production = 0
                    updated_production = 0
                    for prod in production_in_kwh:
                        start_interval = datetime.strptime(
                            prod["start_interval"], "%Y-%m-%dT%H:%M:%S%z"
                        )
                        end_interval = datetime.strptime(
                            prod["end_interval"], "%Y-%m-%dT%H:%M:%S%z"
                        )
                        energy_in_kwh = prod["energy_in_kwh"]
                        try:
                            p = production.get(start_interval=start_interval)
                            if (
                                p.energy_in_kwh == energy_in_kwh
                                and end_interval == p.end_interval
                            ):
                                matched_production += 1
                            else:
                                p.energy_in_kwh = energy_in_kwh
                                p.end_interval = end_interval
                                p.save()
                                updated_production += 1
                        except ElectricityFactoryProduction.DoesNotExist:
                            new_prod = ElectricityFactoryProduction.objects.create(
                                factory=factory,
                                start_interval=start_interval,
                                end_interval=end_interval,
                                energy_in_kwh=energy_in_kwh,
                            )
                            new_prod.save()
                            new_production += 1
                        finally:
                            pass

                    report_for_factory.save()
                    messages.success(
                        request,
                        "Factory %s new=%d, updated=%d, matched=%d"
                        % (
                            factory.name,
                            new_production,
                            updated_production,
                            matched_production,
                        ),
                    )


class FactoryScheduleView(FormView):

    def get_min_price_in_display_currency(self, factory: ElectricityFactory):
        display_currency = factory.currency
        min_price = MinPriceCriteria.objects.filter(factory=factory).first()
        if min_price is not None:
            min_price_in_display_currency = Decimal(
                convert_money(min_price.min_price, display_currency).amount
            )
        else:
            min_price_in_display_currency = None
        return min_price_in_display_currency

    def get_schedule(self, factory: ElectricityFactory):
        prices = factory.get_last_prices(num_days=4)
        working = ElectricityFactorySchedule.get_last(factory=factory, num_days=4)
        min_price_in_display_currency = self.get_min_price_in_display_currency(factory)
        tz = factory.get_pytz_timezone()
        headers = ["%s" % tz.zone]
        rows = []
        j = 0
        if len(prices) > 0:
            for i in range(24):
                rows.append(
                    [
                        {
                            "text": "%d:00 - %d:00" % (i, i + 1),
                        }
                    ]
                )
            start_date = prices[0].start_interval.astimezone(tz).date()
            end_date = prices[len(prices) - 1].start_interval.astimezone(tz).date()

            d = start_date
            now = datetime.now(tz=timezone.utc)
            while d <= end_date:
                headers.append(d)
                for i in range(24):
                    t = tz.localize(
                        datetime(
                            year=d.year,
                            month=d.month,
                            day=d.day,
                            hour=i,
                        )
                    )
                    while j < len(working) and working[j].start_interval < t:
                        j = j + 1
                    if j < len(working) and working[j].start_interval == t:
                        value = "On" if working[j].working else "Off"
                        color = "success" if working[j].working else "danger"
                        rows[i].append(
                            {
                                "color": color,
                                "text_color": "gray-100",
                                "text": str(value),
                            }
                        )
                    else:
                        p = ElectricityPrice.objects.filter(plan=factory.plan).filter(
                            start_interval=t
                        )
                        if len(p) > 0:
                            value = Decimal(
                                convert_money(p[0].price, factory.currency).amount
                            ).quantize(Decimal("1.00"))
                            color = (
                                "warning"
                                if min_price_in_display_currency is not None
                                and value < min_price_in_display_currency
                                else "info"
                            )
                            if now < t:
                                color = (
                                    "danger"
                                    if min_price_in_display_currency is not None
                                    and value < min_price_in_display_currency
                                    else "success"
                                )
                            rows[i].append(
                                {
                                    "color": color,
                                    "text_color": "gray-100",
                                    "text": str(value),
                                }
                            )
                        else:
                            rows[i].append({"text": "-"})
                d = d + timedelta(days=1)

        return {
            "headers": headers,
            "rows": rows,
        }

    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        context["factory"] = factory
        if factory.manager is None:
            context["manager"] = None
        else:
            context["manager_profile"] = get_user_profile(factory.manager)
        context["form"] = FactoryScheduleForm(
            instance=MinPriceCriteria.objects.filter(factory=factory).first()
        )
        context["schedule"] = self.get_schedule(factory)
        return render(request, "factory_schedule.html", context)

    def post(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        context["factory"] = factory
        if factory.manager is None:
            context["manager"] = None
        else:
            # profile = get_user_profile(factory.manager)
            context["manager_profile"] = get_user_profile(factory.manager)
        form = FactoryScheduleForm(data=request.POST)
        context["form"] = form

        if "generate" in self.request.POST:
            new_schedule = ElectricityFactorySchedule.generate_schedule(
                factory, num_days=4
            )
            serializer = ElectricityFactoryScheduleSerializer(
                many=True, data=new_schedule
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            send_notifications(factory, serializer.data)
            num_created = len(new_schedule)
            if num_created > 0:
                messages.success(
                    self.request,
                    _("Generated %d hours of production schedule") % num_created,
                )
            else:
                messages.warning(self.request, _("No new hours of production schedule"))

        if "save" in self.request.POST:
            if form.is_valid():
                queryset = MinPriceCriteria.objects.filter(factory=factory)
                if len(queryset) == 0:
                    obj = MinPriceCriteria.objects.create(
                        factory=factory, min_price=form.cleaned_data["min_price"]
                    )
                    obj.save()
                else:
                    obj = queryset[0]
                    obj.min_price = form.cleaned_data["min_price"]
                    obj.save()
                    form.save()
            else:
                messages.error(request, _("Invalid form") + str(form.errors))

        context["schedule"] = self.get_schedule(factory)
        return render(request, "factory_schedule.html", context)


def datetime_to_chartjs_format(dt, tz):
    return str(dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"))


import pytz
from django.http import JsonResponse


class FactoryProductionChart(View):
    def get(self, request, *args, **kwargs):
        factory_slug = request.GET.get("factory")
        factory = get_object_or_404(ElectricityFactory, slug=factory_slug)
        num_days = 10
        production = ElectricityFactoryProduction.objects.filter(
            factory=factory
        ).order_by("-start_interval")[: 24 * num_days]
        x = []
        y1 = []
        y2 = []
        prices = ElectricityPrice.objects.filter(plan=factory.plan)
        display_currency = factory.currency
        tz = factory.get_pytz_timezone()
        x_scale = tz.zone + " timezone"
        x_min = None
        if len(production) > 0:
            x_max = datetime_to_chartjs_format(production[0].end_interval, tz)
        else:
            x_max = None

        min_price = MinPriceCriteria.objects.filter(factory=factory).first()
        if min_price is not None:
            y1_backgroundColor = []
            min_price_in_display_currency = Decimal(
                convert_money(min_price.min_price, display_currency).amount
            )
        else:
            min_price_in_display_currency = None
            y1_backgroundColor = "rgba(255, 99, 132, 0.2)"

        for p in production:
            x.append(datetime_to_chartjs_format(p.start_interval, tz))
            y1.append(Decimal(p.energy_in_kwh) * Decimal("0.001"))

            p2 = prices.filter(start_interval=p.start_interval)
            if len(p2) > 0:
                p0 = Decimal(convert_money(p2[0].price, display_currency).amount)
                y2.append(p0)
                if (
                    min_price_in_display_currency is not None
                    and p0 > min_price_in_display_currency
                ):
                    color = ("rgba(54, 162, 235, 0.5)",)
                else:
                    color = "rgba(255, 45, 33, 0.2)"
            else:
                color = "rgba(54, 162, 235, 0.5)"
                y2.append(None)
            if min_price is not None:
                y1_backgroundColor.append(color)
        if len(production) > 0:
            x_min = datetime_to_chartjs_format(p.start_interval, tz=tz)
        else:
            x_min = None
        y1 = y1[::-1]
        y1_backgroundColor = y1_backgroundColor[::-1]
        y2 = y2[::-1]
        x = x[::-1]
        # y1.append(y1[-1])
        if len(y2) > 0:
            y2.append(y2[-1])
            x.append(x_max)
        y_scale = "MWh"
        y1_label = factory.name + " " + _("production")
        y2_label = factory.plan.name
        y1_scale_label = "MWh"
        y2_scale_label = factory.plan.electricity_unit + "/" + display_currency
        # y1_backgroundColor = [
        #                         'rgba(255, 99, 132, 0.2)',
        #                         'rgba(255, 159, 64, 0.2)',
        #                         'rgba(255, 205, 86, 0.2)',
        #                         'rgba(75, 192, 192, 0.2)',

        #                         'rgba(54, 162, 235, 0.2)',
        #                         'rgba(153, 102, 255, 0.2)',
        #                         'rgba(201, 203, 207, 0.2)',
        #                         'rgba(255, 99, 132, 0.2)',

        #                         'rgba(255, 159, 64, 0.2)',
        #                         'rgba(255, 205, 86, 0.2)',
        #                         'rgba(75, 192, 192, 0.2)',
        #                         'rgba(54, 162, 235, 0.2)',

        #                         'rgba(153, 102, 255, 0.2)',
        #                         'rgba(201, 203, 207, 0.2)',
        #                         'rgba(255, 99, 132, 0.2)',
        #                         'rgba(255, 159, 64, 0.2)',

        #                         'rgba(255, 205, 86, 0.2)',
        #                         'rgba(75, 192, 192, 0.2)',
        #                         'rgba(54, 162, 235, 0.2)',
        #                         'rgba(153, 102, 255, 0.2)',

        #                         'rgba(201, 203, 207, 0.2)',
        #                         'rgba(201, 203, 207, 0.2)',
        #                         'rgba(201, 203, 207, 0.2)',
        #                         'rgba(201, 203, 207, 0.2)',
        #                     ]
        return JsonResponse(
            data={
                "x_values": x,
                "y1_values": y1,
                "y1_backgroundColor": y1_backgroundColor,  #'rgba(255, 99, 132, 0.7)',
                "y2_values": y2,
                "y1_label": y1_label,
                "y2_label": y2_label,
                "y1_scale_label": y1_scale_label,
                "y2_scale_label": y2_scale_label,
                "x_scale": x_scale,
                "x_min": x_min,
                "x_max": x_max,
            }
        )
