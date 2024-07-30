from django.db import models
from django.conf import settings

# Create your models here.
from decimal import Decimal
from datetime import date, datetime
from .factory import ElectricityFactory, FactoryProductionPlan
from .profile import UserProfile

from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from djmoney.models.fields import MoneyField
from djmoney.money import Money

from uuid import uuid4, UUID

import re


class Campaign(models.Model):
    class Status(models.TextChoices):
        INITIALIZED = "UN", _("Under review")
        ACTIVE = "Ac", _("Active")
        CANCELED = "CA", _("Canceled")
        COMPLETED = "CO", _("Completed")

    start_date = models.DateField()
    amount = MoneyField(
        max_digits=16, decimal_places=2, default=Decimal(0), default_currency="BGN"
    )

    persent_from_profit = models.DecimalField(max_digits=4, decimal_places=2)
    duration = models.IntegerField(default=12 * 15)
    commision = models.DecimalField(default=1.5, max_digits=4, decimal_places=2)
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING
    )
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.INITIALIZED,
    )

    def price_per_kw(self):
        capacity = self.factory.get_capacity_in_kw()
        if capacity < Decimal(0.001):
            return _("Not available")

        v = self.amount.amount
        return Money(
            Decimal(
                v / (capacity * self.persent_from_profit * Decimal("0.01"))
            ).quantize(Decimal("1.00")),
            self.amount.currency,
        )

    @staticmethod
    def get_last_campaign(factory):
        campaigns = Campaign.objects.filter(factory=factory).order_by("pk")
        if len(campaigns) > 0:
            return campaigns[len(campaigns) - 1]
        return None

    def allow_start_new_campaign(self, when=datetime.now()):
        last_campaign = Campaign.get_last_campaign(self.factory)
        return (
            not last_campaign
            or last_campaign.is_expired(when)
            or last_campaign.status == Campaign.Status.CANCELED
        )

    def progress(self):
        t = Money(0, self.amount.currency)
        for investment in self.get_investors():
            t = t + investment.amount
        res = {}
        res["total"] = t
        r = Decimal(100) * (t / self.amount)
        if r > Decimal(100):
            r = Decimal(100)
        res["percent"] = r.quantize(Decimal("1"))
        res["available"] = self.amount - t
        return res

    def allow_finish(self):
        if self.status != Campaign.Status.ACTIVE:
            return False
        t = Money(0, self.amount.currency)
        for investment in self.get_investors():
            t = t + investment.amount
        return t >= self.amount

    def allow_extend(self, when=datetime.now()):
        if self.is_expired(when):
            last_campaign = Campaign.get_last_campaign(self.factory)
            if last_campaign == self:
                return (
                    self.status != Campaign.Status.CANCELED
                    and self.status != Campaign.Status.COMPLETED
                )
        return False

    def allow_cancel(self, when=datetime.now()):
        return (
            not self.is_expired(when)
            and self.status != Campaign.Status.CANCELED
            and self.status != Campaign.Status.COMPLETED
        )

    def count_investitors(self):
        return InvestementInCampaign.objects.filter(campaign=self, status="IN").count()

    def get_absolute_url(self):
        return reverse("campaign", kwargs={"pk": self.pk})

    def show_in_dashboard(self):
        return self.status != Campaign.Status.CANCELED

    def need_approval(self):
        return self.status == Campaign.Status.INITIALIZED

    def is_expired(self, when=datetime.now()):
        return when >= datetime(
            year=self.start_date.year,
            month=self.start_date.month,
            day=self.start_date.day,
            hour=8,
            minute=0,
            second=0,
        )

    def status_str(self, when=datetime.now()):
        if self.status == Campaign.Status.COMPLETED:
            return _("Completed")
        if self.is_expired(when):
            return _("Expired")
        if self.status == Campaign.Status.INITIALIZED:
            return _("Started")
        if self.status == Campaign.Status.ACTIVE:
            return _("Active")
        if self.status == Campaign.Status.CANCELED:
            return _("Canceled")

        return _("Unknown")

    def accept_investments(self, when=datetime.now()):
        return not self.is_expired(when) and self.status == Campaign.Status.ACTIVE

    def get_investors(self):
        return InvestementInCampaign.objects.filter(campaign=self).exclude(
            status=InvestementInCampaign.Status.CANCELED
        )

    def get_investors_for_view(self, show_users, investor_profile=None):
        investors = self.get_investors()
        res = []
        count = 1
        for investor in investors:
            show = show_users or investor.investor_profile == investor_profile
            res.append(
                {
                    "status": investor.status_str(),
                    "amount": investor.amount,
                    "user_profile": (
                        (_("Investor %d") % count)
                        if not show
                        else investor.investor_profile.get_display_name()
                    ),
                    "user_profile_link": (
                        "" if not show else investor.investor_profile.get_href()
                    ),
                    "user_profile_avatar": (
                        "/static/img/undraw_profile.svg"
                        if not show
                        else investor.investor_profile.get_avatar_url()
                    ),
                }
            )
            count = count + 1
        return res


class InvestementInCampaign(models.Model):
    class Status(models.TextChoices):
        INTERESTED = "IN", _("Interested")
        CANCELED = "CA", _("Canceled")
        COMPLETED = "CO", _("Completed")

    # name = models.CharField(max_length=128)
    investor_profile = models.ForeignKey(
        UserProfile, null=False, blank=False, on_delete=models.DO_NOTHING
    )
    campaign = models.ForeignKey(
        Campaign, null=True, blank=True, default=None, on_delete=models.DO_NOTHING
    )
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="BGN", default=Decimal(10000)
    )

    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.INTERESTED,
    )

    def share_from_factory(self):
        return (
            (self.amount * self.campaign.persent_from_profit) / self.campaign.amount
        ).quantize(Decimal(".01"))

    def status_with_css_class(self):
        if self.campaign.accept_investments():
            if self.status == InvestementInCampaign.Status.INTERESTED:
                return (_("Claimed interest"), "text-dark")
            if self.status == InvestementInCampaign.Status.CANCELED:
                return (_("Canceled"), "text-error")
            if self.status == InvestementInCampaign.Status.COMPLETED:
                return (_("Completed"), "text-success")
        else:
            if self.campaign.status == Campaign.Status.COMPLETED:
                return (_("Expecting deposit"), "text-success")
            else:
                return (_("Campaign expired"), "text-muted")
        return (_("Unknown"), "text-error")

    def status_str(self):
        status, css_class = self.status_with_css_class()
        return status

    def status_css_class(self):
        status, css_class = self.status_with_css_class()
        return css_class

    def show_in_dashboard(self):
        return self.status != InvestementInCampaign.Status.CANCELED
