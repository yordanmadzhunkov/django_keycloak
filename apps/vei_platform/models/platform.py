from django.db import models

from .legal import LegalEntity
from .finance_modeling import BankAccount

class PlatformLegalEntity(models.Model):
    entity = models.OneToOneField(LegalEntity, null=False, blank=False, unique=True, on_delete=models.CASCADE)


def platform_bank_accounts(currency):
    my_list = [j.entity.pk for j in PlatformLegalEntity.objects.all()]
    return BankAccount.objects.filter(owner__in=my_list, currency=currency)