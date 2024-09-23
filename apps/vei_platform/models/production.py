from django.db import models
from datetime import datetime, timezone
from decimal import Decimal
from .factory import ElectricityFactory
from djmoney.models.fields import Decimal, MoneyField


class ElectricityFactoryProduction(models.Model):
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.CASCADE
    )

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

    energy_in_kwh = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal(0)
    )

    def __str__(self) -> str:
        return "%s %s" % (
            self.start_interval.strftime("%y-%m-%d %h:%m"),
            self.energy_in_kwh,
        )
