from django import template
from django.db import models

from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from django.contrib.sites.models import Site
from decimal import Decimal
from os import path
from django.utils.translation import gettext as _
from django.urls import reverse

register = template.Library()


@register.filter(is_safe=True)
def factory_actions(factory, user):
    is_manager = factory.manager == user
    # is_staff = user.is_staff

    if is_manager:
        return [
            {
                "href": reverse("factory_edit", kwargs={"pk": factory.pk}),
                "title": _("Edit factory"),
                "css_class": "btn btn-block btn-warning",
            },
            {
                "href": reverse("factory_production", kwargs={"pk": factory.pk}),
                "title": _("View production"),
                "css_class": "btn btn-block btn-info",
            },
            {
                "href": reverse("factory_schedule", kwargs={"pk": factory.pk}),
                "title": _("Schedule"),
                "css_class": "btn btn-block btn-warning",
            },
        ]
    return []


@register.filter(is_safe=True)
def basename(filepath):
    return path.basename(filepath)


@register.simple_tag()
def current_domain():
    dom = Site.objects.get_current().domain
    if dom.startswith("http://"):
        return dom.replace("http://", "https://")
    return dom
    #'http://%s' % Site.objects.get_current().domain
    # return '%s' % Site.objects.get_current()
