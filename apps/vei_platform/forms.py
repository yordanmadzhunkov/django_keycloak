from django import forms
from datetime import date, datetime
from .models.factory import FactoryProductionPlan, ElectricityFactory
from .models.finance_modeling import ElectricityPricePlan, BankLoan, BankAccount, BankTransaction, InvestementInCampaign
from .models.profile import UserProfile
from .models.legal import LegalEntity, find_legal_entity
from .models.platform import platform_bank_accounts


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field

import re
from django.conf import settings
from django.utils.translation import get_language
from django import forms
from django.utils import formats, timezone
from django.core.validators import MaxValueValidator, MinValueValidator

class BootstrapDatePicker(forms.DateInput):
    format_re = re.compile(r'(?P<part>%[bBdDjmMnyY])')

    def __init__(self, attrs=None, format=None):
        '''
        for a list of useful attributes see:
        http://bootstrap-datepicker.readthedocs.io/en/latest/options.html

        Most options can be provided via data-attributes. An option can be
        converted to a data-attribute by taking its name, replacing each
        uppercase letter with its lowercase equivalent preceded by a dash, and
        prepending 'data-date-' to the result. For example, startDate would be
        data-date-start-date, format would be data-date-format, and
        daysOfWeekDisabled would be data-date-days-of-week-disabled.
        '''
        # final_attrs provides:
        # - data-provide: apply datepicker to inline created inputs
        # - data-date-language: apply the current language
        # - data-date-format: apply the current format for dates
        final_attrs = {
            'data-provide': 'datepicker',
            'data-date-language': get_language(),
            'data-date-format': self.get_date_format(format=format),
            'data-date-autoclose': 'true',
            'data-date-clear-btn': 'true',
            'data-date-today-btn': 'linked',
            'data-date-today-highlight': 'true',
        }
        if attrs is not None:
            classes = attrs.get('class', '').split(' ')
            classes.append('datepicker')
            attrs['class'] = ' '.join(classes)
            final_attrs.update(attrs)
        super(BootstrapDatePicker, self).__init__(attrs=final_attrs, format=format)

    def get_date_format(self, format=None):
        format_map = {
            '%d': 'dd',
            '%j': 'd',
            '%m': 'mm',
            '%n': 'm',
            '%y': 'yy',
            '%Y': 'yyyy',
            '%b': 'M',
            '%B': 'MM',
        }
        if format is None:
            format = formats.get_format(self.format_key)[0]
        return re.sub(self.format_re, lambda x: format_map[x.group()], format)



class FactoryFinancialPlaningForm(forms.Form):
    capitalization = forms.DecimalField(label='Капитализация',
                                        initial=53000,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                'class': 'input',
                                                'inputmode': 'decimal',
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
        self.fields['production_plan'] = forms.ChoiceField(label='работни часове',
                                                           choices=production_plan_choise)

        electricity_prices = [(t.pk, t.name)
                              for t in ElectricityPricePlan.objects.all()]
        self.fields['electricity_prices'] = forms.ChoiceField(label='Цена на тока',
                                                              choices=electricity_prices)

        bank_loans = [(t.pk, str(t)) for t in BankLoan.objects.all()]
        self.fields['bank_loan'] = forms.ChoiceField(
            label='Банково финансиране', choices=bank_loans)


class PricePlanForm(forms.ModelForm):
    class Meta:
        model = ElectricityPricePlan
        fields = '__all__'
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
        fields = '__all__'
        labels = {
            'start_date': 'Дата на отпускане',
            'amount': 'Размер',
            'duration': 'Период [месеци]',
        }
        exclude = ['factory']
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

class LegalEntityForm(forms.ModelForm):
    class Meta:
        model = LegalEntity
        fields = '__all__'
        exclude = ['legal_form', 'person']
        labels = {
            'founded': 'Рожденна дата',
            'tax_id': 'ЕГН',
            'native_name': 'Всички имена',
            'latin_name': 'Всички имена на латиница'

        }
        widgets = {
            'founded': BootstrapDatePicker(attrs={
                'class': 'form-control',
                'title': 'Birthday'},
                ),    
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': 'Enter numbers Only'}),
            'native_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'style': 'width:50ch',}),
            'latin_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'style': 'width:50ch',}),
        }


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = '__all__'
        exclude = ['initial_balance', 'status']
        widgets = {
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:40ch',
            }),
            'balance': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': 'Enter numbers Only'}),
        }

    def __init__(self, legal_entities_pk_list, *args, **kwargs):
        super (BankAccountForm,self ).__init__(*args,**kwargs) # populates the post
        self.fields['owner'].queryset = LegalEntity.objects.filter(pk__in=legal_entities_pk_list)

