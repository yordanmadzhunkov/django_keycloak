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


from django.db.models import Q


def create_query_for_finding_overlapping_intervals(start_date_column, end_date_column_name, start_dt, end_dt,
                                                   closed_interval=True):
    """
    Creates a query for finding intervals in the Django model which overlap the [start_date, end_date] closed interval.
    It also takes care of the invalid interval case when start date > end date for both stored ones and the input ones.

    :param start_date_column: name of start date column in the model
    :param end_date_column_name: name of end date column in the model
    :param start_dt: start date of the interval to be checked
    :param end_dt: end date of the interval to be checked
    :param closed_interval: closed interval = True means intervals are of the form [start, end],
     otherwise intervals are of the form [start, end). Where ")" means end-value is included and ")" end-value is not
    included.
    :return:
    """

    q_start_dt__gt = f'{start_date_column}__gt'
    q_start_dt__gte = f'{start_date_column}__gte'
    q_start_dt__lt = f'{start_date_column}__lt'
    q_start_dt__lte = f'{start_date_column}__lte'
    q_end_dt__gt = f'{end_date_column_name}__gt'
    q_end_dt__gte = f'{end_date_column_name}__gte'
    q_end_dt__lt = f'{end_date_column_name}__lt'
    q_end_dt__lte = f'{end_date_column_name}__lte'

    q_is_contained = Q(**{q_start_dt__gte: start_dt}) & Q(**{q_end_dt__lte: end_dt})
    q_contains = Q(**{q_start_dt__lte: start_dt}) & Q(**{q_end_dt__gte: end_dt})
    q_slides_before = Q(**{q_start_dt__lt: start_dt}) & Q(**{q_end_dt__lt: end_dt})
    q_slides_after = Q(**{q_start_dt__gt: start_dt}) & Q(**{q_end_dt__gt: end_dt})
    if closed_interval:
        q_slides_before = q_slides_before & Q(**{q_end_dt__gte: start_dt})
        q_slides_after = q_slides_after & Q(**{q_start_dt__lte: end_dt})
    else:
        q_slides_before = q_slides_before & Q(**{q_end_dt__gt: start_dt})
        q_slides_after = q_slides_after & Q(**{q_start_dt__lt: end_dt})

    return q_contains | q_is_contained | q_slides_before | q_slides_after


class ElectricityPriceSerializer(serializers.ModelSerializer):
    #billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    plan = serializers.SlugRelatedField(slug_field='slug', queryset=ElectricityPricePlan.objects.all())
    start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    end_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = ElectricityPrice
        fields = ('start_interval', 'end_interval', 'price', 'plan')
        read_only_fields = ('plan',)
        
 
    def validate(self, data):
        query_obj = create_query_for_finding_overlapping_intervals('start_interval', 'end_interval', data['start_interval'], data['end_interval'], closed_interval=False)
        if ElectricityPrice.objects.filter(plan=data['plan']).filter(query_obj).exists():
            raise serializers.ValidationError("Price plan time window overlap")
        return super().validate(data)



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






