from django.contrib import admin
from .models.factory import ElectricityFactory
from .models.legal import LegalEntity, LegalEntitySources
from .models.profile import UserProfile
from .models.finance_modeling import InvestementInCampaign
from .models.team import TeamMember
# Register your models here.

admin.site.register(ElectricityFactory)
admin.site.register(LegalEntity)
admin.site.register(LegalEntitySources)
admin.site.register(UserProfile)
admin.site.register(InvestementInCampaign)
admin.site.register(TeamMember)

