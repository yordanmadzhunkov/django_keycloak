from . import common_context

from django.contrib.auth.decorators import login_required
from vei_platform.models.profile import get_user_profile
from django.shortcuts import render

from vei_platform.forms import BankAccountForm
from vei_platform.models.finance_modeling import BankAccount
from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory

from django.contrib import messages

@login_required(login_url='/oidc/authenticate/')
def view_bank_accounts(request):
    context = common_context()
    avatar_url = None
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        context['profile'] = profile
        avatar_url = profile.get_avatar_url()
    context['accounts'] = [
        {
            'iban':'LU130107645115151684',
            'currency': 'EUR',
            'status': 'Active',
            'owner': 'John Doe',
            'avatar_url': avatar_url,
            'actions': ['Withdraw', 'Deposit',]
         },
        {
            'iban':'IR547132577934248129248933',
            'currency': 'Iranian rial',
            'status': 'Inactive',
            'owner': 'Al shamany',
            'avatar_url': avatar_url,
            'actions': [],
         },
        {
            'iban':'BG58UNCR70005276158923',

            'currency': 'BGN',
            'status': 'Unverified',
            'owner': 'Ivan Ivanov',
            'avatar_url': avatar_url,
            'actions': ['Verify', ],
         },
    ]

    my_list = []
    entity = find_legal_entity(user=request.user)
    if entity:
        my_list.append(entity.pk)
    for factory in ElectricityFactory.objects.filter(manager=profile.user):
        if factory.primary_owner:
            my_list.append(factory.primary_owner.pk)
    if profile.user.is_superuser:
        print("Admin power hahah")         

    form = BankAccountForm(my_list, request.POST)
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
    context['form'] = form
    return render(request, "bank_accounts.html", context)