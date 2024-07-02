from django.urls import path

from .electricity_prices import ElectricityBillingZoneListAPIView, ElectricityPricePlanListAPIView, ElectricityPricesAPIView
from .hello import HelloView

urlpatterns = [
    path('hello', HelloView.as_view(), name='hello'),
    path('billing_zones', ElectricityBillingZoneListAPIView.as_view(), name='billing_zones'),
    path('plans',   ElectricityPricePlanListAPIView.as_view(), name='price_series'),
    path('prices',  ElectricityPricesAPIView.as_view(), name='prices'),
]

