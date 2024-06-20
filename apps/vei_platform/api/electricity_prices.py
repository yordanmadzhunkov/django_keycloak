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
    

class ElectricityPricePlanListAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer


class ElectricityPriceSerializer(serializers.ModelSerializer):
    #billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    plan = serializers.SlugRelatedField(slug_field='slug', queryset=ElectricityPricePlan.objects.all())

    class Meta:
        model = ElectricityPrice
        fields = ('start_interval', 'interval_length', 'price', 'plan')
        read_only_fields = ('plan',)




class ElectricityPricesAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityPriceSerializer

    def get_queryset(self):
        return ElectricityPrice.objects.all()
        print(self.request.data)
        plan_slug = self.request.data.get('plan', None)
        if plan:
            plan = ElectricityPricePlan.objects.filter(slug=plan_slug)
            if len(plan) > 0:
                print("Plan is OK")
                return ElectricityPrice.objects.filter(plan=plan)
        return ElectricityPrice.objects.none()






