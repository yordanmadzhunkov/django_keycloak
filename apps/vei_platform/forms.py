from django import forms
from datetime import date, datetime
from .models.factory import FactoryProductionPlan, ElectricityFactory, ElectricityFactoryComponents, docfile_content_types
from .models.campaign import InvestementInCampaign, Campaign as CampaignModel
from .models.electricity_price import ElectricityPricePlan
from .models.profile import UserProfile
from .models.legal import LegalEntity, find_legal_entity


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field, HTML
from .custom_layout_object import Formset


import re
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django import forms
from django.utils import formats, timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from djmoney.forms.fields import MoneyField
from .models.timezone_choises import TIMEZONE_CHOICES
from .settings.base import CURRENCY_CHOICES



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
                                'class': 'form-control form-control-user',
                                'onchange': 'showImage(this);',}))
    
    first_name = forms.CharField(required=True,
                                 widget=forms.TextInput(
                                     attrs={'class': "textinput form-control  form-control-user"}))
    
    last_name = forms.CharField(required=True,
                                widget=forms.TextInput(
                                    attrs={'class': "textinput form-control  form-control-user"}))
    timezone = forms.TypedChoiceField( 
                   choices = TIMEZONE_CHOICES, 
                   label = _('Timezone'),
                   coerce = str,
                  ) 
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].label = _('First name')
        self.fields['last_name'].label = _('Last name')
        self.fields['avatar'].label = _('Avatar')
        self.fields['timezone'].label = _('Timezone')







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


class CampaignCreateForm(forms.Form):
    amount_offered = MoneyField(
        default_amount=1000,
        decimal_places=2,
        label=_('Campaign amount'),
        help_text=_('Total amount you want to collect for this campaign'),
    )
    
 
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
                               label=_('Duration'),
                               help_text=_('Number of months that investors will recieve percent form the profit proportional to their share. After this period ownership will be transfered to original factory owner. A duration of 15 years is good in most cases.'),
                               required=True,
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

    def __init__(self, *args, **kwargs):
        super(CampaignCreateForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        create = Submit('complete', _('Start campaign'))
        create.field_classes = 'btn btn-success btn-block'
        self.helper.layout = Layout(
            Row(
                Column('amount_offered', css_class='form-group'),
                Column('persent_from_profit'),
                css_class='form-row',
            ),
            Row(
                Column('start_date'),
                Column('duration'),
                css_class='form-row',
            ),
            Row(Column('commision')), 
            Row(Column(create)),
        )

       
  

    
class CreateInvestmentForm(forms.Form):
    amount = MoneyField(
        default_amount=1000,
        decimal_places=2,
        label=_('Interest amount'),
        help_text=_('Amount which you want to participate in this project'),
    )
        
    def __init__(self, *args, **kwargs):
        super(CreateInvestmentForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs.keys():
            if 'amount' in kwargs['initial'].keys():
                amount = kwargs['initial']['amount']
                self.initial['amunt'] = amount
            
            
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

class LoiginOrRegisterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(LoiginOrRegisterForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        authenticate = Submit('authenticate', _('Login or Register'))
        authenticate.field_classes = 'btn btn-success btn-block'
        self.helper.layout = Layout(Row(authenticate))    


class CampaingEditForm(forms.Form):
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


    def __init__(self, instance, is_reviewer=False, *args, **kwargs):
        super(CampaingEditForm, self).__init__(*args, **kwargs)
    
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.layout = Layout()
        if instance.allow_cancel():
            cancel = Submit('cancel', _('Cancel campaign'))
            cancel.field_classes = 'btn btn-danger btn-block'
            self.helper.layout.append(Row(cancel))
        if instance.allow_finish():
            complete = Submit('complete', _('Finish campaign'))
            complete.field_classes = 'btn btn-success btn-block'
            self.helper.layout.append(Row(complete))
        if instance.allow_extend():
            extend = Submit('extend', _('Extend campaign'))
            extend.field_classes = 'btn btn-warning btn-block'
            self.helper.layout.append(Row(Field('start_date')))
            self.helper.layout.append(Row(extend))
        else:
            del self.fields['start_date']
            
        if is_reviewer and instance.need_approval():
            approve = Submit('approve', _('Approve campaign'))
            approve.field_classes = 'btn btn-success btn-block'
            self.helper.layout.append(Row(approve))

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
        #self.fields['amount'].fields[1].choices = [('EUR', 'EUR €')]
        #[('BGN', 'BGN лв'), ('EUR', 'EUR €'), ('USD', 'USD $')]


class CustomImageField(Field):
    template = 'layout/image_thumbnail.html'

                             


class ElectricityFactoryComponentsForm(forms.ModelForm):
    class Meta:
        model = ElectricityFactoryComponents
        fields = ('component_type',  'power_in_kw', 'count', 'name', 'description', 'docfile',)
        labels = {
            'component_type': _('Component type'), 
            'name': _('Name'),
            'power_in_kw': _('Power [kW]'),
            'count': _('Count'),
            'docfile': _('Document file [pdf]'),
            'description': _('Description')
        }
        docfile = forms.ClearableFileInput(
                attrs={'accept': docfile_content_types(),
                       'class': 'form-control',                                           
            })

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                }
            ),
            'power_in_kw': forms.NumberInput(attrs={
                'class': 'form-control',
                }
            ),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                }
            ),
            'docfile': docfile,
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 10,
                    'cols': 120,
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super(ElectricityFactoryComponentsForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.form_show_labels = True
        for key, value in self.Meta.labels.items():
            self.fields[key].label = _(value)



class FactoryModelForm(forms.ModelForm):
    class Meta:
        model = ElectricityFactory
        fields = '__all__'
        exclude = ['manager', 'primary_owner']
        labels = {
            'name': _('Factory name'),
            'location': _('Location'),
            'opened': _('Opened'),
            'capacity_in_mw': _('Capacity [MW]'),
            'tax_id': _('TAX ID'), 
            'owner_name': _('Legal entity owning the factory'), 
            'factory_type': _('Energy source type'),
            'image': _('Image'),
        }

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
                   label = _('Type energy source'),
                   coerce = str
                  ) 
        self.fields['factory_type'] = factory_type

        for key, value in self.Meta.labels.items():
            self.fields[key].label = _(value)
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
            Formset('formset', 'formset_helper'),
            save,
        )


