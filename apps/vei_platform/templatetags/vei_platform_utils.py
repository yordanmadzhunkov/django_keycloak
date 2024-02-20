from django import template
from django.db import models

from vei_platform.models.campaign import Campaign
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from django.contrib.sites.models import Site
from decimal import Decimal
from os import path
from django.utils.translation import gettext as _
from django.urls import reverse

register = template.Library()

@register.filter(is_safe=True)
def get_last_campaign(factory):
    return Campaign.get_last_campaign(factory)

@register.filter(is_safe=True)
def campaign_links(factory, user):
    campaign = Campaign.get_last_campaign(factory)
    is_manager = factory.manager == user
    #is_staff = user.is_staff

    if is_manager and (campaign is None or campaign.allow_start_new_campaign()):
        return [
                {               
                    'href': reverse('campaign_create', kwargs={'pk':factory.pk}),
                    'title': _('Start campaign'),
                    'css_class': 'btn btn-block btn-success',
                },
                {               
                    'href': reverse('factory_edit', kwargs={'pk':factory.pk}),
                    'title': _('Edit factory'),
                    'css_class': 'btn btn-block btn-warning',
                },
        ]

    if campaign:
        return [{ 'href': campaign.get_absolute_url(),
                  'title': _('View campaign'),
                  'css_class': 'btn btn-block btn-info',
        }]
    
    return []


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

