from django.contrib import admin
from .models.factory import ElectricityFactory
from .models.legal import LegalEntity, LegalEntitySources
from .models.profile import UserProfile
from .models.finance_modeling import BankAccount, InvestementInCampaign
from .models.platform import PlatformLegalEntity
# Register your models here.

admin.site.register(ElectricityFactory)
admin.site.register(LegalEntity)
admin.site.register(LegalEntitySources)
admin.site.register(UserProfile)
admin.site.register(BankAccount)
admin.site.register(PlatformLegalEntity)
admin.site.register(InvestementInCampaign)

