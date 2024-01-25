from . import common_context, get_balance, get_user_profile

from vei_platform.models.profile import get_user_profile
from vei_platform.forms import BankAccountForm, BankAccountDepositForm, PlatformWithdrawForm
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from vei_platform.templatetags.vei_platform_utils import balance_from_transactions

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
from django.utils.translation import gettext as _


def legal_entities_pk_for_user(user):
    profile = get_user_profile(user)
    res = []
    entity = find_legal_entity(user=user)
    if entity:
        res.append(entity.pk)
    for factory in ElectricityFactory.objects.filter(manager=profile.user):
        if factory.primary_owner:
            res.append(factory.primary_owner.pk)
    return res
