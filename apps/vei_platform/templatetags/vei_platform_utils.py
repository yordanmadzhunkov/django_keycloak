from django import template
from django.db import models

from vei_platform.models.finance_modeling import Campaign, BankAccount, BankTransaction
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory

from decimal import Decimal

register = template.Library()

@register.filter(is_safe=True)
def is_listed(factory):
    return Campaign.is_listed(factory)

@register.filter(is_safe=True)
def total_amount_listed(factory):
    total = Decimal(0)
    for o in  Campaign.objects.filter(factory=factory):
        total += o.amount
    res = '{:,}'.format(total) 
    # print(res)
    return res

@register.filter(is_safe=True)
def get_active_campaign(factory):
    return Campaign.get_active(factory)
 
@register.filter(is_safe=True)
def get_campaign_progress_percent(factory):
    return Campaign.get_active(factory).progress()['percent']
    

@register.filter(is_safe=True)
def balance_from_transactions(account):
    r = BankTransaction.objects.filter(account=account).aggregate(
        total=models.Sum(models.F('amount') - models.F('fee')))
    return Decimal(r['total'] if r['total'] else 0)