from datetime import datetime, timezone
from .factory import ElectricityFactory
from django.db import models
from djmoney.models.fields import Decimal, MoneyField


class ElectricityFactorySchedule(models.Model):
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

    working = models.BooleanField(blank=True, null=True)
    # 1.0 = FULL CAPACITY
    # capacity = models.DecimalField(max_digits=6, decimal_places=4,default=Decimal(1.0))




class MinPriceCriteria(models.Model):
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.CASCADE
    )

    min_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="BGN", default=Decimal(0)
    )
