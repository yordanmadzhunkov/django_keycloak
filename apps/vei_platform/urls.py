from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

from .views.factory import (
    FactoriesList,
    FactoryDetail,
    FactoriesOfUserList,
    FactoryCreate,
    FactoryEdit,
    FactoryProduction,
    FactoryProductionChart,
)

from .views.dashboard import Dashboard
from .views.home import Home
from .views.profile import Profile, MyProfileUpdate
from .views.legal_entity import (
    view_entity_detail,
    view_my_entity_detail,
    view_entity_platform,
)
from .views.electricity_prices import ElectricityPriceChart, ElectricityPlanView
from .views.scriping_tools import view_scriping_tools
from .views.team import Team
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ElectricityFactorySitemap


sitemaps = {
    "factories": ElectricityFactorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("ht/", include("health_check.urls")),
    path("api/v1/", include("vei_platform.api.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", Home.as_view(), name="home"),
    path("team", Team.as_view(), name="team"),
    path("dashboard", Dashboard.as_view(), name="dashboard"),
    path("profile", MyProfileUpdate.as_view(), name="my_profile"),
    path("profile/<int:pk>", Profile.as_view(), name="user_profile"),
    path("factory/all", FactoriesList.as_view(), name="factories_all"),
    path("factory/", FactoriesOfUserList.as_view(), name="my_factories"),
    path("factory/add", FactoryCreate.as_view(), name="factory_create"),
    path("factory/<int:pk>", FactoryDetail.as_view(), name="view_factory"),
    path("factory/<int:pk>/edit", FactoryEdit.as_view(), name="factory_edit"),
    path(
        "factory/<int:pk>/production",
        FactoryProduction.as_view(),
        name="factory_production",
    ),
    path(
        "factory/production/chart",
        FactoryProductionChart.as_view(),
        name="factory_production_chart",
    ),
    path("price/chart", ElectricityPriceChart.as_view(), name="energy_price_chart"),
    path("price", ElectricityPlanView.as_view(), name="view_electricity_plan"),
    path("entity/<int:pk>", view_entity_detail, name="entity"),
    path("entity/my_entity", view_my_entity_detail, name="my_entity"),
    path("entity/platform", view_entity_platform, name="platform_legal"),
    path("tools/scriping", view_scriping_tools, name="scriping_tools"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
