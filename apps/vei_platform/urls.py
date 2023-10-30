from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

from .views.factory import view_factories_list, view_factory_detail, view_factory_production, view_factory_offer_shares
from .views.dashboard import view_dashboard
from .views.home import view_home
from .views.profile import view_my_profile, view_user_profile
from .views.legal_entity import view_entity_detail, view_my_entity_detail, view_entity_platform
from .views.electricity_prices import view_electricity_prices
from .views.loan import view_bank_loan_detail
from .views.bank_account import view_bank_accounts
from .views.scriping_tools import view_scriping_tools

urlpatterns = [
    path('', view_home, name="home"),
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('ht/', include('health_check.urls')),
    path('dashboard', view_dashboard, name='dashboard'),
    path('profile', view_my_profile, name='my_profile'),
    path('profile/<int:pk>', view_user_profile, name='user_profile'),
    path('invest', view_factories_list, name='factories_list'),
    path('factory/<int:pk>', view_factory_detail, name='view_factory'),
    path('factory/offer_shares/<int:pk>', view_factory_offer_shares, name='view_factory_offer_shares'),
    path('production/<int:pk>', view_factory_production,
         name='view_factory_production'),
    path('electricity/<int:pk>', view_electricity_prices,
         name='view_electricity_prices'),
    path('entity/<int:pk>', view_entity_detail, name='entity'),
    path('entity/my_entity', view_my_entity_detail, name='my_entity'),
    path('entity/platform', view_entity_platform, name='platform_legal'),
    path('tools/scriping', view_scriping_tools, name='scriping_tools'),
    path('bank_loan/<int:pk>', view_bank_loan_detail, name='bank_loan'),
    path('bank_accounts_list', view_bank_accounts, name='bank_accounts_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
