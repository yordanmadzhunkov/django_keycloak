from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

from .views.factory import view_all_factories_paganated, view_factory_production 
from .views.factory import FactoriesList, FactoryDetail
from .views.factory import view_my_factories
from .views.factory import FactoryCreate, FactoryEdit, CampaignCreate, CampaignActive
from .views.dashboard import Dashboard
from .views.home import Home
from .views.profile import Profile, MyProfileUpdate
from .views.legal_entity import view_entity_detail, view_my_entity_detail, view_entity_platform
from .views.electricity_prices import view_electricity_prices
from .views.scriping_tools import view_scriping_tools
from .views.invest import Campaign
from .views.team import Team

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('ht/', include('health_check.urls')),
    
    path('', Home.as_view(), name="home"),
    path('team', Team.as_view(), name='team'),

    path('dashboard', Dashboard.as_view(), name='dashboard'),
    path('profile', MyProfileUpdate.as_view(), name='my_profile'),
    path('profile/<int:pk>', Profile.as_view(), name='user_profile'),

    path('campaign/', FactoriesList.as_view(), name='campaigns'),
    path('campaign/<int:pk>', Campaign.as_view(), name='campaign'),

    path('factory/', view_my_factories, name='my_factories'),
    path('factory/all', view_all_factories_paganated, name='factories_list_all'),

    path('factory/<int:pk>', FactoryDetail.as_view(), name='view_factory'),
    path('factory/add', FactoryCreate.as_view(), name='factory_create'),
    path('factory/<int:pk>/active', CampaignActive.as_view(), name='campaign_active'),
    path('factory/<int:pk>/campaign', CampaignCreate.as_view(), name='campaign_create'),
    path('factory/<int:pk>/edit', FactoryEdit.as_view(), name='factory_edit'),

    path('production/<int:pk>', view_factory_production,
         name='view_factory_production'),
    path('electricity/<int:pk>', view_electricity_prices,
         name='view_electricity_prices'),
    path('entity/<int:pk>', view_entity_detail, name='entity'),
    path('entity/my_entity', view_my_entity_detail, name='my_entity'),
    path('entity/platform', view_entity_platform, name='platform_legal'),
    path('tools/scriping', view_scriping_tools, name='scriping_tools'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
