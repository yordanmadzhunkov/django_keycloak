from django.urls import path

from .electricity_prices import ElectricityBillingZoneListAPIView
from .electricity_prices import ElectricityPricePlanListAPIView
from .electricity_prices import ElectricityPricesAPIView
from .electricity_prices import ElectricityProductionAPIView
from .electricity_prices import ElectricityFactoryAPIView


from .hello import HelloView

urlpatterns = [
    path("hello", HelloView.as_view(), name="hello"),
    path(
        "billing_zones",
        ElectricityBillingZoneListAPIView.as_view(),
        name="billing_zones",
    ),
    path("plans", ElectricityPricePlanListAPIView.as_view(), name="price_series"),
    path("prices", ElectricityPricesAPIView.as_view(), name="prices"),
    path("production", ElectricityProductionAPIView.as_view(), name="production_api"),
    path("factories", ElectricityFactoryAPIView.as_view(), name="my_factories_api"),

]
