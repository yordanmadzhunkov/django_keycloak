from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import ElectricityPrice, ElectricityPricePlan, ElectricityBillingZone
from rest_framework.fields import CurrentUserDefault
from django.contrib.auth import get_user_model

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
    owner        = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = ElectricityPricePlan
        fields = ('name', 'billing_zone', 'description', 'currency', 'electricity_unit', 'slug', 'owner')
        read_only_fields = ('slug', 'owner')

    def save(self, **kwargs):
        self.validated_data['owner'] = self.context['request'].user
        return super().save(**kwargs)
    

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



    
