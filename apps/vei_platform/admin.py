from django.contrib import admin
from .models.factory import ElectricityFactory
from .models.legal import LegalEntity
from .models.profile import UserProfile
# Register your models here.

admin.site.register(ElectricityFactory)
admin.site.register(LegalEntity)
admin.site.register(UserProfile)
