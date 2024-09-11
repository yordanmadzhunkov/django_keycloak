from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import (
    ElectricityPrice,
    ElectricityPricePlan,
    ElectricityBillingZone,
)
from vei_platform.models.factory_production import (
    ElectricityFactory,
    ElectricityFactoryProduction,
)

from django.db.models import Q

# from rest_framework.validators import UniqueForYearValidator
from djmoney.money import Money


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
    billing_zone = serializers.SlugRelatedField(
        slug_field="code", queryset=ElectricityBillingZone.objects.all()
    )
    owner = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = ElectricityPricePlan
        fields = (
            "name",
            "billing_zone",
            "description",
            "currency",
            "electricity_unit",
            "slug",
            "owner",
        )
        read_only_fields = ("slug", "owner")

    def save(self, **kwargs):
        self.validated_data["owner"] = self.context["request"].user
        return super().save(**kwargs)


class ElectricityPricePlanListAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer


def create_query_for_finding_overlapping_intervals(
    start_date_column, end_date_column_name, start_dt, end_dt, closed_interval=True
):
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

    q_start_dt__gt = f"{start_date_column}__gt"
    q_start_dt__gte = f"{start_date_column}__gte"
    q_start_dt__lt = f"{start_date_column}__lt"
    q_start_dt__lte = f"{start_date_column}__lte"
    q_end_dt__gt = f"{end_date_column_name}__gt"
    q_end_dt__gte = f"{end_date_column_name}__gte"
    q_end_dt__lt = f"{end_date_column_name}__lt"
    q_end_dt__lte = f"{end_date_column_name}__lte"

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
    # billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    plan = serializers.SlugRelatedField(
        slug_field="slug", queryset=ElectricityPricePlan.objects.all()
    )
    start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    end_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = ElectricityPrice
        fields = ("start_interval", "end_interval", "price", "plan")
        read_only_fields = ("plan",)

    def validate(self, data):
        query_overlapping_intervals = create_query_for_finding_overlapping_intervals(
            "start_interval",
            "end_interval",
            data["start_interval"],
            data["end_interval"],
            closed_interval=False,
        )
        if (
            ElectricityPrice.objects.filter(plan=data["plan"])
            .filter(query_overlapping_intervals)
            .exists()
        ):
            raise serializers.ValidationError("Price plan time window overlap")
        amount = data["price"]
        if isinstance(amount, Money):
            amount = data["price"].amount
        data["price"] = Money(amount=amount, currency=data["plan"].currency)
        return super().validate(data)


class ElectricityPricesAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityPriceSerializer
    # queryset = ElectricityPrice.objects.all()

    def get_queryset(self):
        plan_slug = self.request.query_params.get("plan")
        if plan_slug:
            plan = ElectricityPricePlan.objects.get(slug=plan_slug)
            start_interval = self.request.query_params.get("start_interval")
            end_interval = self.request.query_params.get("end_interval")
            obj = ElectricityPrice.objects.filter(plan=plan)
            if start_interval and end_interval:
                query_overlapping_intervals = (
                    create_query_for_finding_overlapping_intervals(
                        "start_interval",
                        "end_interval",
                        start_interval,
                        end_interval,
                        closed_interval=False,
                    )
                )
                obj = obj.filter(query_overlapping_intervals)
            return obj
        return ElectricityPrice.objects.none()

    def get_serializer(self, *args, **kwargs):
        # https://medium.com/swlh/efficient-bulk-create-with-django-rest-framework-f73da6af7ddc
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)


### PRODUCTION ###


class ElectricityProductionSerializer(serializers.ModelSerializer):
    factory = serializers.SlugRelatedField(
        slug_field="slug", queryset=ElectricityFactory.objects.all()
    )
    start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    end_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    energy_in_kwh = serializers.DecimalField(decimal_places=4, max_digits=14)

    class Meta:
        model = ElectricityFactoryProduction
        fields = ("start_interval", "end_interval", "energy_in_kwh", "factory")
        read_only_fields = ("factory",)

    def validate(self, data):
        query_overlapping_intervals = create_query_for_finding_overlapping_intervals(
            "start_interval",
            "end_interval",
            data["start_interval"],
            data["end_interval"],
            closed_interval=False,
        )
        if (
            ElectricityFactoryProduction.objects.filter(factory=data["factory"])
            .filter(query_overlapping_intervals)
            .exists()
        ):
            raise serializers.ValidationError("Factory production time window overlap")
        return super().validate(data)


class ElectricityProductionAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityProductionSerializer

    def get_queryset(self):
        factory_slug = self.request.query_params.get("factory")
        if factory_slug:
            factory = ElectricityFactory.objects.get(slug=factory_slug)
            start_interval = self.request.query_params.get("start_interval")
            end_interval = self.request.query_params.get("end_interval")
            obj = ElectricityFactoryProduction.objects.filter(factory=factory)
            if start_interval and end_interval:
                query_overlapping_intervals = (
                    create_query_for_finding_overlapping_intervals(
                        "start_interval",
                        "end_interval",
                        start_interval,
                        end_interval,
                        closed_interval=False,
                    )
                )
                obj = obj.filter(query_overlapping_intervals)
            return obj
        return ElectricityFactoryProduction.objects.none()

    def get_serializer(self, *args, **kwargs):
        # https://medium.com/swlh/efficient-bulk-create-with-django-rest-framework-f73da6af7ddc
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)


class ElectricityFactorySerializer(serializers.ModelSerializer):
    # billing_zone = serializers.SlugRelatedField(slug_field='code', queryset=ElectricityBillingZone.objects.all())
    # plan = serializers.SlugRelatedField(
    #    slug_field="slug", queryset=ElectricityPricePlan.objects.all()
    # )
    # start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    # end_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = ElectricityFactory
        fields = ("name", "slug", "factory_type")
        read_only_fields = ("name", "slug", "factory_type")


class ElectricityFactoryAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityFactorySerializer

    def get_queryset(self):
        return ElectricityFactory.objects.filter(manager=self.request.user)
