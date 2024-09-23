from datetime import datetime, timezone
from .factory import ElectricityFactory
from .electricity_price import ElectricityPrice
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

    def generate_schedule(factory: ElectricityFactory, num_prices=24):
        if not factory:
            return []
        plan = factory.plan
        if not plan:
            return []
        criteria = MinPriceCriteria.objects.filter(factory=factory).first()
        prices = ElectricityPrice.objects.filter(plan=plan).order_by("-start_interval")[
            :num_prices
        ]
        schedule = ElectricityFactorySchedule.objects.filter(factory=factory)
        schedule_for_creation = []
        for p in prices:
            s = schedule.filter(start_interval=p.start_interval)
            if len(s) == 0:
                schedule_for_creation.append(
                    {
                        "factory": factory.slug,
                        "start_interval": p.start_interval,
                        "end_interval": p.end_interval,
                        "working": p.price >= criteria.min_price,
                    }
                )
            else:
                break
        schedule_for_creation = schedule_for_creation[::-1]
        return schedule_for_creation


class MinPriceCriteria(models.Model):
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.CASCADE
    )

    min_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="BGN", default=Decimal(0)
    )
