from django.db import models
from django.db.models import Q

from djmoney.models.fields import Decimal, CurrencyField, MoneyField
from djmoney.money import Money
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from datetime import datetime, timezone
from decimal import Decimal

from . import unique_slug_generator


class ElectricityBillingZone(models.Model):
    code = models.CharField(max_length=128, null=False, blank=False, unique=True)
    name = models.CharField(max_length=1024, null=False, blank=False)
    description = models.TextField()

    def __str__(self) -> str:
        return "%s -> %s" % (self.code, self.name)


# Financial data related to the platform
# Evealuation, P/E, available for investment, number of investors
class ElectricityPricePlan(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, null=False, blank=False)  # Ensure unique slugs
    kWh = "kWh"
    MWh = "MWh"
    ELECTRICITY_UNIT_CHOISES = (
        (kWh, "kWh"),
        (MWh, "MWh"),
    )
    billing_zone = models.ForeignKey(
        ElectricityBillingZone, on_delete=models.DO_NOTHING, blank=True, default=None
    )
    description = models.TextField(max_length=1024 * 4, null=False, blank=False)
    currency = CurrencyField(default="EUR")
    electricity_unit = models.CharField(
        max_length=3,
        choices=ELECTRICITY_UNIT_CHOISES,
        null=False,
        blank=False,
        default=kWh,
    )
    owner = models.ForeignKey(
        User, null=True, blank=True, default=None, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return "/electricity/%s" % self.pk

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator(self)  # Handle Unicode characters
        super().save(*args, **kwargs)


class ElectricityPrice(models.Model):
    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)

    start_interval = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        default=datetime(
            year=2024, month=1, day=1, hour=0, minute=0, tzinfo=timezone.utc
        ),
    )
    end_interval = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        default=datetime(
            year=2024, month=1, day=1, hour=1, minute=0, tzinfo=timezone.utc
        ),
    )

    price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="BGN", default=Decimal(0)
    )

    def month(self):
        return self.start_interval.date()

    def __str__(self) -> str:
        return "%s @ %s - plan = %s" % (
            str(self.start_interval),
            str(self.price),
            self.plan.name,
        )
