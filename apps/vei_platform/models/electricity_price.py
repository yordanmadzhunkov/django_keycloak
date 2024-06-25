from django.db import models

from djmoney.models.fields import Decimal, CurrencyField, MoneyField
from djmoney.money import Money
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, timezone, timedelta
from django.utils.text import slugify
import uuid 
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django.db.models import Q

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
    kWh = 'kWh'
    MWh = 'MWh'
    ELECTRICITY_UNIT_CHOISES = (
        (kWh, 'kWh'),
        (MWh, 'MWh'),
    )
    billing_zone = models.ForeignKey(ElectricityBillingZone, on_delete=models.DO_NOTHING, blank=True, default=None)
    description = models.TextField(max_length=1024*4, null=False, blank=False)
    currency = CurrencyField(default='EUR')
    electricity_unit = models.CharField(
        max_length=3,
        choices=ELECTRICITY_UNIT_CHOISES,
        null=False, blank=False,
        default=kWh,
    )
    owner = models.ForeignKey(User, null=True, blank=True, default=None, on_delete=models.CASCADE)

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


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator(self) # Handle Unicode characters
        super().save(*args, **kwargs)


def unique_slug_generator(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = slugify(instance.name, allow_unicode=True) 
    Klass = instance.__class__ 
    max_length = Klass._meta.get_field('slug').max_length 
    slug = slug[:max_length] 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
    
    if qs_exists: 
        new_slug = "{slug}-{randstr}".format( 
            slug = slug[:max_length-5], randstr = str(uuid.uuid1())[:4]) 
              
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug


class ElectricityPrice(models.Model):
    
    start_interval = models.DateTimeField(blank=False, null=False, db_index=True,
                                default=datetime(year=2024, month=1, day=1, hour=0, minute=0, tzinfo=timezone.utc))
    interval_length = models.IntegerField(default=3600)
    
    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='BGN',
        default=Decimal(0)
    )

    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)


            

    def month(self):
        return self.start_interval.date()

    def __str__(self) -> str:
        return "%s @ %s - plan = %s" % (str(self.start_interval), str(self.price),  self.plan.name)
    
    #def save(self, *args, **kwargs):
        #print("Save this bitch")
    #    if ElectricityPrice.objects.filter(plan = self.plan).count() > 0:
    #    #if self.start_interval and self.start_date < timezone.now().date():
    #        raise ValueError("Duplicate found. Improve this error message")
    #    return super().save(*args, **kwargs)
        