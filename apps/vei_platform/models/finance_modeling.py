from django.db import models
from django.conf import settings
# Create your models here.
from decimal import Decimal
from datetime import date, datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from .factory import ElectricityFactory, FactoryProductionPlan
from .legal import LegalEntity
from .profile import UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_q.tasks import async_task

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
    number = models.DecimalField(max_digits=6, decimal_places=2)
    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return "%s @ %.2f - plan = %s" % (str(self.month), self.number,  self.plan.name)


class Currency(models.TextChoices):
    BGN = 'BGN', ('Bulgarian lev')
    EUR = 'EUR', ('Euro')
    USD = 'USD', ('Unated States Dolar')



class BankAccount(models.Model):
    class AccountStatus(models.TextChoices):
        UNVERIFIED = 'UN', ('Unverified')
        INACTIVE = 'IN', ('Inactive')
        ACTIVE = 'AC', ('Active')

    owner = models.ForeignKey(LegalEntity, null=True, blank=True, on_delete=models.DO_NOTHING)
    iban = models.TextField(max_length=100, null=False, blank=False)
    balance = models.DecimalField(max_digits=24, decimal_places=2, default=Decimal(0))
    initial_balance = models.DecimalField(max_digits=24, decimal_places=2, default=Decimal(0))
    currency = models.CharField(
        max_length=4,
        choices=Currency.choices,
        default=Currency.BGN,
    )
    status = models.CharField(
        max_length=2,
        choices=AccountStatus.choices,
        default=AccountStatus.UNVERIFIED,
    )

    def __str__(self) -> str:
        return "%s / %s" % (self.iban, self.owner.native_name)
    
    def actions(self):
        actions = []
        if self.status == BankAccount.AccountStatus.UNVERIFIED:
            actions.append({'url': '/bank_accounts/verify/%s' % self.pk, 'value': 'Verify', 'method': 'POST'})
        elif self.status == BankAccount.AccountStatus.ACTIVE:
            actions.append({'url': '/bank_accounts/deposit/%s' % self.pk, 'value': 'Deposit', 'method': 'GET'})
            actions.append({'url': '/bank_accounts/withdraw/%s' % self.pk, 'value': 'Withdraw', 'method': 'GET'})
        return actions

    def badge(self):
        if self.status == BankAccount.AccountStatus.ACTIVE:
            return 'badge-success'
        if self.status == BankAccount.AccountStatus.UNVERIFIED:
            return 'badge-warning'
        #if self.status == BankAccount.AccountStatus.INACTIVE:
        return 'badge-error'
    
    def status_str(self):
        if self.status == BankAccount.AccountStatus.ACTIVE:
            return 'Active'
        if self.status == BankAccount.AccountStatus.UNVERIFIED:
            return 'Unverified'
        if self.status == BankAccount.AccountStatus.INACTIVE:
            return 'Inactive'
        return 'Unknown'

    
class BankTransaction(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2,
                                 max_digits=20,
                                 default=0.00,
                                 verbose_name=('Amount'),
                                 help_text=('Account of the transaction.'),
                                 )
    fee = models.DecimalField(decimal_places=2,
                                 max_digits=20,
                                 default=0.00,
                                 verbose_name=('Fee'),
                                 help_text=('Fee assosiated with the transaction.'),
                                 )
    other_account_iban = models.TextField(max_length=100, null=True, blank=True, default='')
    occured_at = models.DateTimeField(blank=False, null=False)
    #created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=256,
                                   null=False,
                                   blank=True,
                                   verbose_name=('Tx Description'),
                                   help_text=('A description to be included with this individual transaction'))
    

    def __str__(self) -> str:
        return "%s %s %s->%s %s" % (self.occured_at, self.amount, self.account.iban, self.other_account_iban, self.description)
        


