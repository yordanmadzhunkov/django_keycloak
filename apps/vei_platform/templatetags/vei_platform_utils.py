from django import template
from vei_platform.models.finance_modeling import SolarEstateListing
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


