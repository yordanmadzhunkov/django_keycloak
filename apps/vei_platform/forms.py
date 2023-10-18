from django import forms
from datetime import date
from .models.factory import FactoryProductionPlan
from .models.finance_modeling import ElectricityPricePlan, BankLoan
from .models.profile import UserProfile



class FactoryFinancialPlaningForm(forms.Form):
    capitalization = forms.DecimalField(label='Капитализация',
                                        initial=53000,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                "class": "input",
                                                "inputmode": "decimal",
                                            }
                                        ))
    start_date = forms.DateField(initial=date(2023, 6, 1))

    production_plan = forms.ChoiceField(
        choices=(), required=False
    )

    electricity_prices = forms.ChoiceField(
        choices=()
    )

    bank_loan = forms.ChoiceField(
        choices=()
    )

    start_year = forms.IntegerField(
        initial=2021, max_value=2050, min_value=1990, required=True)
    end_year = forms.IntegerField(
        initial=2025, max_value=2050, min_value=1990, required=True)

    def __init__(self, factory, *args, **kwargs):
        super(FactoryFinancialPlaningForm, self).__init__(*args, **kwargs)
        production_plan_choise = [
            (t.pk, t.name) for t in FactoryProductionPlan.objects.filter(factory=factory)]
        self.fields['production_plan'] = forms.ChoiceField(label="работни часове",
                                                           choices=production_plan_choise)

        electricity_prices = [(t.pk, t.name)
                              for t in ElectricityPricePlan.objects.all()]
        self.fields['electricity_prices'] = forms.ChoiceField(label='Цена на тока',
                                                              choices=electricity_prices)

        bank_loans = [(t.pk, str(t)) for t in BankLoan.objects.all()]
        self.fields['bank_loan'] = forms.ChoiceField(
            label="Банково финансиране", choices=bank_loans)


class PricePlanForm(forms.ModelForm):
    class Meta:
        model = ElectricityPricePlan
        fields = "__all__"
        labels = {
            'name': 'Име на план',
            'start_year': 'Начало',
            'end_year': 'Край',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'title': 'Plan name'}),
            'start_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:9ch',
            }),
            'end_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:9ch',
            }),
        }


class BankLoanForm(forms.ModelForm):
    class Meta:
        model = BankLoan
        fields = "__all__"
        labels = {
            'start_date': 'Дата на отпускане',
            'amount': 'Размер',
            'duration': 'Период [месеци]',
        }
        exclude = ["factory"]
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'title': 'Дата на отпускане'}),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:19ch',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:19ch',
            }),
        }


class NumberPerMonthForm(forms.Form):
    number = forms.CharField(initial=None,
                             required=False,
                             widget=forms.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': 'Enter numbers Only'}))
    month = forms.DateField(widget=forms.HiddenInput(), required=True)


class UserProfileForm(forms.Form):
    avatar = forms.ImageField(initial=None, required=False,)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)


class FactoryScriperForm(forms.Form):
    page_number = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'pattern': '[0-9\.]+',
                                      'style': 'width:9ch',
                                      'title': 'Enter numbers Only'}))


class SolarEstateListingForm(forms.Form):
    amount = forms.DecimalField(label='Капитализация',
                                        initial=1000,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                "class": "form-control",
                                                "inputmode": "decimal",
                                            }
                                        ))

    persent_from_profit = forms.DecimalField(label='Дял от централата[%]',
                                        initial=10.0,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                "class": "form-control",
                                                "inputmode": "decimal",
                                            }
                                        ))


    start_date = forms.DateField(initial=date(2023, 6, 1),
                                widget= forms.widgets.SelectDateWidget(attrs={
                'class': 'form-control',
                'title': 'Дата на придобиване'})
                                    )

    duration = forms.CharField(initial="180",
                               label='Продължителност',
                             required=False,
                             widget=forms.widgets.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': 'Enter numbers Only'}))

    commision = forms.DecimalField(label='Комисионна за Солар Естайет [%]',
                                        initial=1.5,
                                        widget=forms.widgets.TextInput(attrs={
                                            'class': 'form-control',
                                            'autocomplete': 'off',
                                            'pattern': '[0-9\.]+',
                                            'style': 'width:9ch',
                                            'title': 'Enter numbers Only',
                                            'readonly': True,}
                                        )
                                 )
                                        
                                        
        