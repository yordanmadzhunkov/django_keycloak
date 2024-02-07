from . import common_context
from vei_platform.models.factory import ElectricityFactory, FactoryProductionPlan, ElectricityWorkingHoursPerMonth
from vei_platform.models.finance_modeling import Campaign as CampaignModel, InvestementInCampaign
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CreateInvestmentForm, EditInvestmentForm, CampaingEditForm, CampaingReviewForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from decimal import Decimal
from django.utils.translation import gettext as _
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class Campaign(LoginRequiredMixin, View):
    
    login_url = '/oidc/authenticate/'
    
    def get(self, request, pk, *args, **kwargs):
        context = common_context(request)
        campaign = CampaignModel.objects.get(pk=pk)
        self.campaign = campaign
        factory = campaign.factory
        if request.user and request.user.is_authenticated:
            is_reviewer = request.user.is_staff
            if is_reviewer and self.campaign.need_approval():
                return self.get_as_reviewer(request, context)
            is_manager = factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager:
                return self.get_as_manager(request, context)
            else:
                return self.get_as_investor(request, context)
        return self.get_as_anon(request, context)
    
    
    def get_as_investor(self, request, context):
        profile = get_user_profile(request.user)        
        my_investments = InvestementInCampaign.objects.filter(campaign=self.campaign, 
                                                          investor_profile=profile, 
                                                          status=InvestementInCampaign.Status.INTERESTED)
        if len(my_investments) == 0:
            form = CreateInvestmentForm()
        else:
            form = EditInvestmentForm(instance=my_investments[0])

        context['show_form'] = self.campaign.accept_investments()
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors(show_users=False, investor_profile=profile)
        context['card_form'] = form
        return render(request, "campaign.html", context)    
    
    def get_as_manager(self, request, context):
        if self.campaign.accept_investments():
            allow_finish = self.campaign.progress()['percent'] >= Decimal(100)
            form = CampaingEditForm(allow_finish)
            context['form'] = form
        context['show_form'] = self.campaign.accept_investments()
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors(show_users=True)
        return render(request, "campaign.html", context)
    
    def get_as_reviewer(self, request, context):
        if self.campaign.status == CampaignModel.Status.INITIALIZED:
            form = CampaingReviewForm()
            context['form'] = form
        context['show_form'] = True
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        #context['investors'] = self.campaign.get_investors(show_users=True)
        return render(request, "campaign.html", context)
    
    
    def post_as_reviewer(self, request, context):
        if request.method == 'POST':
            if 'cancel' in request.POST:
                self.campaign.status = CampaignModel.Status.CANCELED
                self.campaign.save()
                messages.success(request, _("Campaign is canceled"))

            if 'approve' in request.POST:
                self.campaign.status = CampaignModel.Status.ACTIVE
                self.campaign.save()
                messages.success(request, _("Campaign is activated"))

        return redirect(self.campaign.get_absolute_url())
    
    def post_as_manager(self, request, context):
        if self.campaign.accept_investments():
            allow_finish = self.campaign.progress()['percent'] >= Decimal(100)
            form = CampaingEditForm(allow_finish)
            if request.method == 'POST':
                if 'cancel' in request.POST:
                    form = CampaingEditForm(request.POST)
                    self.campaign.status = CampaignModel.Status.CANCELED
                    self.campaign.save()
                    messages.success(request, _("Campaign is canceled"))

                if 'complete' in request.POST:
                    form = CampaingEditForm(request.POST)
                    if allow_finish:
                        self.campaign.status = CampaignModel.Status.COMPLETED;
                        self.campaign.save()
                        messages.success(request, _("Campaign is completed"))
                    else:
                        messages.error(request, _("Not enough accumulated interest to be able to finish the campaing"))

            context['form'] = form
        context['show_form'] = self.campaign.accept_investments()
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors(show_users=True)
        return render(request, "campaign.html", context)    
    
    def post_as_investor(self, request, context):
        profile = get_user_profile(request.user)        
        my_investments = InvestementInCampaign.objects.filter(campaign=self.campaign, 
                                                            investor_profile=profile, 
                                                            status=InvestementInCampaign.Status.INTERESTED)
        if len(my_investments) == 0:
            form = CreateInvestmentForm()
            if 'invest' in request.POST:
                form = CreateInvestmentForm(request.POST)
                if form.is_valid():
                    amount = form.cleaned_data['amount']
                    investment = InvestementInCampaign(
                                amount= amount,
                                campaign=self.campaign,
                                investor_profile=profile,
                                status=InvestementInCampaign.Status.INTERESTED
                    )
                    investment.save()
                    form = EditInvestmentForm(instance=investment)

                    messages.success(request, _("You declared interest in amount %s to %s") % (amount, self.campaign.factory.name))
                else:
                    messages.error(request, _("Invalid data, please try again"))        
        else:
            form = EditInvestmentForm(instance=my_investments[0])
            if 'cancel' in request.POST:
                my_investments[0].status = InvestementInCampaign.Status.CANCELED
                my_investments[0].save()
                messages.success(request, _("Your interest have been canceled"))
                form = CreateInvestmentForm()

                    
            if 'save' in request.POST:
                form = EditInvestmentForm(request.POST)
                if form.is_valid():
                    my_investments[0].amount = form.cleaned_data['amount']
                    my_investments[0].save()
                    messages.success(request, _("You declared interest in amount changed to %s") % my_investments[0].amount)
                else:
                    messages.error(request, _("Error occured when changing the amount"))

        context['show_form'] = self.campaign.accept_investments()
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors(show_users=False, investor_profile=profile)
        context['form'] = form
        return render(request, "campaign.html", context)    
    
    
    def get_as_anon(self, request, context):
        return render(request, "campaign.html", context)    
    
    def post(self, request, pk, *args, **kwargs):
        context = common_context(request)
        self.campaign = CampaignModel.objects.get(pk=pk)
        if request.user and request.user.is_authenticated:
            is_reviewer = request.user.is_staff
            if is_reviewer and self.campaign.need_approval():
                return self.post_as_reviewer(request, context)
            is_manager = self.campaign.factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager:
                return self.post_as_manager(request, context)
            else:
                return self.post_as_investor(request, context)
        return self.get_as_anon(request, context)    