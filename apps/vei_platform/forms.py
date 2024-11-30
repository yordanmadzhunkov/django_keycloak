from django import forms
from .models.factory import (
    ElectricityFactory,
    ElectricityFactoryComponents,
    docfile_content_types,
)
from .models.schedule import MinPriceCriteria
from .models.legal import LegalEntity


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field, HTML
from .custom_layout_object import Formset


import re
from django.conf import settings
from django.utils import formats
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from .models.timezone_choises import TIMEZONE_CHOICES
from .settings.base import CURRENCY_CHOICES


class BootstrapDatePicker(forms.DateInput):
    format_re = re.compile(r"(?P<part>%[bBdDjmMnyY])")

    def __init__(self, attrs=None, format=None):
        """
        for a list of useful attributes see:
        http://bootstrap-datepicker.readthedocs.io/en/latest/options.html

        Most options can be provided via data-attributes. An option can be
        converted to a data-attribute by taking its name, replacing each
        uppercase letter with its lowercase equivalent preceded by a dash, and
        prepending 'data-date-' to the result. For example, startDate would be
        data-date-start-date, format would be data-date-format, and
        daysOfWeekDisabled would be data-date-days-of-week-disabled.
        """
        # final_attrs provides:
        # - data-provide: apply datepicker to inline created inputs
        # - data-date-language: apply the current language
        # - data-date-format: apply the current format for dates
        final_attrs = {
            "data-provide": "datepicker",
            "data-date-language": get_language(),
            "data-date-format": self.get_date_format(format=format),
            "data-date-autoclose": "true",
            "data-date-clear-btn": "true",
            "data-date-today-btn": "linked",
            "data-date-today-highlight": "true",
        }
        if attrs is not None:
            classes = attrs.get("class", "").split(" ")
            classes.append("datepicker")
            attrs["class"] = " ".join(classes)
            final_attrs.update(attrs)
        super(BootstrapDatePicker, self).__init__(attrs=final_attrs, format=format)

    def get_date_format(self, format=None):
        format_map = {
            "%d": "dd",
            "%j": "d",
            "%m": "mm",
            "%n": "m",
            "%y": "yy",
            "%Y": "yyyy",
            "%b": "M",
            "%B": "MM",
        }
        if format is None:
            format = formats.get_format(self.format_key)[0]
        return re.sub(self.format_re, lambda x: format_map[x.group()], format)


class LegalEntityForm(forms.ModelForm):
    class Meta:
        model = LegalEntity
        fields = "__all__"
        exclude = ["legal_form", "person"]
        labels = {
            "founded": _("Birth date"),
            "tax_id": _("EGN"),
            "native_name": _("Full name"),
            "latin_name": _("Full name using latin"),
        }
        widgets = {
            "founded": BootstrapDatePicker(
                attrs={"class": "form-control", "title": _("Birthday")},
            ),
            "tax_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "pattern": "[0-9\.]+",
                    "style": "width:30ch",
                    "title": _("Enter numbers Only"),
                }
            ),
            "native_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "style": "width:50ch",
                }
            ),
            "latin_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "style": "width:50ch",
                }
            ),
        }


class NumberPerMonthForm(forms.Form):
    number = forms.CharField(
        initial=None,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "pattern": "[0-9\.]+",
                "style": "width:9ch",
                "title": _("Enter numbers Only"),
            }
        ),
    )
    month = forms.DateField(widget=forms.HiddenInput(), required=True)


class UserProfileForm(forms.Form):
    avatar = forms.ImageField(
        initial=None,
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control form-control-user",
                "onchange": "showImage(this);",
            }
        ),
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "textinput form-control  form-control-user"}
        ),
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "textinput form-control  form-control-user"}
        ),
    )
    timezone = forms.TypedChoiceField(
        choices=TIMEZONE_CHOICES,
        label=_("Timezone"),
        coerce=str,
    )

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].label = _("First name")
        self.fields["last_name"].label = _("Last name")
        self.fields["avatar"].label = _("Avatar")
        self.fields["timezone"].label = _("Timezone")


class FactoryScriperForm(forms.Form):
    page_number = forms.CharField(
        initial=None,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "pattern": "[0-9\.]+",
                "style": "width:9ch",
                "title": _("Enter numbers Only"),
            }
        ),
    )
    tax_id = forms.CharField(
        initial=None,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "pattern": "[0-9\.]+",
                "style": "width:9ch",
                "title": _("Enter numbers Only"),
            }
        ),
    )


