from django import forms
from datetime import date, datetime
from .models.factory import FactoryProductionPlan, ElectricityFactory, ElectricityFactoryComponents, docfile_content_types
from .models.finance_modeling import ElectricityPricePlan, BankLoan, BankAccount, BankTransaction, InvestementInCampaign
from .models.profile import UserProfile
from .models.legal import LegalEntity, find_legal_entity
from .models.platform import platform_bank_accounts


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field, HTML
from .custom_layout_object import Formset


import re
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext as _
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
    capitalization = forms.DecimalField(label=_('Capitalization'),
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
        self.fields['production_plan'] = forms.ChoiceField(label=_('Working hours'),
                                                           choices=production_plan_choise)

        electricity_prices = [(t.pk, t.name)
                              for t in ElectricityPricePlan.objects.all()]
        self.fields['electricity_prices'] = forms.ChoiceField(label=_('Electricity price'),
                                                              choices=electricity_prices)

        bank_loans = [(t.pk, str(t)) for t in BankLoan.objects.all()]
        self.fields['bank_loan'] = forms.ChoiceField(
            label=_('Bank loan'), choices=bank_loans)


class PricePlanForm(forms.ModelForm):
    class Meta:
        model = ElectricityPricePlan
        fields = '__all__'
        labels = {
            'name': _('Plan name'),
            'start_year': _('Start year'),
            'end_year': _('End year'),
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'title': _('Plan name')}),
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
            'start_date': _('Issued date'),
            'amount': _('Amount'),
            'duration': _('Duration [months]'),
        }
        exclude = ['factory']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'title': _('Issued date')}),
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
            'founded': _('Birth date'),
            'tax_id': _('EGN'),
            'native_name': _('Full name'),
            'latin_name': _('Full name using latin'),
        }
        widgets = {
            'founded': BootstrapDatePicker(attrs={
                'class': 'form-control',
                'title': _('Birthday')},
                ),    
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': _('Enter numbers Only')}),
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
                'title': _('Enter numbers Only')}),
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
                'title': _('Enter numbers Only')}),
            'fee': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'pattern': '[0-9\.]+',
                'style': 'width:30ch',
                'title': _('Enter numbers Only')}),
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
        dest_iban = forms.ChoiceField(label=_('IBAN'), choices=bank_accounts)
        self.fields['dest_iban'] = dest_iban 

class PlatformWithdrawForm(forms.Form):
    amount = forms.CharField(initial='0',
                             required=False,
                             widget=forms.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': _('Enter numbers Only')})
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
                                 'title': _('Enter numbers Only')}))
    month = forms.DateField(widget=forms.HiddenInput(), required=True)


class UserProfileForm(forms.Form):
    avatar = forms.ImageField(initial=None, 
                              required=False,
                              widget=forms.ClearableFileInput(attrs={
                                    'onchange': 'showImage(this);',}))
    first_name = forms.CharField(required=True,
                                 widget=forms.TextInput(attrs={'class': "textinput form-control  form-control-user"}))
    last_name = forms.CharField(required=True,
                                widget=forms.TextInput(attrs={'class': "textinput form-control  form-control-user"}))
    show_balance = forms.BooleanField(required=False, 
                                      label=_('Show balance'), 
                                      widget=forms.CheckboxInput(attrs={
                                        'class': 'form-control form-control-user',})
                                      )
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-sm-3'),
                css_class='form-row'
            ),
        )
        self.fields['first_name'].label = _('First name')
        self.fields['last_name'].label = _('Last name')




class FactoryScriperForm(forms.Form):
    page_number = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'pattern': '[0-9\.]+',
                                      'style': 'width:9ch',
                                      'title': _('Enter numbers Only')}))
    tax_id = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'pattern': '[0-9\.]+',
                                      'style': 'width:9ch',
                                      'title': _('Enter numbers Only')}))


class SearchForm(forms.Form):
    search_text = forms.CharField(initial=None,
                                  required=False,
                                  widget=forms.TextInput(attrs={
                                      'class': 'form-control',
                                      'autocomplete': 'off',
                                      'style': 'width:30ch',
                                      'title': _('Text to search')}))