class ElectricityPlanForm(forms.Form):

    def __init__(self, plans, initial_timezone=None, *args, **kwargs):
        super(ElectricityPlanForm, self).__init__(*args, **kwargs)
        choices = []
        for plan in plans:
            choices.append((plan.slug, plan.name))
        plan_field = forms.TypedChoiceField( 
                   choices = choices, 
                   label = _('Plan'),
                   coerce = str
                  ) 
        self.fields['plan'] = plan_field

        currency = forms.TypedChoiceField( 
                   choices = CURRENCY_CHOICES, 
                   label = _('Currency'),
                   coerce = str
                  ) 
        self.fields['currency'] = currency
        initial_timezone = kwargs.get('initial_timezone','UTC')
        timezone = forms.TypedChoiceField( 
                   choices = TIMEZONE_CHOICES, 
                   label = _('Timezone'),
                   initial = initial_timezone,
                   coerce = str,
                  ) 
        self.fields['timezone'] = timezone
        days = forms.IntegerField(max_value=30,min_value=1,required=True,initial=1)
        self.fields['days'] = days


        show = Submit('show', _('Show'), css_class='btn btn-primary')
        show.field_classes = 'btn btn-success'

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('plan', css_class='form-group col-md-5 mb-2'),
                Column('currency', css_class='form-group col-md-2 mb-2'),
                Column('timezone', css_class='form-group col-md-3 mb-2'),
                Column('days', css_class='form-group col-md-2 mb-1'),
                show,
                css_class='form-row'
            ),
        )