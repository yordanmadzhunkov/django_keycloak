from django.urls import path

from .electricity_prices import ElectricityBillingZoneListAPIView, ElectricityPricesListAPIView
from .hello import HelloView

urlpatterns = [
    path('hello', HelloView.as_view(), name='hello'),
    path('billing_zones', ElectricityBillingZoneListAPIView.as_view(), name='billing_zones'),
    path('price_series', ElectricityPricesListAPIView.as_view(), name='price_series'),
]

