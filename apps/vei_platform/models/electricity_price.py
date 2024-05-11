from django.db import models

from djmoney.models.fields import Decimal, CurrencyField, MoneyField
from djmoney.money import Money
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, timezone


#class ElectricityPrices(models.Model):
#    kWh = 'kWh'
#    MWh = 'MWh'
#    ELECTRICITY_UNIT_CHOISES = (
#        (kWh, 'kWh'),
#        (MWh, 'MWh'),
#    )
#    code = models.CharField()
#    name = models.CharField()
#    description = models.TextField()
#    currency = CurrencyField(default='EUR')
#    electricity_unit = models.CharField(
#        max_length=3,
#        choices=ELECTRICITY_UNIT_CHOISES,
#        null=False, blank=False,
#        default=kWh,
#    )

class ElectricityBillingZone(models.Model):
    code = models.CharField()
    name = models.CharField()
    description = models.TextField()
    


# Financial data related to the platform
# Evealuation, P/E, available for investment, number of investors

class ElectricityPricePlan(models.Model):
    name = models.CharField(max_length=128)

    start_year = models.IntegerField(
        default=2022,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )
    end_year = models.IntegerField(
        default=2025,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )

    def __str__(self) -> str:
        return self.name

    def get_price(self, month):
        prices = ElectricityPrice.objects.filter(
            plan=self).order_by('-month')
        if len(prices) > 0:
            for price in prices:
                if price.month <= month:
                    return price.number
            price = prices[len(prices)-1]
            return price.number
        return Decimal(0)

    def get_absolute_url(self):
        return "/electricity/%s" % self.pk





class ElectricityPrice(models.Model):
    
    when = models.DateTimeField(blank=False, null=False, db_index=True,default=datetime(year=2024, month=1, day=1, hour=0, minute=0, tzinfo=timezone.utc))
    
    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='BGN',
        default=Decimal(0)
    )

    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)

    def month(self):
        return self.when.date()

    def __str__(self) -> str:
        return "%s @ %.2f - plan = %s" % (str(self.month), self.number,  self.plan.name)