class BankAccountDepositForm(forms.ModelForm):
    class Meta:
        model = BankTransaction
        fields = '__all__'
        exclude = ['account', 'other_account_iban', 'fee']
        widgets = {
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:40ch',
            }),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': 'Enter numbers Only'}),
            'fee': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': 'Enter numbers Only'}),
            'occured_at':  BootstrapDatePicker(attrs={
                'class': 'form-control',
                'title': 'Date of transaction',
                'style': 'width:12ch',
                'data-date-autoclose': 'true',
                'data-date-clear-btn': 'false',
                'data-date-today-btn': 'linked',
                'data-date-today-highlight': 'true'
                }),
        }

    def __init__(self, bank_account, *args, **kwargs):
        super (BankAccountDepositForm, self).__init__(*args,**kwargs) # populates the post
        bank_accounts = [(t.pk, str(t)) for t in platform_bank_accounts(bank_account.currency)]
        dest_iban = forms.ChoiceField(label='IBAN', choices=bank_accounts)
        self.fields['dest_iban'] = dest_iban 

class PlatformWithdrawForm(forms.Form):
    amount = forms.CharField(initial='0',
                             required=False,
                             widget=forms.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': 'Enter numbers Only'})
                             )
    occured_at = forms.DateTimeField(initial=datetime.today(),
                               required=True,
                               widget=BootstrapDatePicker(attrs={
                'class': 'form-control',
                'title': 'Date of transaction',
                'style': 'width:12ch',
                'data-date-autoclose': 'true',
                'data-date-clear-btn': 'false',
                'data-date-today-btn': 'linked',
                'data-date-today-highlight': 'true'
                }))
    
    #def __init__(self, user, *args, **kwargs):
        #super (PlatformWithdrawForm, self).__init__(*args, **kwargs) # populates the post
        #bank_accounts = [(t.pk, str(t)) for t in platform_bank_accounts(bank_account.currency)]
        #dest_iban = forms.ChoiceField(label='IBAN', choices=bank_accounts)
        #self.fields['dest_iban'] = dest_iban 


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
    avatar = forms.ImageField(initial=None, 
                              required=False,
                              widget=forms.ClearableFileInput(attrs={
                                    'onchange': 'showImage(this);',}))
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    show_balance = forms.BooleanField(required=False, 
                                      label='Show balance', 
                                      widget=forms.CheckboxInput(attrs={
                                        'class': 'form-control form-control-user',})
                                      )


class FactoryScriperForm(forms.Form):
    page_number = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'pattern': '[0-9\.]+',
                                      'style': 'width:9ch',
                                      'title': 'Enter numbers Only'}))
    tax_id = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'pattern': '[0-9\.]+',
                                      'style': 'width:9ch',
                                      'title': 'Enter numbers Only'}))


class SearchForm(forms.Form):
    search_text = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'style': 'width:30ch',
                                      'title': 'Text to search'}))


class FactoryListingForm(forms.Form):
    amount = forms.DecimalField(label='Капитализация',
                                help_text='Общата сума на електроцентралата в лева',
                                        initial=1000,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                'class': 'form-control',
                                                'inputmode': 'decimal',
                                            }
                                        ))

    persent_from_profit = forms.DecimalField(label='Дял от централата[%]',
                                        help_text='Който искате да продадете. Сумата, която ще получите е капитализацията по дяла минус комисионната на платформата',
                                        initial=10.0,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                'class': 'form-control',
                                                'inputmode': 'decimal',
                                            }
                                        ))


    start_date = forms.DateField(label='Влизане в сила',
                                 help_text='Дата на която ще се разделите с вашият дял, ако съберем нужното количество инвестирори',
                                 initial=date(2023, 6, 1),
                                 widget=BootstrapDatePicker(attrs={
                                    'title': 'Дата',
                                    'class': 'form-control',
                                    'style': 'width:18ch',
                                    'data-date-autoclose': 'true',
                                    'data-date-clear-btn': 'false',
                                    'data-date-today-btn': 'linked',
                                    'data-date-today-highlight': 'true'
                                    }),
                                    )

    duration = forms.CharField(initial='180',
                               label='Продължителност',
                               help_text='Броя месеци в който инвеститорите ще получават съответстващият им дял от печалбите. След изтичане на периода, цялата собственост се връща на оригинатора. 15 години или 180 месеца е добър срок',

                             required=False,
                             widget=forms.widgets.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': 'Enter numbers Only'}))

    commision = forms.DecimalField(label='Комисионна [%]',
                                   help_text='% комисионна за платформата. Удържа се веднъж при първоначалното инвестиране, както и при бъдещите разплащания от елекроцентралата към ивеститорите. ',
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
    
class CreateInvestmentForm(forms.Form):
    amount = forms.DecimalField(label='Инвестиция',
                                help_text='Общата сума, която искате да ивестирате в централата',
                                        initial=1000,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                'class': 'form-control',
                                                'inputmode': 'decimal',
                                            }
                                        ))
    def __init__(self, *args, **kwargs):
        super(CreateInvestmentForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('amount', css_class='form-group'),
                css_class='form-row'
            ),
            Submit('invest', 'Заяви интерес')
        )

class CampaingEditForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CampaingEditForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        cancel = Submit('cancel', 'Отмяна')
        cancel.field_classes = 'btn btn-danger'
        complete = Submit('complete', 'Завърши')
        complete.field_classes = 'btn btn-success'
        self.helper.layout = Layout(
            complete,
            cancel,
        )

class EditInvestmentForm(forms.ModelForm):
    class Meta:
        model = InvestementInCampaign
        fields = ('amount',)
    
    def __init__(self, *args, **kwargs):
        super(EditInvestmentForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        cancel = Submit('cancel', 'Отмяна')
        cancel.field_classes = 'btn btn-danger'
        save = Submit('save', 'Запази')
        save.field_classes = 'btn btn-warning'
        self.helper.layout = Layout(
            Row(
                Column('amount', css_class='form-group'),
                css_class='form-row'
            ),
            save,
            cancel,
        )


class CustomImageField(Field):
    template = 'layout/image_thumbnail.html'

                             
class FactoryModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FactoryModelForm, self).__init__(*args, **kwargs)

        FACTORY_TYPE_CHOISES = (
            (ElectricityFactory.PHOTOVOLTAIC, 'ФЕЦ'),
            (ElectricityFactory.WIND_TURBINE, 'ВтЕЦ'),
            (ElectricityFactory.HYDROPOWER, 'ВЕЦ'),
            (ElectricityFactory.BIOMASS, 'БиоЕЦ'),
            (ElectricityFactory.REN_GAS, 'БиоГЕЦ'),
        )

        factory_type = forms.TypedChoiceField( 
                   choices = FACTORY_TYPE_CHOISES, 
                   label= 'Вид електроцентрала',
                   coerce = str
                  ) 
        self.fields['factory_type'] = factory_type

        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('factory_type', css_class='form-group col-md-2 mb-0'),
                Column('name', css_class='form-group col-md-10 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('opened', css_class='form-group col-md-2 mb-0'),
                Column('capacity_in_mw', css_class='form-group col-md-2 mb-0'),
                Column('location', css_class='form-group col-md-8 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('owner_name', css_class='form-group col-md-8 mb-0'),
                Column('tax_id', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(CustomImageField('image'), css_class='form-group col-md-12'),
                css_class='form-row'
            ),
            Submit('add', 'Добави')
        )

    class Meta:
        model = ElectricityFactory
        fields = '__all__'
        exclude = ['manager', 'primary_owner']
        labels = {
            'name': 'Име на електроцентралата',
            'location': 'Местоположение',
            'opened': 'в експлотация от',
            'capacity_in_mw': 'капацитет [в MW]',
            'tax_id': 'ЕИК',
            'owner_name': 'Юридическо лице собственик на централата',
            'factory_type': 'Вид електроцентрала',
            'image': "Снимка"
        }
#        help_texts = {
#            'client_id': (
#                'Um identificador exclusivo de formato livre da chave. 50 caracteres no máximo'
#            ),
#        }
        widgets = {
            'opened': BootstrapDatePicker(attrs={
                'class': 'form-control',
                'title': 'Date of transaction',
                'style': 'width:18ch',
                'data-date-autoclose': 'true',
                'data-date-clear-btn': 'false',
                'data-date-today-btn': 'linked',
                'data-date-today-highlight': 'true'
                }),
        }
