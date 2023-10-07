from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from .views import view_factories_list, view_dashboard, view_home, view_my_profile, view_user_profile, view_factory_detail, view_entity_detail, view_factory_production, view_electricity_prices, view_bank_loan_detail

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
    path('production/<int:pk>', view_factory_production,
         name='view_factory_production'),
    path('electricity/<int:pk>', view_electricity_prices,
         name='view_electricity_prices'),
    path('entity/<int:pk>', view_entity_detail, name='entity'),
    path('bank_loan/<int:pk>', view_bank_loan_detail, name='bank_loan'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
