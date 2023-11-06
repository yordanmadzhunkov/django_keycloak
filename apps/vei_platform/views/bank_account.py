from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render, redirect

from vei_platform.forms import BankAccountForm, BankAccountDepositForm, PlatformWithdrawForm
from vei_platform.models.finance_modeling import BankAccount, BankTransaction
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.platform import PlatformLegalEntity, platform_bank_accounts

from vei_platform.templatetags.vei_platform_utils import balance_from_transactions

from . import get_balance, get_user_profile

from django.contrib import messages
from decimal import Decimal

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
    context = common_context(request)
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
    context = common_context(request)
    bank_account = BankAccount.objects.get(pk=pk)
    context['bank_account'] = bank_account
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
    context = common_context(request)
    bank_account = BankAccount.objects.get(pk=pk)
    context['bank_account'] = bank_account
    c = bank_account.currency
    balances = get_balance(get_user_profile(request.user))
    availabe = Decimal(0)
    for cur, val in balances:
        if cur == c:
            availabe = val
    context['availabe'] = availabe
    form = PlatformWithdrawForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            requested_amount = Decimal(form.cleaned_data['amount'])
            if requested_amount <= availabe:
                messages.info(request, "You can withdraw %s" % str(requested_amount))
                accounts = platform_bank_accounts(c)
                for account in accounts:
                    balance = balance_from_transactions(account)
                    if balance >= requested_amount:
                        print("do it %s->%s" % (account.iban, bank_account))
            else:
                messages.error(request, "Not enough money in you account")
        else:
            messages.error(request, "Invalid form")

    context['form'] = form
    return render(request, "bank_account_withdraw.html", context)
