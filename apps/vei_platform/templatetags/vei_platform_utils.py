from django import template
from django.db import models

from vei_platform.models.finance_modeling import SolarEstateListing, BankAccount, BankTransaction
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory

from decimal import Decimal

register = template.Library()

@register.filter(is_safe=True)
def is_listed(factory):
    return len(SolarEstateListing.objects.filter(factory=factory)) > 0

@register.filter(is_safe=True)
def total_amount_listed(factory):
    total = Decimal(0)
    for o in  SolarEstateListing.objects.filter(factory=factory):
        total += o.amount
    res = '{:,}'.format(total)  # For Python ≥2.7
    print(res)
    return res

@register.filter(is_safe=True)
def get_balance(profile):
    legal_entities_pk = []
    entity = find_legal_entity(user=profile.user)
    if entity:
        legal_entities_pk.append(entity.pk)

    for factory in ElectricityFactory.objects.filter(manager=profile.user):
        if factory.primary_owner:
            legal_entities_pk.append(factory.primary_owner.pk)
    
    bank_accounts = BankAccount.objects.filter(owner__in=legal_entities_pk)
    amounts = {}
    for account in bank_accounts:
        cur = account.currency
        sum = amounts[cur] if cur in amounts.keys() else Decimal(0)
        balance = sum - balance_from_transactions(account)
        amounts[cur] = balance
    #amounts = {'BGN': Decimal(10), 'EUR': Decimal(20)}
    return amounts.items()

@register.filter(is_safe=True)
def balance_from_transactions(account):
    r = BankTransaction.objects.filter(account=account).aggregate(
        total=models.Sum(models.F('amount') - models.F('fee')))
    return Decimal(r['total'] if r['total'] else 0)