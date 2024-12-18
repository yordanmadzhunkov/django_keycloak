from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import (
    ElectricityPrice,
    ElectricityPricePlan,
    ElectricityBillingZone,
)
from rest_framework.mixins import UpdateModelMixin
from vei_platform.models.production import (
    ElectricityFactory,
    ElectricityFactoryProduction,
)
from vei_platform.models.schedule import MinPriceCriteria, ElectricityFactorySchedule

from django.db.models import Q

# from rest_framework.validators import UniqueForYearValidator
from djmoney.money import Money

from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.http import Http404


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


class ElectricityPricePlanSerializer(serializers.ModelSerializer):
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
    serializer_class = ElectricityPricePlanSerializer


class ElectricityPricePlanSummarySerializer(serializers.ModelSerializer):
    last_price_start_interval = serializers.SerializerMethodField(
        "get_last_price_start_interval"
    )
    last_gap = serializers.SerializerMethodField("get_last_gap")
    last_overlap = serializers.SerializerMethodField("get_last_overlap")

    def get_last_price_start_interval(self, plan: ElectricityPricePlan):
        prices = ElectricityPrice.objects.filter(plan=plan).order_by("start_interval")
        res = prices.last()
        if res is not None:
            res = res.start_interval
        # self.get_continuous_start_interval(plan)
        return res

    def get_continuous_start_interval(self, plan: ElectricityPricePlan):
        prices = ElectricityPrice.objects.filter(plan=plan).order_by("-start_interval")
        # first = prices.first()
        # if first is not None:
        prev = None
        start = None
        for p in prices:
            if prev is None:
                start = p
                prev = p
                print("Staring iteration in plan = ", plan.name, " last = ", p)
            else:
                if prev.start_interval == p.end_interval:
                    prev = p
                else:
                    if prev.start_interval == p.start_interval:
                        print("         Duplicate found price = ", p, " prev =", prev)
                        prev = p
                    else:
                        print("Break found price = ", p, " prev =", prev)
                        prev = p

        if prev is not None:
            print("Last value found = ", prev, "Fist value = ", start)

    def get_last_gap(self, plan: ElectricityPricePlan):
        prices = ElectricityPrice.objects.filter(plan=plan).order_by("-start_interval")
        prev = None
        for p in prices:
            if prev is None:
                prev = p
            else:
                if prev.start_interval == p.end_interval:
                    prev = p
                else:
                    return [p.end_interval, prev.start_interval]
        return None

    def get_last_overlap(self, plan: ElectricityPricePlan):
        prices = ElectricityPrice.objects.filter(plan=plan).order_by("-start_interval")
        prev = None
        for p in prices:
            if prev is None:
                prev = p
            else:
                if prev.start_interval < p.end_interval:
                    return [
                        p.start_interval,
                        p.end_interval,
                        str(p.price),
                        prev.start_interval,
                        prev.end_interval,
                        str(prev.price),
                    ]
                prev = p

        return None

    class Meta:
        model = ElectricityPricePlan
        fields = (
            "name",
            "currency",
            "electricity_unit",
            "slug",
            "last_price_start_interval",
            "last_gap",
            "last_overlap",
        )
        read_only_fields = (
            "slug",
            "last_price_start_interval",
            "last_gap",
            "last_overlap",
        )

    def save(self, **kwargs):
        self.validated_data["owner"] = self.context["request"].user
        return super().save(**kwargs)


class ElectricityPricePlanSummaryAPIView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityPricePlanSummarySerializer

    def get(self, request, plan, *args, **kwargs):
        instance = get_object_or_404(ElectricityPricePlan, slug=plan)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


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
        overlaping = ElectricityPrice.objects.filter(plan=data["plan"]).filter(
            query_overlapping_intervals
        )
        if overlaping.exists():
            if (
                self.instance is None
                or overlaping.count() > 1
                or self.instance != overlaping[0]
            ):
                raise serializers.ValidationError("Price plan time window overlap")
        amount = data["price"]
        if isinstance(amount, Money):
            amount = data["price"].amount
        data["price"] = Money(amount=amount, currency=data["plan"].currency)
        return super().validate(data)

    def update(self, instance, validated_data):
        instance.start_interval = validated_data.get(
            "start_interval", instance.start_interval
        )
        instance.end_interval = validated_data.get(
            "end_interval", instance.end_interval
        )
        instance.price = validated_data.get("price", instance.price)
        instance.save()
        return instance


