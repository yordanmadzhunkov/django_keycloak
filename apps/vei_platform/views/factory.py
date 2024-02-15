from django.core.paginator import Paginator

from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth, ElectricityFactoryComponents
from vei_platform.models.finance_modeling import Campaign
from vei_platform.models.finance_modeling import ElectricityPricePlan, Campaign
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CampaignCreateForm, FactoryFinancialPlaningForm, FactoryModelForm, ElectricityFactoryComponentsForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.views import View

from decimal import Decimal, DecimalException
from datetime import date
from django import template
from django.forms import formset_factory
from django.forms.models import model_to_dict

from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from djmoney.money import Money



class FactoriesList(ListView):
    title = _('Electrical factories from renewable sources')
    model = ElectricityFactory
    template_name = 'factories_list.html'
    paginate_by = 5

    def get_queryset(self):
        listed = self.view_offered_factories()
        factories_list = ElectricityFactory.objects.filter(pk__in=listed).order_by('pk')
        return factories_list
    
    def get_context_data(self, **kwargs):
        context = super(FactoriesList, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context['head_title'] = self.title
        return context

    def view_offered_factories(self):
        campaigns = Campaign.objects.filter(status=Campaign.Status.ACTIVE).order_by('factory')
        prev = None
        listed = []
        for l in campaigns:
            if prev != l.factory.pk:
                #print(l.factory.name)
                listed.append(l.factory.pk)
            prev = l.factory.pk
        return listed

class FactoriesForReview(FactoriesList):
    def view_offered_factories(self):
        campaigns = Campaign.objects.filter(status=Campaign.Status.INITIALIZED).order_by('factory')
        
        prev = None
        listed = []
        for l in campaigns:
            if l.get_active(l.factory):
                if prev != l.factory.pk:
                    #print(l.factory.name)
                    listed.append(l.factory.pk)
                prev = l.factory.pk
        return listed


class FactoriesOfUserList(LoginRequiredMixin, FactoriesList):
    
    login_url = '/oidc/authenticate/'#reverse_lazy('oidc_authentication_init')
    title = _('My Factories')
    
    def get_queryset(self):
        return  ElectricityFactory.objects.filter(manager=self.request.user).order_by('pk')

    def get_context_data(self, **kwargs):
        context = super(FactoriesOfUserList, self).get_context_data(**kwargs)
        context['add_button'] = True
        return context


class CampaignCreate(CreateView):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        #factory = ElectricityFactory.objects.get(pk=pk)
        context['factory'] = factory
        context['manager_profile'] = get_user_profile(factory.manager)
        # Check if user is manager
        if context['profile'].pk == context['manager_profile'].pk:
            capacity = factory.get_capacity_in_kw()
            fraction = Decimal(0.5)
            form = CampaignCreateForm(initial={
                'amount_offered': Money(Decimal(1500) * capacity * fraction, currency='BGN'),
                'persent_from_profit': fraction * Decimal(100),
                'start_date': date(2024,12,1),
                'duration': Decimal(15*12),
                'commision': Decimal(1.5),
            })
            context['new_campaign_form'] = form
            context['hide_link_buttons'] = True
        else:
            messages.error(request, _('Only factory manager can initiate campaign'))
            return redirect(factory.get_absolute_url())
        return render(request, "campaign_create.html", context)

    def post(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = get_object_or_404(ElectricityFactory, pk=pk)
        form = CampaignCreateForm(data=request.POST)
        if form.is_valid():
            context['form_data'] = form.cleaned_data
            amount = form.cleaned_data['amount_offered']
            persent_from_profit = form.cleaned_data['persent_from_profit']
            start_date = form.cleaned_data['start_date']
            duration = form.cleaned_data['duration']
            commision = form.cleaned_data['commision']
            campaign = Campaign(
                    start_date=start_date, 
                    amount=amount, 
                    persent_from_profit=Decimal(persent_from_profit).quantize(Decimal('99.99')),
                    duration=Decimal(duration).quantize(Decimal('1.')), 
                    commision=Decimal(commision).quantize(Decimal('99.99')),
                    factory=factory
            )
            campaign.save()
            messages.success(request, _('You have successfully started a campaign to collect investors until %s')  
                             % (start_date))
            return redirect(campaign.get_absolute_url())
        else:
            messages.error(request, _('Invalid data, please try again'))

        context['factory'] = factory
        context['new_campaign_form'] = form
        context['hide_link_buttons'] = True
        return render(request, "campaign_create.html", context)


#@login_required(login_url='/oidc/authenticate/')
class FactoryDetail(View):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        factory = ElectricityFactory.objects.get(pk=pk)
        context['factory'] = factory
        
        campaigns = Campaign.objects.filter(factory=factory).exclude(status=Campaign.Status.CANCELED)
        context['campaigns'] = campaigns
        
        components = ElectricityFactoryComponents.objects.filter(factory=factory)
        context['components'] = components

        
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


def extract_error_messages_from(request, formset):
    for f in formset:
        if not f.is_valid():
            if 'docfile' in f.errors.keys():
                s = str(f.errors['docfile']) 
                if s.find('Filetype not supported') > 0:
                    messages.error(request, "Грешен тип на прикачения файл")
                elif s.find('Please keep filesize under') > 0:
                    messages.error(request, "Прикачения файл е прекаленно голям")
                else:
                    messages.error(request, "Файлът го няма - изчезнал е")


class FactoryEdit(UpdateView):
    model = ElectricityFactory
    template_name = 'factory_components.html'
    form_class = FactoryModelForm
    success_url = None
    formset_fields = ['component_type', 'power_in_kw', 'count', 'docfile', 'name', 'description']

    
    def get_context_data(self, **kwargs):
        context = super(FactoryEdit, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context['factory'] = self.object
        if self.request.POST:
            form = FactoryModelForm(self.request.POST, instance=self.object)
            context['form'] = form
            FactoryComponentsFormSet = inlineformset_factory(           
                ElectricityFactory, 
                ElectricityFactoryComponents, 
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields, 
                can_delete=True
                )
            context['formset'] = FactoryComponentsFormSet(data=self.request.POST, 
                                                          files=self.request.FILES,
                                                          instance=self.object)
            
        else:
            context['form'] = FactoryModelForm(instance=self.object)
            FactoryComponentsFormSet = inlineformset_factory(           
                ElectricityFactory, 
                ElectricityFactoryComponents, 
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields, 
                extra=2, can_delete=True
                )
            context['formset'] = FactoryComponentsFormSet(instance=self.object)
        for f in context['formset']:
            formset_helper = f.helper
            context['formset_helper'] = formset_helper
            #print(formset_helper)
            break
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        for component_form in formset:
            if component_form.is_valid():
                d = component_form.cleaned_data
                # DELETE HARD
                do_delete = 'DELETE' in d.keys() and d['DELETE']
                if 'id' in d.keys():
                    id = d['id']
                    if id is not None and do_delete:
                        id.delete()
                    else:
                        component_form.save()

        extract_error_messages_from(self.request, formset)
        return super(FactoryEdit, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('view_factory', kwargs={'pk': self.object.pk})


class FactoryCreate(CreateView):
    model = ElectricityFactory
    template_name = 'factory_create.html'
    form_class = FactoryModelForm
    success_url = None
    formset_fields = ['component_type', 'name', 'power_in_kw', 'count', 'docfile', 'description']

    def get_context_data(self, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')

        context = super(FactoryCreate, self).get_context_data(**kwargs)
        context.update(common_context(self.request))
        context['factory'] = self.object
        if self.request.POST:
            form = FactoryModelForm(data=self.request.POST, 
                                    files=self.request.FILES, 
                                    instance=self.object)
            context['form'] = form
        else:
            context['form'] = FactoryModelForm(instance=self.object)
            FactoryComponentsFormSet = inlineformset_factory(           
                ElectricityFactory, 
                ElectricityFactoryComponents, 
                form=ElectricityFactoryComponentsForm,
                fields=self.formset_fields, 
                extra=2, can_delete=True
                )
            context['formset'] = FactoryComponentsFormSet(instance=self.object)
        return context


    def form_valid(self, form):
        created_factory = form.save(commit=True)
        created_factory.manager = self.request.user
        created_factory.save()
        messages.success(self.request, _('Electrical factory added'))

        FactoryComponentsFormSet = inlineformset_factory(           
                ElectricityFactory, 
                ElectricityFactoryComponents, 
                form=ElectricityFactoryComponentsForm,
                fields=self.fields, 
                can_delete=True
                )
        formset = FactoryComponentsFormSet(data=self.request.POST, 
                                           files=self.request.FILES, 
                                           instance=created_factory)
        if formset.is_valid():
            formset.save()
        extract_error_messages_from(self.request, formset)
        return super(FactoryCreate, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Invalid data, please try again'))
        return super(FactoryCreate).form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('view_factory', kwargs={'pk': self.object.pk})

