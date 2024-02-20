from . import common_context
from vei_platform.models.campaign import Campaign as CampaignModel, InvestementInCampaign
from vei_platform.models.profile import get_user_profile
from vei_platform.forms import CreateInvestmentForm, EditInvestmentForm, CampaingEditForm, LoiginOrRegisterForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from datetime import datetime

from decimal import Decimal
from django.utils.translation import gettext as _
from django.views import View
from djmoney.money import Money

class Campaign(View):
   
    def get(self, request, pk, *args, **kwargs):
        context = common_context(request)
        campaign = CampaignModel.objects.get(pk=pk)
        self.campaign = campaign
        factory = campaign.factory
        if request.user and request.user.is_authenticated:
            is_reviewer = request.user.is_staff
            is_manager = factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager or is_reviewer:
                return self.get_as_manager_or_reviewer(request, context, is_reviewer=is_reviewer)
            else:
                return self.get_as_investor(request, context)
        return self.get_as_anon(request, context)

    def get_as_anon(self, request, context):
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors_for_view(show_users=False)
        context['hide_link_buttons'] = True
        context['card_form'] = LoiginOrRegisterForm()
        return render(request, "campaign.html", context)        
    
    def get_as_investor(self, request, context):
        profile = get_user_profile(request.user)        
        my_investments = InvestementInCampaign.objects.filter(campaign=self.campaign, 
                                                          investor_profile=profile, 
                                                          status=InvestementInCampaign.Status.INTERESTED)
        if self.campaign.accept_investments():
            if len(my_investments) == 0:
                context['card_form'] = CreateInvestmentForm(initial={'amount': Money(Decimal('1000'), self.campaign.amount.currency)})
            else:
                context['card_form'] = EditInvestmentForm(instance=my_investments[0])

        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors_for_view(show_users=False, investor_profile=profile)
        context['hide_link_buttons'] = True
        return render(request, "campaign.html", context)    
    
    def get_as_manager_or_reviewer(self, request, context, is_reviewer):
        context['card_form'] = CampaingEditForm(instance=self.campaign, is_reviewer=is_reviewer)
        context['factory'] = self.campaign.factory
        context['campaign'] = self.campaign
        context['investors'] = self.campaign.get_investors_for_view(show_users=True)
        context['hide_link_buttons'] = True
        return render(request, "campaign.html", context)
    

    def post_as_manager_or_reviewer(self, request, context, is_reviewer):
        if request.method == 'POST':
            if 'cancel' in request.POST:
                self.campaign.status = CampaignModel.Status.CANCELED
                self.campaign.save()
                messages.success(request, _("Campaign is canceled"))

            if 'approve' in request.POST:
                if is_reviewer:
                    self.campaign.status = CampaignModel.Status.ACTIVE
                    self.campaign.save()
                    messages.success(request, _("Campaign is activated"))
                else:
                    messages.error(request, _("Only staff can approve a campaign"))

            if 'extend' in request.POST:
                form = CampaingEditForm(data=request.POST, instance=self.campaign,)
                if form.is_valid():
                    next_deadline = form.cleaned_data['start_date']
                    if next_deadline > self.campaign.start_date:
                        self.campaign.start_date = next_deadline
                        self.campaign.save()
                        messages.success(request, _("Campaign deadline extended to %s" % (next_deadline)))
                    else:
                        messages.error(request, _("Campaign deadline should be further in the future"))


            if 'complete' in request.POST:
                if self.campaign.allow_finish():
                    self.campaign.status = CampaignModel.Status.COMPLETED;
                    self.campaign.save()
                    messages.success(request, _("Campaign is completed"))
                else:
                    messages.error(request, _("Not enough accumulated interest to be able to finish the campaing"))
        
        return redirect(self.campaign.get_absolute_url())
    
            
    
    def post_as_investor(self, request, context):
        profile = get_user_profile(request.user)        
        my_investments = InvestementInCampaign.objects.filter(campaign=self.campaign, 
                                                            investor_profile=profile, 
                                                            status=InvestementInCampaign.Status.INTERESTED)
        if len(my_investments) == 0:
            form = CreateInvestmentForm(initial={'amount': Money(Decimal('1000'), self.campaign.amount.currency)})
            if 'invest' in request.POST:
                form = CreateInvestmentForm(request.POST)
                if form.is_valid():
                    amount = form.cleaned_data['amount']
                    if amount.currency == self.campaign.amount.currency:
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
                        messages.error(request, _("Currency conversion from %s to %s is not supported" % (amount.currency, self.campaign.amount.currency)))
                else:
                    messages.error(request, _("Invalid data, please try again"))        
        else:
            form = EditInvestmentForm(instance=my_investments[0])
            if 'cancel' in request.POST:
                my_investments[0].status = InvestementInCampaign.Status.CANCELED
                my_investments[0].save()
                messages.success(request, _("Your interest have been canceled"))
                form = CreateInvestmentForm(initial={'amount': Money(Decimal('1000'), self.campaign.amount.currency)})

                    
            if 'save' in request.POST:
                form = EditInvestmentForm(request.POST)
                if form.is_valid():
                    amount = form.cleaned_data['amount']
                    if amount.currency == self.campaign.amount.currency:
                        my_investments[0].amount = form.cleaned_data['amount']
                        my_investments[0].save()
                        messages.success(request, _("You declared interest in amount changed to %s") % my_investments[0].amount)
                    else:
                        messages.error(request, _("Currency conversion from %s to %s is not supported") % (amount.currency, self.campaign.amount.currency))

                else:
                    messages.error(request, _("Error occured when changing the amount"))
        return redirect(self.campaign.get_absolute_url())

    def post_as_anon(self, request, context):
        return redirect('oidc_authentication_init')
    
    def post(self, request, pk, *args, **kwargs):
        context = common_context(request)
        self.campaign = CampaignModel.objects.get(pk=pk)
        if request.user and request.user.is_authenticated:
            is_reviewer = request.user.is_staff
            is_manager = self.campaign.factory.get_manager_profile() == get_user_profile(request.user)
            if is_manager or is_reviewer:
                return self.post_as_manager_or_reviewer(request, context, is_reviewer)
            else:
                return self.post_as_investor(request, context)
        return self.post_as_anon(request, context)    