from django.db import models
from datetime import datetime, timezone
from decimal import Decimal
from .factory import ElectricityFactory


class ElectricityFactoryProduction(models.Model):
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING
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


# FACTORY WORKING PLANNING
# class FactoryProductionPlan(models.Model):
#     name = models.CharField(max_length=128)
#     factory = models.ForeignKey(
#         ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING
#     )
#     start_year = models.IntegerField(
#         default=2022, validators=[MaxValueValidator(2050), MinValueValidator(1990)]
#     )
#     end_year = models.IntegerField(
#         default=2025, validators=[MaxValueValidator(2050), MinValueValidator(1990)]
#     )

#     def get_working_hours(self, month):
#         objects = ElectricityFactoryProduction.objects.filter(plan=self)
#         s = objects.filter(month__month=month.month)
#         y = s.filter(month__year=month.year)
#         if len(y) > 0:
#             return s[0].number

#         count = len(s)
#         sum = Decimal(0)
#         for k in s:
#             sum = sum + k.number

#         if len(s) > 0:
#             return sum / count

#         return Decimal(100)

#     def __str__(self) -> str:
#         return self.name

#     def get_absolute_url(self):
#         res = self.factory.get_absolute_url()
#         return res + "/production/%s" % self.pk