class SearchForm(forms.Form):
    search_text = forms.CharField(
        initial=None,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "style": "width:30ch",
                "title": _("Text to search"),
            }
        ),
    )


class LoiginOrRegisterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(LoiginOrRegisterForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        authenticate = Submit("authenticate", _("Login or Register"))
        authenticate.field_classes = "btn btn-success btn-block"
        self.helper.layout = Layout(Row(authenticate))


class CustomImageField(Field):
    template = "layout/image_thumbnail.html"


class ElectricityFactoryComponentsForm(forms.ModelForm):
    class Meta:
        model = ElectricityFactoryComponents
        fields = (
            "component_type",
            "power_in_kw",
            "count",
            "name",
            "description",
            "docfile",
        )
        labels = {
            "component_type": _("Component type"),
            "name": _("Name"),
            "power_in_kw": _("Power [kW]"),
            "count": _("Count"),
            "docfile": _("Document file [pdf]"),
            "description": _("Description"),
        }
        docfile = forms.ClearableFileInput(
            attrs={
                "accept": docfile_content_types(),
                "class": "form-control",
            }
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "power_in_kw": forms.NumberInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "count": forms.NumberInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "docfile": docfile,
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "cols": 120,
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
        fields = "__all__"
        exclude = ["manager", "primary_owner", "slug"]
        labels = {
            "name": _("Factory name"),
            "location": _("Location"),
            "opened": _("Opened"),
            "capacity_in_mw": _("Capacity [MW]"),
            "tax_id": _("TAX ID"),
            "owner_name": _("Legal entity owning the factory"),
            "factory_type": _("Energy source type"),
            "image": _("Image"),
            "factory_code": _("Factory code"),
            "email": _("Email"),
            "phone": _("Phone"),
        }

        widgets = {
            "opened": BootstrapDatePicker(
                attrs={
                    "class": "form-control",
                    "title": "Date of transaction",
                    "style": "width:18ch",
                    "data-date-autoclose": "true",
                    "data-date-clear-btn": "false",
                    "data-date-today-btn": "linked",
                    "data-date-today-highlight": "true",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(FactoryModelForm, self).__init__(*args, **kwargs)

        FACTORY_TYPE_CHOISES = (
            (ElectricityFactory.PHOTOVOLTAIC, "ФЕЦ"),
            (ElectricityFactory.WIND_TURBINE, "ВтЕЦ"),
            (ElectricityFactory.HYDROPOWER, "ВЕЦ"),
            (ElectricityFactory.BIOMASS, "БиоЕЦ"),
            (ElectricityFactory.REN_GAS, "БиоГЕЦ"),
        )

        factory_type = forms.TypedChoiceField(
            choices=FACTORY_TYPE_CHOISES, label=_("Type energy source"), coerce=str
        )
        self.fields["factory_type"] = factory_type
        currency = forms.TypedChoiceField(
            choices=CURRENCY_CHOICES, label=_("Currency"), coerce=str
        )
        self.fields["currency"] = currency
        for key, value in self.Meta.labels.items():
            self.fields[key].label = _(value)
        save = Submit("save", _("Save"), css_class="btn btn-primary")
        save.field_classes = "btn btn-success"
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("factory_type", css_class="form-group col-md-2 mb-0"),
                Column("name", css_class="form-group col-md-10 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("opened", css_class="form-group col-md-2 mb-0"),
                Column("capacity_in_mw", css_class="form-group col-md-2 mb-0"),
                Column("location", css_class="form-group col-md-8 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("factory_code", css_class="form-group col-md-4 mb-0"),
                Column("email", css_class="form-group col-md-4 mb-0"),
                Column("phone", css_class="form-group col-md-4 mb-0"),
            ),
            Row(
                Column("owner_name", css_class="form-group col-md-8 mb-0"),
                Column("tax_id", css_class="form-group col-md-4 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("plan", css_class="form-group col-md-5 mb-2"),
                Column("currency", css_class="form-group col-md-2 mb-2"),
                Column("timezone", css_class="form-group col-md-3 mb-2"),
            ),
            Row(
                Column(CustomImageField("image"), css_class="form-group col-md-12"),
                css_class="form-row",
            ),
            HTML("<h2>" + _("Details about the factory") + "</h2>"),
            Formset("formset", "formset_helper"),
            save,
        )


class ElectricityPlanForm(forms.Form):

    def __init__(
        self, plans, initial_timezone=None, initial_plan=None, *args, **kwargs
    ):
        super(ElectricityPlanForm, self).__init__(*args, **kwargs)
        choices = []
        for plan in plans:
            choices.append((plan.slug, plan.name))
        plan_field = forms.TypedChoiceField(
            choices=choices,
            label=_("Plan"),
            coerce=str,
            initial=initial_plan,
        )
        self.fields["plan"] = plan_field

        currency = forms.TypedChoiceField(
            choices=CURRENCY_CHOICES, label=_("Currency"), coerce=str
        )
        self.fields["currency"] = currency

        timezone = forms.TypedChoiceField(
            choices=TIMEZONE_CHOICES,
            label=_("Timezone"),
            initial=initial_timezone,
            coerce=str,
        )
        self.fields["timezone"] = timezone
        days = forms.IntegerField(max_value=90, min_value=1, required=True, initial=3)
        self.fields["days"] = days

        show = Submit("show", _("Show"), css_class="btn btn-primary")
        show.field_classes = "btn btn-success"

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("plan", css_class="form-group col-md-5 mb-2"),
                Column("currency", css_class="form-group col-md-2 mb-2"),
                Column("timezone", css_class="form-group col-md-3 mb-2"),
                Column("days", css_class="form-group col-md-2 mb-1"),
                show,
                css_class="form-row",
            ),
        )

from datetime import datetime, timedelta

class TimeWindowDaysForm(forms.Form):

    days = forms.IntegerField(max_value=90, min_value=1, required=True, initial=7)    
    start_date = forms.DateTimeField(
        #input_formats=['%Y-%M-%D'],
        widget=BootstrapDatePicker(
                attrs={
                    "class": "form-control col-md-12 mb-12",
                    "title": "Date of transaction",
                    "style": "width:18ch",
                    "data-date-autoclose": "true",
                    "data-date-clear-btn": "false",
                    "data-date-today-btn": "linked",
                    "data-date-today-highlight": "true",
                }
            ),
    )

    def get_start_date():
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return today - timedelta(days=90)

    def __init__(
        self, *args, **kwargs
    ):
        kwargs.update( initial = { 'start_date': TimeWindowDaysForm.get_start_date() } )

        super(TimeWindowDaysForm, self).__init__(*args, **kwargs)
        show = Submit("show", _("Show"), css_class="btn btn-primary")
        show.field_classes = "btn btn-success"
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("start_date"),#, css_class="form-group col-md-6 mb-6"),
                Column("days", css_class="form-group col-md-5 mb-5"),
                show,
                css_class="form-row",
            ),
        )



class FactoryScheduleForm(forms.ModelForm):
    class Meta:
        model = MinPriceCriteria
        fields = ("min_price",)
        labels = {
            "min_price": _("Min price"),
        }

    def __init__(self, *args, **kwargs):
        super(FactoryScheduleForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.form_show_labels = True
        for key, value in self.Meta.labels.items():
            self.fields[key].label = _(value)

        save = Submit("save", _("Save"), css_class="btn btn-primary")
        save.field_classes = "btn btn-primary"

        generate = Submit("generate", _("Generate"), css_class="btn btn-success")
        generate.field_classes = "btn btn-success"

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("min_price", css_class="form-group"),
                # Column("currency", css_class="form-group col-md-2 mb-2"),
                save,
                generate,
                css_class="form-row",
            ),
        )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator


class MaxSizeValidator(MaxValueValidator):
    def __call__(self, value):
        # get the file size as cleaned value
        cleaned = self.clean(value.size)
        message = _("The file %s exceed the maximum size of %d MB.") % (
            value.name,
            self.limit_value,
        )

        if self.compare(
            cleaned, self.limit_value * 1024 * 1024
        ):  # convert limit_value from MB to Bytes
            raise ValidationError(message, code=self.code, params=None)


class UploadFileForm(forms.Form):
    # file = forms.FileField()
    files = MultipleFileField(validators=[MaxSizeValidator(6)])

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_show_labels = True

        upload = Submit("upload", _("Upload"), css_class="btn btn-primary")
        upload.field_classes = "btn btn-primary"

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("files", css_class="form-group"),
                css_class="form-row",
            ),
            Row(
                upload,
                css_class="form-row",
            ),
        )
