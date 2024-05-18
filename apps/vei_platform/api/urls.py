from django.urls import path

from .electricity_prices import HelloView, ElectricityBillingZoneListView, ElectricityPricesListView
from .hello import HelloView

urlpatterns = [
    path('hello', HelloView.as_view(), name='hello'),
    path('billing_zones', ElectricityBillingZoneListView.as_view(), name='billing_zones'),
    path('price_series', ElectricityPricesListView.as_view(), name='price_series'),
]

