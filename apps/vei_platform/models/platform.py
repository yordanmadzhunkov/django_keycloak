from django.db import models

from .legal import LegalEntity

class PlatformLegalEntity(models.Model):
    entity = models.OneToOneField(LegalEntity, null=False, blank=False, unique=True, on_delete=models.CASCADE)
