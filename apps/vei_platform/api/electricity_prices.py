from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import ElectricityPrice, ElectricityPricePlan, ElectricityBillingZone


class ElectricityBillingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityBillingZone
        fields = (
            "code",
            "name",
        )


class ElectricityBillingZoneListAPIView(generics.ListAPIView):
    queryset = ElectricityBillingZone.objects.all()
    serializer_class = ElectricityBillingZoneSerializer



class ElectricityPricesSerializer(serializers.ModelSerializer):
    billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    class Meta:
        model = ElectricityPricePlan
        fields = ('name', 'billing_zone', 'description', 'currency', 'electricity_unit', 'slug')
        read_only_fields = ('slug',)

class ElectricityPricesListAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer


class ElectricityPricesSeriesSerializer(serializers.ModelSerializer):
    billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    class Meta:
        model = ElectricityPrice
        fields = ('start_interval', 'interval_length', 'price', 'currency', 'electricity_unit', 'plan')
        read_only_fields = ('plan',)

class ElectricityPricesSeriesAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    #queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer

    
