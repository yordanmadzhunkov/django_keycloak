from django.db import models
from .legal import LegalEntity, add_legal_entity
from .profile import get_user_profile
from django.db.models.signals import post_save
from django.conf import settings
from decimal import Decimal
from django.dispatch import receiver

from .restricted_file_field import RestrictedFileField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .timezone_choises import TIMEZONE_CHOICES
from djmoney.models.fields import CurrencyField

import os
from django.db import models

from . import TimeStampMixin
from . import unique_slug_generator
from .electricity_price import ElectricityPricePlan, ElectricityPrice
import pytz


def user_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.manager), filename)


def factory_component_file_upload_directory_path(instance, filename):
    return "documents/factory_{0}/{1}".format(instance.factory.pk, filename)


class ElectricityFactory(TimeStampMixin):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, null=True, blank=False)  # Ensure unique slugs

    # Factory type
    PHOTOVOLTAIC = "FEV"
    WIND_TURBINE = "WIN"
    HYDROPOWER = "HYD"
    BIOMASS = "BIO"
    REN_GAS = "RGS"

    FACTORY_TYPE_CHOISES = (
        (PHOTOVOLTAIC, _("Photovoltaic")),
        (WIND_TURBINE, _("Wind turbine")),
        (HYDROPOWER, _("Hydropower")),
        (BIOMASS, _("Biomass")),
        (REN_GAS, _("Renewable gas")),
    )

    factory_type = models.CharField(
        max_length=3,
        choices=FACTORY_TYPE_CHOISES,
        default=PHOTOVOLTAIC,
    )

    # User that manages the data shown on the platform
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        default=None,
        on_delete=models.DO_NOTHING,
    )

    # info
    location = models.CharField(max_length=100, default=_("Bulgaria"))
    opened = models.DateField(null=True)
    capacity_in_mw = models.DecimalField(default=0, decimal_places=3, max_digits=9)
    image = models.ImageField(
        upload_to=user_image_upload_directory_path, default=None, null=True, blank=True
    )

    # primary owner
    primary_owner = models.ForeignKey(
        LegalEntity, null=True, blank=True, default=None, on_delete=models.SET_NULL
    )

    tax_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        default=None,
    )
    owner_name = models.CharField(max_length=128, default="Unknown")

    factory_code = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        default=None,
    )

    email = models.EmailField(null=True, blank=True, default=None)
    phone = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        default=None,
    )

    plan = models.ForeignKey(
        ElectricityPricePlan, null=True, blank=True, on_delete=models.SET_NULL
    )
    timezone = models.CharField(
        verbose_name="Timezone",
        max_length=50,
        default="UTC",
        choices=TIMEZONE_CHOICES,
    )
    currency = CurrencyField(default="EUR")

    def __str__(self):
        return self.name

    def is_working(self):
        return self.status == self.WORKING

    def is_stopped(self):
        return self.status == self.STOPED

    def get_image_url(self):
        if self.image and hasattr(self.image, "url"):
            return self.image.url
        if self.factory_type == self.PHOTOVOLTAIC:
            return "/static/img/password_img.jpg"
        if self.factory_type == self.WIND_TURBINE:
            return "/static/img/wind-turbine.jpg"
        if self.factory_type == self.HYDROPOWER:
            return "/static/img/wickramanayaka.jpg"
        print("type = " + self.factory_type + "\n")
        return None

    def get_capacity_in_kw(self):
        return self.capacity_in_mw * Decimal(1000)

    def get_absolute_url(self):
        return reverse("view_factory", kwargs={"pk": self.pk})

    def get_manager_profile(self):
        if self.manager:
            return get_user_profile(self.manager)
        else:
            return None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator(self)  # Handle Unicode characters
        super().save(*args, **kwargs)

    def get_requested_timezone(self) -> str:
        requested_timezone = self.timezone
        if requested_timezone is None:
            requested_timezone = "UTC"
        return requested_timezone

    def get_pytz_timezone(self) -> pytz.timezone:
        requested_timezone = self.timezone
        if requested_timezone is None:
            requested_timezone = "UTC"
        tz = pytz.timezone(requested_timezone)
        return tz

    def get_last_prices(self, num_days):
        if self.plan is None:
            return []
        prices = ElectricityPrice.objects.filter(plan=self.plan).order_by(
            "-start_interval"
        )[: num_days * 24]
        return prices[::-1]


def docfile_content_types():
    return "application/pdf"


class ElectricityFactoryComponents(models.Model):
    # Factory type
    PHOTO_PANEL = "PAN"
    INVERTOR = "INV"
    CONNECTOR = "CON"
    OTHER = "OTH"

    COMPONENT_TYPE_CHOISES = (
        (PHOTO_PANEL, _("Photovoltaic Panel")),
        (INVERTOR, _("Invertor")),
        (CONNECTOR, _("Connector")),
        (OTHER, _("Other")),
    )

    name = models.CharField(max_length=128)
    component_type = models.CharField(
        max_length=3,
        choices=COMPONENT_TYPE_CHOISES,
        default=OTHER,
    )
    factory = models.ForeignKey(
        ElectricityFactory,
        null=True,
        blank=True,
        default=None,
        on_delete=models.DO_NOTHING,
    )
    power_in_kw = models.DecimalField(
        null=True, blank=True, default=None, decimal_places=3, max_digits=9
    )
    count = models.IntegerField(default=1)
    docfile = RestrictedFileField(
        upload_to=factory_component_file_upload_directory_path,
        content_types=docfile_content_types(),  # ['application/pdf',],
        max_upload_size=5242880,  # 5 MB
        default=None,
        null=True,
        blank=True,
    )
    description = models.TextField(null=True, blank=True, default=None)

    def __str__(self) -> str:
        return "%s %s kW x %d" % (self.name, self.power_in_kw, self.count)


def _delete_file(path):
    """Deletes file from filesystem."""
    if os.path.isfile(path):
        # print("cleaning " + path)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@receiver(models.signals.post_delete, sender=ElectricityFactoryComponents)
def delete_file(sender, instance, *args, **kwargs):
    """Deletes image files on `post_delete`"""
    if instance.docfile:
        _delete_file(instance.docfile.path)


@receiver(models.signals.pre_save, sender=ElectricityFactoryComponents)
def auto_delete_file_on_change(sender, instance, update_fields, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `ElectricityFactoryComponents` object is updated
    with new file.
    """
    # print(update_fields)
    if not instance.pk:
        return False

    try:
        old_instance = ElectricityFactoryComponents.objects.get(pk=instance.pk)
        old_file = old_instance.docfile
        should_delete = instance.docfile != old_instance.docfile
        if should_delete and old_file:
            _delete_file(old_file.path)
    except ElectricityFactoryComponents.DoesNotExist:
        return False
