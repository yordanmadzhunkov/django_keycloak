from django import template
from django.db import models

from vei_platform.models.finance_modeling import FactoryListing, BankAccount, BankTransaction
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory

from decimal import Decimal

register = template.Library()

@register.filter(is_safe=True)
def is_listed(factory):
    return len(FactoryListing.objects.filter(factory=factory)) > 0

@register.filter(is_safe=True)
def total_amount_listed(factory):
    total = Decimal(0)
    for o in  FactoryListing.objects.filter(factory=factory):
        total += o.amount
    res = '{:,}'.format(total) 
    # print(res)
    return res

@register.filter(is_safe=True)
def get_active_listing_pk(factory):
    obj = FactoryListing.objects.filter(factory=factory)
    if len(obj) > 0:
        return obj[0].pk
    return None


@register.filter(is_safe=True)
def balance_from_transactions(account):
    r = BankTransaction.objects.filter(account=account).aggregate(
        total=models.Sum(models.F('amount') - models.F('fee')))
    return Decimal(r['total'] if r['total'] else 0)