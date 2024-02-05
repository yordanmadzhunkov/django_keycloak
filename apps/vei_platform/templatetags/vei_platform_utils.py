from django import template
from django.db import models

from vei_platform.models.finance_modeling import Campaign
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from django.contrib.sites.models import Site
from decimal import Decimal
from os import path

register = template.Library()

@register.filter(is_safe=True)
def is_listed(factory):
    return Campaign.is_listed(factory)

@register.filter(is_safe=True)
def total_amount_listed(factory):
    campaing = Campaign.get_active(factory)
    if campaing:
        return campaing.amount
    return Decimal(0)


@register.filter(is_safe=True)
def get_active_campaign(factory):
    return Campaign.get_active(factory)
 
@register.filter(is_safe=True)
def get_campaign_progress_percent(factory):
    return Campaign.get_active(factory).progress()['percent']

@register.filter(is_safe=True)
def available_for_investment(factory):
    return Campaign.get_active(factory).progress()['available']

@register.filter(is_safe=True)
def get_campaign_progress_amount(factory):
    return Campaign.get_active(factory).progress()['total']

@register.filter(is_safe=True)
def has_completed_campaign(factory):
    return Campaign.get_last_completed(factory) != None

@register.filter(is_safe=True)
def last_completed_campaign_amount(factory):
    return Campaign.get_last_completed(factory).progress()['total']

@register.filter(is_safe=True)
def last_completed_campaign_href(factory):
    return Campaign.get_last_completed(factory).get_absolute_url()

@register.filter(is_safe=True)
def balance_from_transactions(account):
    r = BankTransaction.objects.filter(account=account).aggregate(
        total=models.Sum(models.F('amount') - models.F('fee')))
    return Decimal(r['total'] if r['total'] else 0)

@register.filter(is_safe=True)
def basename(filepath):
    return path.basename(filepath)


@register.simple_tag()
def current_domain():
    dom = Site.objects.get_current().domain
    if dom.startswith('http://'):
        return dom.replace('http://', 'https://')
    return dom
    #'http://%s' % Site.objects.get_current().domain
    #return '%s' % Site.objects.get_current()

