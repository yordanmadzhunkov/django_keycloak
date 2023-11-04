from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.forms import formset_factory
from django.forms.models import model_to_dict


from . import common_context, generate_formset_table
from vei_platform.models.finance_modeling import BankLoan, BankLoanInterest
from vei_platform.forms import NumberPerMonthForm, BankLoanForm


from decimal import Decimal, DecimalException


@login_required(login_url='/oidc/authenticate/')
def view_bank_loan_detail(request, pk=None):
    context = common_context(request)
    loan = BankLoan.objects.get(pk=pk)
    objects = BankLoanInterest.objects.filter(loan=loan)
    factory = loan.factory

    # creating a formset
    NumberPerMonthFormSet = formset_factory(
        NumberPerMonthForm, extra=0)
    PricePlanFormSet = formset_factory(BankLoanForm, extra=0)

    if request.POST:
        numbers_formset = NumberPerMonthFormSet(request.POST, prefix='numbers')
        loan_formset = PricePlanFormSet(request.POST, prefix='loan')

        if numbers_formset.is_valid():
            # All validation rules pass
            # save to database :)
            for form in numbers_formset:
                hours_str = form.cleaned_data['number']
                month = form.cleaned_data['month']
                try:
                    val = Decimal(hours_str)
                    s = objects.filter(
                        month__year=month.year).filter(month__month=month.month)
                    if len(s) == 0:
                        obj = BankLoanInterest(
                            loan=loan, month=month, number=val)
                        obj.save()
                    else:
                        if val != s[0].number:
                            s[0].number = val
                            s[0].save()
                except (ValueError, DecimalException):
                    pass
        if loan_formset.is_valid():
            # one form only
            for form in loan_formset:
                needs_save = False
                if loan.duration != form.cleaned_data['duration']:
                    loan.duration = form.cleaned_data['duration']
                    needs_save = True

                if loan.start_date != form.cleaned_data['start_date']:
                    loan.start_date = form.cleaned_data['start_date']
                    needs_save = True

                if loan.amount != form.cleaned_data['amount']:
                    loan.amount = form.cleaned_data['amount']
                    needs_save = True

                if needs_save:
                    loan.save()

        return redirect(factory.get_absolute_url())

    years = range(loan.start_year(), loan.end_year())
    numbers_formset, table = generate_formset_table(
        years, objects, NumberPerMonthFormSet, prefix='numbers')
    loan_formset = PricePlanFormSet(
        initial=[model_to_dict(loan)], prefix='loan')
    context['table'] = table

    rows = []
    labels = ['Месец', 'Вноска', 'Погасена лихва',
              'Погасена главница', 'Оставаща главница']
    amortization_schedule = loan.amortization_schedule()
    for row in amortization_schedule:
        number, payment, interest, principal, balance = row
        rows.append(
            [loan.offset_start_date(number).strftime(
                '%b %y'), payment, interest, principal, balance]
        )

    table = {'labels': labels, 'rows': rows}
    context['amortization_schedule'] = {'table': table}
    context['loan_formset'] = loan_formset
    context['numbers_formset'] = numbers_formset
    context['factory'] = factory

    return render(request, "bank_loan.html", context)
