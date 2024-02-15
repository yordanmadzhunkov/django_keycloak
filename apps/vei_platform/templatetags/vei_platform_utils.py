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
def get_active_campaign(factory):
    return Campaign.get_last_campaign(factory)

@register.filter(is_safe=True)
def campaign_links(factory, user):
    #print (user.is_staff)
    #factory
    campaign = Campaign.get_last_campaign(factory)
    #if not user.is_authenticated:
        #{% trans "You need to login in order to claim interest in project" %}
        #<a href="{% url 'oidc_authentication_init' %}">{% trans "Login" %}</a>
    #     return [{ 'href': reverse('oidc_authentication_init'),
    #               'title': _('You need to login in order to claim interest in project'),
    #              'css_class': 'btn-success',
    #    }]    
    if campaign:
        return [{ 'href': campaign.get_absolute_url(),
                  'title': campaign.status_str(),
                  'css_class': 'btn-info',
        }]
    else:
        if factory.manager == user:
            return [
                {               
                    'href': reverse('campaign_create', kwargs={'pk':factory.pk}),
                    'title': _('Start campaign'),
                    'css_class': 'btn-success',
                },
                {               
                    'href': reverse('factory_edit', kwargs={'pk':factory.pk}),
                    'title': _('Edit factory'),
                    'css_class': 'btn-warning',
                },
            ]
        else:
            print("manager = %s user = %s" % (factory.manager, user))
        return []
    return factory.campaign_links()


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

