from django.contrib import admin
from .models import ElectricityFactory, LegalEntity, UserProfile
# Register your models here.

admin.site.register(ElectricityFactory)
admin.site.register(LegalEntity)
admin.site.register(UserProfile)