class ElectricityPricesAPIView(generics.ListCreateAPIView, UpdateModelMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityPriceSerializer

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

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def get_object(self):
        """
        Returns the object the view is displaying/update
        """
        plan_slug = self.request.data.get("plan")
        start_interval = self.request.data.get("start_interval")
        end_interval = self.request.data.get("end_interval")
        if plan_slug and start_interval and end_interval:
            plan = ElectricityPricePlan.objects.get(slug=plan_slug)
            if plan:
                # print("Plan found = ", plan)
                p = ElectricityPrice.objects.filter(plan=plan)
                p = p.filter(start_interval__gte=start_interval)
                p = p.filter(end_interval__lte=end_interval)
                if p.count() == 1:
                    obj = p[0]
                    # May raise a permission denied
                    self.check_object_permissions(self.request, obj)
                    return obj
        raise Http404("No prices found for given plan and intervals ")


### PRODUCTION ###
from djmoney.contrib.django_rest_framework import MoneyField


class ElectricityProductionSerializer(serializers.ModelSerializer):
    factory = serializers.SlugRelatedField(
        slug_field="slug", queryset=ElectricityFactory.objects.all()
    )
    start_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    end_interval = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    energy_in_kwh = serializers.DecimalField(decimal_places=4, max_digits=14)
    reported_price_per_mwh = MoneyField(
        max_digits=14, decimal_places=2, required=False, default=None
    )

    class Meta:
        model = ElectricityFactoryProduction
        fields = (
            "start_interval",
            "end_interval",
            "energy_in_kwh",
            "factory",
            "reported_price_per_mwh",
            "reported_price_per_mwh_currency",
        )
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


class ElectricityFactoryScheduleSerializer(serializers.ModelSerializer):
    factory = serializers.SlugRelatedField(
        slug_field="slug", queryset=ElectricityFactory.objects.all()
    )

    class Meta:
        model = ElectricityFactorySchedule
        fields = ("start_interval", "end_interval", "working", "factory")
        read_only_fields = ("factory",)


class ElectricityFactoryScheduleAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ElectricityFactoryScheduleSerializer

    def get_queryset(self):
        factory_slug = self.request.query_params.get("factory")
        if factory_slug:
            factory = ElectricityFactory.objects.get(slug=factory_slug)
            start_interval = self.request.query_params.get("start_interval")
            end_interval = self.request.query_params.get("end_interval")
            # print(factory)
            obj = ElectricityFactorySchedule.objects.filter(factory=factory)
            # print(obj)
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
        return ElectricityFactorySchedule.objects.none()

    def create(self, request, *args, **kwargs):
        factory_slug = request.data.get("factory")
        # start_interval = self.request.data.get("start_interval")
        # end_interval = self.request.data.get("end_interval")
        if not factory_slug:
            return Response(
                {"error": "missing `factory` parameter"},
                status=status.HTTP_404_NOT_FOUND,
                headers={},
            )
        factory = ElectricityFactory.objects.get(slug=factory_slug)
        if not factory:
            return Response(
                {"error": "Factory not found slug = '%s' " % factory_slug},
                status=status.HTTP_404_NOT_FOUND,
                headers={},
            )
        return self.create_for_factory(factory)

    def create_for_factory(self, factory: ElectricityFactory, num_days=4):
        data = ElectricityFactorySchedule.generate_schedule(factory, num_days)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        send_notifications(factory, serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_serializer(self, *args, **kwargs):
        # https://medium.com/swlh/efficient-bulk-create-with-django-rest-framework-f73da6af7ddc
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)


from prettytable import PrettyTable
from datetime import datetime


def send_notifications(factory: ElectricityFactory, data):
    if len(data) == 0:
        return
    has_shutdown = False
    tz = factory.get_pytz_timezone()
    tz_name = factory.get_requested_timezone()
    if factory.factory_code is None:
        title = "%s" % factory.name
    else:
        title = "%s %s" % (factory.name, factory.factory_code)
    title = title + " " + tz_name
    table = PrettyTable(["Date", "Time %s" % tz_name, "Working"], title=title)

    for d in data:
        st = datetime.strptime(d["start_interval"], "%Y-%m-%dT%H:%M:%SZ").astimezone(tz)
        et = datetime.strptime(d["end_interval"], "%Y-%m-%dT%H:%M:%SZ").astimezone(tz)
        table.add_row(
            [
                st.date(),
                "%d - %d" % (st.time().hour, et.time().hour),
                "On" if d["working"] else "Off",
            ]
        )

        if not d["working"]:
            has_shutdown = True

    subject = "Wokring schedule for %s" % factory.name
    message = table.get_string()
    sender = "data.intensive99@gmail.com"
    recipeint_list = ["y.madzhunkov@vei-imot.bg"]
    send_mail(
        subject,
        message,
        sender,
        recipeint_list,
        fail_silently=False,
    )