class BankLoan(models.Model):
    start_date = models.DateField()
    amount = models.DecimalField(
        default=10000, max_digits=12, decimal_places=2)
    duration = models.IntegerField(default=12*15)
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return "%.0f start %s months=%d" % (self.amount, self.start_date.strftime('%b %y'), self.duration)

    def get_absolute_url(self):
        return "/bank_loan/%s" % self.pk

    def start_year(self):
        return self.start_date.year

    def end_year(self):
        return self.start_date.year + ((self.duration + self.start_date.month - 1) // 12)

    def get_interest(self, date):
        interests = BankLoanInterest.objects.filter(
            loan=self).order_by('-month')
        if len(interests) > 0:
            for interest in interests:
                if interest.month <= date:
                    return interest.number
            interest = interests[len(interests)-1]
            return interest.number
        return Decimal(5)

    def calculate_payment_amount(self, principal, interest_rate, period):
        x = (Decimal(1) + interest_rate) ** period
        return principal * (interest_rate * x) / (x - 1)

    def adjust_mountly_interest(self, yearly_interest):
        return (Decimal(1.0) + yearly_interest/Decimal(100))**Decimal(1.0/12) - Decimal(1.0)

    def offset_date_by_period(self, date1, period):
        dy = (period + date1.month - 1) // 12
        m = (period + date1.month - 1) % 12 + 1
        return date(year=date1.year + dy, month=m, day=date1.day)

    def offset_start_date(self, months):
        return self.offset_date_by_period(self.start_date, period=months)

    def amortization_schedule(self):
        # (index, payment, payment_interest, payment_principal, balance)
        # (0, Decimal('855.57'), Decimal('40.74'), Decimal('814.83'), Decimal('9185.17'))
        amortization_schedule = []
        balance = self.amount
        for number in range(self.duration):
            remaining_period = self.duration - number
            p = self.offset_date_by_period(self.start_date, number)
            interest_rate = self.get_interest(p)
            montly_interest = self.adjust_mountly_interest(interest_rate)
            payment = self.calculate_payment_amount(
                principal=balance,
                interest_rate=montly_interest,
                period=remaining_period,
            )
            payment = round(payment, 2)
            interest = round(balance * montly_interest, 2)
            if payment > interest + balance:
                payment = interest + balance
            principal = payment - interest
            balance = balance - principal
            row = (number, payment, interest, principal, balance)
            amortization_schedule.append(row)
            if balance == Decimal(0):
                break
        return amortization_schedule

    def total_amortization(self):
        total_payment = Decimal(0)
        total_interest = Decimal(0)
        total_principal = Decimal(0)
        for row in self.amortization_schedule():
            number, payment, interest, principal, balance = row
            total_payment = total_payment + payment
            total_interest = total_interest + interest
            total_principal = total_principal + principal
        return total_payment, total_interest, total_principal


class BankLoanInterest(models.Model):
    month = models.DateField()
    number = models.DecimalField(max_digits=6, decimal_places=2)
    loan = models.ForeignKey(BankLoan, on_delete=models.CASCADE)


class Campaign(models.Model):
    class Status(models.TextChoices):
        INITIALIZED = 'UN', ('Under review')
        ACTIVE = 'Ac', ('Active')
        CANCELED = 'CA', ('Canceled')
        COMPLETED = 'CO', ('Completed')
        TIMEOUT = 'To', ('Timeout')

    start_date = models.DateField()
    amount = models.DecimalField(max_digits=16, decimal_places=2)
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
        return Decimal(self.amount / (self.factory.get_capacity_in_kw() * self.persent_from_profit * Decimal('0.01'))).quantize(Decimal('1.00'))
        
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

    def progress(self):
        total = InvestementInCampaign.objects.filter(campaign=self, status='IN').aggregate(total=models.Sum(models.F('amount')))
        if total['total'] is None:
            total['total'] = Decimal(0)
        r = Decimal(100) * (total['total'] / self.amount)
        if r > Decimal(100):
            r = Decimal(100)
        total['percent'] = r.quantize(Decimal('1')) 
        return total
    
    def count_investitors(self):
        return InvestementInCampaign.objects.filter(campaign=self, status='IN').count()

    def get_absolute_url(self):
        return "/campaign/%s" % self.pk        
    
    def status_str(self, when=datetime.now()):
        if when < datetime(year=self.start_date.year,
                          month=self.start_date.month,
                          day=self.start_date.day,
                          hour=8, minute=0, second=0):
            if self.status == Campaign.Status.INITIALIZED:
                return 'Стартирана'
            if self.status == Campaign.Status.ACTIVE:
                return 'Активена'
            if self.status == Campaign.Status.CANCELED:
                return 'Отменена'
            if self.status == Campaign.Status.COMPLETED:
                return 'Приключила'
        return 'Изтекла'

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
        investors = InvestementInCampaign.objects.filter(campaign=self)
        res = []
        count = 1
        for investor in investors:
            show = show_users or investor.investor_profile == investor_profile
            res.append({
                'status': investor.status_str(),
                'amount': investor.amount,
                'user_profile': ("Инвеститор %d" % count) if not show else investor.investor_profile.get_display_name(),
                'user_profile_link': '' if not show else investor.investor_profile.get_href(),
                'user_profile_avatar': '/static/img/undraw_profile.svg' if not show else investor.investor_profile.get_avatar_url(),
            })
            count = count + 1
        return res

        
        
    

class InvestementInCampaign(models.Model):
    class Status(models.TextChoices):
        INTERESTED = 'IN', ('Interested')
        CANCELED = 'CA', ('Canceled')
        COMPLETED = 'CO', ('Completed')
        
    #name = models.CharField(max_length=128)
    investor_profile = models.ForeignKey(UserProfile, null=False, blank=False, on_delete=models.DO_NOTHING)
    campaign = models.ForeignKey(
        Campaign, null=True, blank=True, default=None, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(
        default=10000, max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.INTERESTED,
    )
    
    def share_from_factory(self):
        return ((self.amount * self.campaign.persent_from_profit)/ self.campaign.amount).quantize(Decimal('.01'))
    
    
    def status_str(self):
        if self.campaign.accept_investments():
            if self.status == InvestementInCampaign.Status.INTERESTED:
                return 'Заявен интерес'
            if self.status == InvestementInCampaign.Status.CANCELED:
                return 'Отменен'
            if self.status == InvestementInCampaign.Status.COMPLETED:
                return 'Завършен'
        else:
            if self.campaign.status == Campaign.Status.COMPLETED:
                return 'Очакваме депозит' 
            else:
                return 'Кампанията е изтекла'
        return 'Unknown'
    

    def status_color(self):
        if self.campaign.accept_investments():
            if self.status == InvestementInCampaign.Status.INTERESTED:
                return 'blue'
            if self.status == InvestementInCampaign.Status.CANCELED:
                return 'red'
            if self.status == InvestementInCampaign.Status.COMPLETED:
                return 'green'
        else:
            if self.campaign.status == Campaign.Status.COMPLETED:
                return 'green' 
            else:
                return 'red'
        return 'blue'
    
    def show_link_in_dashboard(self):
        return self.status != InvestementInCampaign.Status.CANCELED

       
    
class FinancialPlan(models.Model):
    name = models.TextField()
    factory = models.ForeignKey(
        ElectricityFactory, on_delete=models.DO_NOTHING)
    start_month = models.DateField()
    span_in_months = models.IntegerField()
    capitalization = models.DecimalField(max_digits=12, decimal_places=2)
    manager_capital = models.DecimalField(max_digits=12, decimal_places=2)
    loan = models.ForeignKey(
        BankLoan, null=True, blank=True, on_delete=models.DO_NOTHING)
    solar_estates = models.ForeignKey(
        Campaign, null=True, blank=True, on_delete=models.DO_NOTHING)
    working_hours = models.ForeignKey(
        FactoryProductionPlan, null=True, blank=True, on_delete=models.DO_NOTHING)
    prices = models.ForeignKey(
        ElectricityPricePlan, null=True, blank=True, on_delete=models.DO_NOTHING)

    def rows(self):
        res = []
        next_month = self.start_month
        for i in range(self.span_in_months):
            res.append({
                'month':  next_month.strftime('%b %y')
            })
            next_month = date(next_month.year + int(next_month.month / 12),
                              ((next_month.month % 12) + 1), next_month.day)
        return res