class FactoryListingForm(forms.Form):
    amount = forms.DecimalField(label=_('Capitalization'),
                                help_text=_('Total value of factory'),
                                initial=1000,
                                widget=forms.widgets.NumberInput(
                                    attrs={
                                        'class': 'form-control',
                                        'inputmode': 'decimal',
                                    }
                                ))

    persent_from_profit = forms.DecimalField(label=_('Share from factory [%]'),
                                        help_text=_('This share will be sold to investors in this platform. The amount you will recieve is this share times capitalization minus platform commision.'),
                                        initial=10.0,
                                        widget=forms.widgets.NumberInput(
                                            attrs={
                                                'class': 'form-control',
                                                'inputmode': 'decimal',
                                            }
                                        ))


    start_date = forms.DateField(label=_('Campaing end date'),
                                 help_text=_('Until this date investors can declare interest in this project. If enough people declare interst in this project you will be able to complete the campaing'),
                                 initial=date(2024, 12, 31),
                                 widget=BootstrapDatePicker(attrs={
                                    'title': _('Date'),
                                    'class': 'form-control',
                                    'style': 'width:18ch',
                                    'data-date-autoclose': 'true',
                                    'data-date-clear-btn': 'false',
                                    'data-date-today-btn': 'linked',
                                    'data-date-today-highlight': 'true'
                                    }),
                                    )

    duration = forms.CharField(initial='180',
                               label=_('Ducation'),
                               help_text=_('Number of months that investors will recieve percent form the profit proportional to their share. After this period ownership will be transfered to original factory owner. A duration of 15 years is good in most cases.'),
                             required=False,
                             widget=forms.widgets.TextInput(attrs={
                                 'class': 'form-control',
                                 'autocomplete': 'off',
                                 'pattern': '[0-9\.]+',
                                 'style': 'width:9ch',
                                 'title': _('Enter numbers Only')}))

    commision = forms.DecimalField(label=_('Commision [%]'),
                                   help_text=_('%% commision for the platform. This commision is withholded once when the initial amout it''s collected and transfered to the factory originar and each time a payment to investors is carried out in the future.'),
                                                
                                        initial=1.5,
                                        widget=forms.widgets.TextInput(attrs={
                                            'class': 'form-control',
                                            'autocomplete': 'off',
                                            'pattern': '[0-9\.]+',
                                            'style': 'width:9ch',
                                            'title': _('Enter numbers Only'),
                                            'readonly': True,}
                                        )
                                 )
    
class CreateInvestmentForm(forms.Form):
    amount = forms.DecimalField(label=_('Interest amount'),
                                help_text=_('Amount which you want to participate in this project'),
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
            Submit('invest', _('Claim interest'))
        )

class CampaingEditForm(forms.Form):
    def __init__(self, allow_finish, *args, **kwargs):
        super(CampaingEditForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        cancel = Submit('cancel', _('Cancel campaign'))
        cancel.field_classes = 'btn btn-danger'
        complete = Submit('complete', _('Finish campaign'))
        complete.field_classes = 'btn btn-success'
        self.helper.layout = Layout(Row(complete), Row(cancel),) if allow_finish else Layout(Row(cancel),)
        

class EditInvestmentForm(forms.ModelForm):
    class Meta:
        model = InvestementInCampaign
        fields = ('amount',)
    
    def __init__(self, *args, **kwargs):
        super(EditInvestmentForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        cancel = Submit('cancel', _('Cancel'))
        cancel.field_classes = 'btn btn-danger'
        save = Submit('save', _('Save'))
        save.field_classes = 'btn btn-warning'
        self.helper.layout = Layout(
            Row(
                Column('amount', css_class='form-group'),
                css_class='form-row'
            ),
            save,
            cancel,
        )
        self.fields['amount'].label = _('Your interest')


class CustomImageField(Field):
    template = 'layout/image_thumbnail.html'

                             


class ElectricityFactoryComponentsForm(forms.ModelForm):
    class Meta:
        model = ElectricityFactoryComponents
        fields = ('component_type', 'name', 'power_in_kw', 'count', 'docfile')
        labels = {
            'component_type': _('Component type'), 
            'name': _('Name'),
            'power_in_kw': _('Power [kW]'),
            'count': _('Count'),
            'docfile': _('Document file [pdf]'),
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:40ch',
                'autocomplete': 'off',
                }),
            'power_in_kw': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:9ch',
            }),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:9ch',
            }),
            'docfile': forms.ClearableFileInput(
                attrs={'accept': docfile_content_types(),                                           
            })
        }
        
    def __init__(self, *args, **kwargs):
        super(ElectricityFactoryComponentsForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.form_show_labels = False
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Row(
                Column('component_type', css_class='form-group col-md-2 mb-0'),
                Column('name',           css_class='form-group col-md-6 mb-0'),
                Column('power_in_kw',    css_class='form-group col-md-2 mb-0'),
                Column('count',          css_class='form-group col-md-2 mb-0'),
                Column('docfile',        css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            )
        )



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
                   label = _('Type energy source'),#'Вид електроцентрала',
                   coerce = str
                  ) 
        self.fields['factory_type'] = factory_type
        save = Submit('save', _('Save'), css_class='btn btn-primary')
        save.field_classes = 'btn btn-success'
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
            HTML('<h2>' + _('Details about the factory') + '</h2>'),
            Formset('formset'),
            save,
        )

    class Meta:
        model = ElectricityFactory
        fields = '__all__'
        exclude = ['manager', 'primary_owner']
        labels = {
            'name': _('Factory name'), #Име на електроцентралата',
            'location': _('Location'),#'Местоположение',
            'opened': _('Opened'),#'в експлотация от',
            'capacity_in_mw': _('Capacity [MW]'),#'капацитет [в MW]',
            'tax_id': _('TAX ID'), #'ЕИК',
            'owner_name': _('Legal entity owning the factory'), #'Юридическо лице собственик на централата',
            'factory_type': _('Energy source type'),
            'image': _('Image'),
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

