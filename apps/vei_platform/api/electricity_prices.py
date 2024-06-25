from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import ElectricityPrice, ElectricityPricePlan, ElectricityBillingZone
from rest_framework.fields import CurrentUserDefault
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db.models import F

#from rest_framework.validators import UniqueForYearValidator

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
    

class ElectricityPricePlanListAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer



class ElectricityPriceSerializer(serializers.ModelSerializer):
    #billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    plan = serializers.SlugRelatedField(slug_field='slug', queryset=ElectricityPricePlan.objects.all())
    start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = ElectricityPrice
        fields = ('start_interval', 'interval_length', 'price', 'plan')
        read_only_fields = ('plan',)
        

    def validate(self, data):
        obj = ElectricityPrice.objects.filter(plan=data['plan'])
        end_interval = data['start_interval'] + timedelta(seconds=data['interval_length'])
        if obj.filter(start_interval__gte=data['start_interval'], start_interval__lt=end_interval).exists():
            raise serializers.ValidationError("Price plan time window overlap")
        if obj.filter(start_interval__gte=data['start_interval']-F('interval_length')).exists():
            raise serializers.ValidationError("Price plan time window overlap")

        return data


class ElectricityPricesAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityPriceSerializer
    #queryset = ElectricityPrice.objects.all()

    def get_queryset(self):
        plan_slug = self.request.query_params.get('plan')
        if plan_slug:
            plan = ElectricityPricePlan.objects.get(slug=plan_slug)            
            return ElectricityPrice.objects.filter(plan=plan)
        return ElectricityPrice.objects.none()






