from django.db import models
from django.conf import settings
# Create your models here.
from decimal import Decimal
from datetime import date, datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from .factory import ElectricityFactory, FactoryProductionPlan
from .legal import LegalEntity
from .profile import UserProfile

from django.utils.translation import gettext_lazy as _

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task

from djmoney.models.fields import MoneyField
from djmoney.money import Money

from uuid import uuid4, UUID

import re
    
# Financial data related to the platform
# Evealuation, P/E, available for investment, number of investors

class ElectricityPricePlan(models.Model):
    name = models.CharField(max_length=128)

    start_year = models.IntegerField(
        default=2022,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )
    end_year = models.IntegerField(
        default=2025,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )

    def __str__(self) -> str:
        return self.name

    def get_price(self, month):
        prices = ElectricityPrice.objects.filter(
            plan=self).order_by('-month')
        if len(prices) > 0:
            for price in prices:
                if price.month <= month:
                    return price.number
            price = prices[len(prices)-1]
            return price.number
        return Decimal(0)

    def get_absolute_url(self):
        return "/electricity/%s" % self.pk


class ElectricityPrice(models.Model):
    month = models.DateField()
    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='BGN',
        default=Decimal(0)
    )

    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return "%s @ %.2f - plan = %s" % (str(self.month), self.number,  self.plan.name)





class Campaign(models.Model):
    class Status(models.TextChoices):
        INITIALIZED = 'UN', _('Under review')
        ACTIVE = 'Ac', _('Active')
        CANCELED = 'CA', _('Canceled')
        COMPLETED = 'CO', _('Completed')
        TIMEOUT = 'To', _('Timeout')

    start_date = models.DateField()
    amount = MoneyField(max_digits=16, decimal_places=2, default=Decimal(0), default_currency='BGN')
    persent_from_profit = models.DecimalField(max_digits=4, decimal_places=2)
    duration = models.IntegerField(default=12*15)
    commision = models.DecimalField(
        default=1.5, max_digits=4, decimal_places=2)
    factory = models.ForeignKey(ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.INITIALIZED,
    )
    def price_per_kw(self):
        v = self.amount.amount
        return Money(
            Decimal(v / (self.factory.get_capacity_in_kw() * self.persent_from_profit * Decimal('0.01'))).quantize(Decimal('1.00')),
            self.amount.currency)
        
    @staticmethod
    def is_listed(factory):
        return Campaign.get_active(factory) != None
    
    @staticmethod
    def get_active(factory, when=datetime.now()):
        campaigns = Campaign.objects.filter(factory=factory)
        for c in campaigns:
            time_ok = when < datetime(year=c.start_date.year,
                          month=c.start_date.month,
                          day=c.start_date.day,
                          hour=8, minute=0, second=0)
            status_ok = c.status == Campaign.Status.ACTIVE or c.status == Campaign.Status.INITIALIZED
            if time_ok and status_ok:
                return c
        return None
    
    @staticmethod
    def get_last_completed(factory):
        campaigns = Campaign.objects.filter(factory=factory, status=Campaign.Status.COMPLETED).order_by('start_date')
        if len(campaigns) > 0:
            return campaigns[len(campaigns) - 1]
        return None
   

    def progress(self):
        investments = InvestementInCampaign.objects.filter(campaign=self, status='IN')
        t = Money(0, 'BGN')
        for invest in investments:
            t = t + invest.amount
        res = {}
        res['total'] = t
        r = Decimal(100) * (t / self.amount)
        if r > Decimal(100):
            r = Decimal(100)
        res['percent'] = r.quantize(Decimal('1')) 
        res['available'] = self.amount - t
        return res
    
    def count_investitors(self):
        return InvestementInCampaign.objects.filter(campaign=self, status='IN').count()

    def get_absolute_url(self):
        return "/campaign/%s" % self.pk       

    def show_in_dashboard(self):
        return self.status != Campaign.Status.CANCELED 
    
    def status_str(self, when=datetime.now()):
        if when < datetime(year=self.start_date.year,
                          month=self.start_date.month,
                          day=self.start_date.day,
                          hour=8, minute=0, second=0):
            if self.status == Campaign.Status.INITIALIZED:
                return _('Started')
                
            if self.status == Campaign.Status.ACTIVE:
                return _('Active')
            if self.status == Campaign.Status.CANCELED:
                return _('Canceled')
            if self.status == Campaign.Status.COMPLETED:
                return _('Completed')
        return _('Expired')

    def accept_investments(self, when=datetime.now()):
        if when < datetime(year=self.start_date.year,
                          month=self.start_date.month,
                          day=self.start_date.day,
                          hour=8, minute=0, second=0):
            
            if self.status == Campaign.Status.INITIALIZED:
                return True
            if self.status == Campaign.Status.ACTIVE:
                return True
        return False
    
    def get_investors(self, show_users, investor_profile = None):
        investors = InvestementInCampaign.objects.filter(campaign=self).exclude(status=InvestementInCampaign.Status.CANCELED)
        res = []
        count = 1
        for investor in investors:
            show = show_users or investor.investor_profile == investor_profile
            res.append({
                'status': investor.status_str(),
                'amount': investor.amount,
                'user_profile': (_("Investor %d") % count) if not show else investor.investor_profile.get_display_name(),
                'user_profile_link': '' if not show else investor.investor_profile.get_href(),
                'user_profile_avatar': '/static/img/undraw_profile.svg' if not show else investor.investor_profile.get_avatar_url(),
            })
            count = count + 1
        return res

        
        
    

class InvestementInCampaign(models.Model):
    class Status(models.TextChoices):
        INTERESTED = 'IN', _('Interested')
        CANCELED = 'CA', _('Canceled')
        COMPLETED = 'CO', _('Completed')
        
    #name = models.CharField(max_length=128)
    investor_profile = models.ForeignKey(UserProfile, null=False, blank=False, on_delete=models.DO_NOTHING)
    campaign = models.ForeignKey(
        Campaign, null=True, blank=True, default=None, on_delete=models.DO_NOTHING)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='BGN',
        default=Decimal(10000)
    )

    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.INTERESTED,
    )
    
    def share_from_factory(self):
        return ((self.amount * self.campaign.persent_from_profit)/ self.campaign.amount).quantize(Decimal('.01'))
    
    
    def status_with_css_class(self):
        if self.campaign.accept_investments():
            if self.status == InvestementInCampaign.Status.INTERESTED:
                return (_('Claimed interest'), 'text-dark')
            if self.status == InvestementInCampaign.Status.CANCELED:
                return (_('Canceled'), 'text-error')
            if self.status == InvestementInCampaign.Status.COMPLETED:
                return (_('Completed'), 'text-success')
        else:
            if self.campaign.status == Campaign.Status.COMPLETED:
                return (_('Expecting deposit'), 'text-success')
            else:
                return (_('Campaign expired'), 'text-muted')
        return (_('Unknown'), 'text-error')
    
    def status_str(self):
        status, css_class = self.status_with_css_class()
        return status

    def status_css_class(self):
        status, css_class = self.status_with_css_class()
        return css_class
    
    def show_in_dashboard(self):
        return self.status != InvestementInCampaign.Status.CANCELED
   