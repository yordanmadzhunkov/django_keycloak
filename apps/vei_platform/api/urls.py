from django.urls import path

from .electricity_prices import ElectricityBillingZoneListAPIView
from .electricity_prices import ElectricityPricePlanListAPIView
from .electricity_prices import ElectricityPricesAPIView
from .electricity_prices import ElectricityProductionAPIView
from .electricity_prices import ElectricityFactoryAPIView
from .electricity_prices import ElectricityFactoryScheduleAPIView
from .electricity_prices import ElectricityPricePlanSummaryAPIView

urlpatterns = [
    path("zones", ElectricityBillingZoneListAPIView.as_view(), name="billing_zones"),
    path("plans", ElectricityPricePlanListAPIView.as_view(), name="plans_api"),
    path(
        "plan/summary",
        ElectricityPricePlanSummaryAPIView.as_view(),
        name="plan_summary_api",
    ),
    path("prices", ElectricityPricesAPIView.as_view(), name="prices"),
    path("production", ElectricityProductionAPIView.as_view(), name="production_api"),
    path("factories", ElectricityFactoryAPIView.as_view(), name="my_factories_api"),
    path("schedule", ElectricityFactoryScheduleAPIView.as_view(), name="schedule_api"),
]
