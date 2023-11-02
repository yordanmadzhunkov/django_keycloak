from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render, redirect

from vei_platform.forms import BankAccountForm, BankAccountDepositForm
from vei_platform.models.finance_modeling import BankAccount, BankTransaction
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.platform import PlatformLegalEntity

from django.contrib import messages

from decimal import Decimal
from datetime import datetime
def legal_entities_pk_for_user(user):
    profile = get_user_profile(user)
    res = []
    entity = find_legal_entity(user=user)
    if entity:
        res.append(entity.pk)
    for factory in ElectricityFactory.objects.filter(manager=profile.user):
        if factory.primary_owner:
            res.append(factory.primary_owner.pk)
    if profile.user.is_superuser:
        for platform in PlatformLegalEntity.objects.all():
            res.append(platform.entity.pk)
    return res

@login_required(login_url='/oidc/authenticate/')
def view_bank_accounts(request):
    context = common_context()
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        context['profile'] = profile
    entities = legal_entities_pk_for_user(user=request.user)
    form = BankAccountForm(entities, request.POST)
    if request.method == "POST":
        if form.is_valid():
            balance = form.cleaned_data['balance']
            new_account = BankAccount(
                owner = form.cleaned_data['owner'],
                iban = form.cleaned_data['iban'], 
                balance = balance,
                initial_balance = balance,
                currency = form.cleaned_data['currency'], 
                status = BankAccount.AccountStatus.UNVERIFIED
            )
            new_account.save()
        else:
            messages.error(request, 'Invalid from ' + str(form.errors))
    accounts = BankAccount.objects.filter(owner__in=entities)
    context['accounts'] = accounts            
    context['form'] = form
    return render(request, "bank_accounts.html", context)

@login_required(login_url='/oidc/authenticate/')
def view_verify_bank_account(request, pk=None):
    if request.method == "POST":
        account = BankAccount.objects.get(pk=pk)
        if account.status == BankAccount.AccountStatus.UNVERIFIED:
            account.status = BankAccount.AccountStatus.ACTIVE
            account.save()
            messages.success(request, "Activating " + str(account))
        elif account.status == BankAccount.AccountStatus.ACTIVE:
            messages.info(request, "Already active account " + str(account))
        else:
            messages.error(request, "Can't activate " + str(account))
    return redirect('bank_accounts')
    
@login_required(login_url='/oidc/authenticate/')
def view_deposit_bank_account(request, pk=None):
    context = common_context()
    bank_account = BankAccount.objects.get(pk=pk)
    context['bank_account'] = bank_account
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        context['profile'] = profile

    form = BankAccountDepositForm(bank_account, request.POST)
    if request.method == "POST":
        if form.is_valid():
            if 'deposit' in request.POST:
                occured_at = form.cleaned_data['occured_at']
                destination_account = BankAccount.objects.get(pk=form.cleaned_data['dest_iban'])
                source_account = bank_account
                amount = Decimal(form.cleaned_data['amount'])
                description = form.cleaned_data['description']

                deposit = BankTransaction(
                    account = source_account,
                    amount = -Decimal(form.cleaned_data['amount']),
                    fee = Decimal(0.0),
                    other_account_iban = destination_account.iban,
                    occured_at = occured_at,
                    description = description)
            
                accepted_deposit = BankTransaction(
                    account = destination_account,
                    amount = amount,
                    fee = Decimal(0.0),
                    other_account_iban = source_account.iban,
                    occured_at = occured_at,
                    description = description)
                
                deposit.save()
                accepted_deposit.save()
                messages.success(request, str(deposit))
                form.clean()
    context['transactions'] = BankTransaction.objects.filter(account=bank_account)
    context['form'] = form
    return render(request, "bank_account_deposit.html", context)

@login_required(login_url='/oidc/authenticate/')
def view_withdraw_bank_account(request, pk=None):
    context = common_context()
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        context['profile'] = profile
    return render(request, "bank_account_deposit.html", context)
