from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

from .views.factory import view_all_factories_paganated, view_factory_detail, view_factory_production, view_campaign_create, view_campaign_active, view_offered_factories_paganated, view_my_factories, view_add_factory
from .views.dashboard import view_dashboard
from .views.home import view_home
from .views.profile import view_my_profile, view_user_profile
from .views.legal_entity import view_entity_detail, view_my_entity_detail, view_entity_platform
from .views.electricity_prices import view_electricity_prices
from .views.loan import view_bank_loan_detail
from .views.bank_account import view_bank_accounts, view_verify_bank_account, view_deposit_bank_account, view_withdraw_bank_account
from .views.scriping_tools import view_scriping_tools
from .views.invest import view_campaign

urlpatterns = [
    path('', view_home, name="home"),
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('ht/', include('health_check.urls')),
    path('dashboard', view_dashboard, name='dashboard'),
    path('profile', view_my_profile, name='my_profile'),
    path('profile/<int:pk>', view_user_profile, name='user_profile'),
    path('campaign/', view_offered_factories_paganated, name='campaigns'),
    path('campaign/<int:pk>', view_campaign, name='invest_opportunity'),
    path('factory/', view_my_factories, name='my_factories'),
    path('factory/<int:pk>', view_factory_detail, name='view_factory'),
    path('factory/add', view_add_factory, name='view_add_factory'),
    path('factory/<int:pk>/active', view_campaign_active, name='campaign_active'),
    path('factory/<int:pk>/campaign', view_campaign_create, name='campaign_create'),
    path('factory/all', view_all_factories_paganated, name='factories_list_all'),
    path('production/<int:pk>', view_factory_production,
         name='view_factory_production'),
    path('electricity/<int:pk>', view_electricity_prices,
         name='view_electricity_prices'),
    path('entity/<int:pk>', view_entity_detail, name='entity'),
    path('entity/my_entity', view_my_entity_detail, name='my_entity'),
    path('entity/platform', view_entity_platform, name='platform_legal'),
    path('tools/scriping', view_scriping_tools, name='scriping_tools'),
    path('bank_loan/<int:pk>', view_bank_loan_detail, name='bank_loan'),
    
    path('bank_accounts', view_bank_accounts, name='bank_accounts'),
    path('bank_accounts/verify/<int:pk>', view_verify_bank_account, name='verify_bank_account'),
    path('bank_accounts/deposit/<int:pk>', view_deposit_bank_account, name='deposit_bank_account'),
    path('bank_accounts/withdraw/<int:pk>', view_withdraw_bank_account, name='withdraw_bank_account'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
