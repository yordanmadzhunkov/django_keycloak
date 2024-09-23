from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.legal import LegalEntity
from vei_platform.models.schedule import MinPriceCriteria
from vei_platform.models.electricity_price import (
    ElectricityPrice,
    ElectricityPricePlan,
    ElectricityBillingZone,
)
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from djmoney.money import Money, Currency


class ElectricityProductionScheduleAPIWithUserTestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="123")
        self.client.force_authenticate(self.user)
        self.legal_entity = LegalEntity.objects.create(
            native_name="Нашата малка фирма ЕООД",
            latin_name="Nashta malka firma EOOD",
            legal_form="",
            tax_id="BG389294392",
            founded=date(2022, 2, 2),
            person=False,
        )
        self.legal_entity.save()

        self.billing_zone_object = ElectricityBillingZone.objects.filter(code="BG")[0]
        self.plan = ElectricityPricePlan.objects.create(
            name="Day ahead price pac",
            electricity_unit="kWh",
            billing_zone=self.billing_zone_object,
            currency="EUR",
            owner=self.user,
        )
        self.plan.save()

        self.factory = ElectricityFactory.objects.create(
            name="Малката кофа за фотони",
            factory_type=ElectricityFactory.PHOTOVOLTAIC,
            manager=self.user,
            primary_owner=self.legal_entity,
            owner_name=self.legal_entity.native_name,
            location="България, голямо село",
            opened=date(2023, 7, 1),
            capacity_in_mw=Decimal("0.2"),
            plan=self.plan,
        )
        self.factory.save()

        self.start_time = datetime(2024, 5, 19, 12, 00, 00, tzinfo=timezone.utc)
        prices = [
            Money(20, "EUR"),
            Money(30, "EUR"),
            Money(40, "EUR"),
            Money(50, "EUR"),
            Money(60, "EUR"),
            Money(70, "EUR"),
            Money(80, "EUR"),
            Money(70, "EUR"),
            Money(60, "EUR"),
            Money(50, "EUR"),
            Money(40, "EUR"),
            Money(30, "EUR"),
            Money(120, "EUR"),
            Money(130, "EUR"),
            Money(140, "EUR"),
            Money(150, "EUR"),
            Money(160, "EUR"),
            Money(170, "EUR"),
            Money(180, "EUR"),
            Money(170, "EUR"),
            Money(160, "EUR"),
            Money(150, "EUR"),
            Money(140, "EUR"),
            Money(130, "EUR"),
        ]
        for i in range(24):
            obj = ElectricityPrice.objects.create(
                start_interval=self.start_time + timedelta(hours=i),
                end_interval=self.start_time + timedelta(hours=i + 1),
                price=prices[i],
                plan=self.plan,
            )
            obj.save()

        min_price = Money(77, "EUR")
        obj = MinPriceCriteria.objects.create(factory=self.factory, min_price=min_price)
        obj.save()

        self.url = reverse("schedule_api")

    def tearDown(self):
        self.user.delete()
        self.factory.delete()
        self.legal_entity.delete()

    def checkTime(self, year, month, day, hour, minute, resp):
        self.assertEqual(
            datetime(year, month, day, hour, minute, 00, tzinfo=timezone.utc),
            datetime.strptime(resp, "%Y-%m-%dT%H:%M:%S%z"),
        )

    def test_get_schedule_prior_create(self):
        self.assertEqual(24, ElectricityPrice.objects.filter(plan=self.plan).count())
        data = {
            "factory": self.factory.slug,
            # "start_interval": "2024-05-19T11:20+00:00",
            # "end_interval": "2024-05-19T11:30:00+00:00",
        }
        response = self.client.get(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_schedule(self):
        self.assertEqual(24, ElectricityPrice.objects.filter(plan=self.plan).count())
        data = {
            "factory": self.factory.slug,
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_response(response.data)

    def test_get_schedule_after_create(self):
        self.test_create_schedule()
        data = {
            "factory": self.factory.slug,
            # "start_interval": "2024-05-19T11:20+00:00",
            # "end_interval": "2024-05-19T11:30:00+00:00",
        }
        response = self.client.get(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_response(response.data)

    def check_response(self, data):
        self.assertEqual(len(data), 24)
        self.assertEqual(data[0]["working"], False)
        self.assertEqual(data[1]["working"], False)
        self.assertEqual(data[2]["working"], False)
        self.assertEqual(data[3]["working"], False)
        self.assertEqual(data[4]["working"], False)
        self.assertEqual(data[5]["working"], False)
        self.assertEqual(data[6]["working"], True)
        self.assertEqual(data[7]["working"], False)
        self.assertEqual(data[8]["working"], False)
        self.assertEqual(data[9]["working"], False)
        self.assertEqual(data[10]["working"], False)
        self.assertEqual(data[11]["working"], False)
        self.assertEqual(data[12]["working"], True)
        self.assertEqual(data[13]["working"], True)
        self.assertEqual(data[14]["working"], True)
        self.assertEqual(data[15]["working"], True)
        self.assertEqual(data[16]["working"], True)
        self.assertEqual(data[17]["working"], True)
        self.assertEqual(data[18]["working"], True)
        self.assertEqual(data[19]["working"], True)
        self.assertEqual(data[21]["working"], True)
        self.assertEqual(data[22]["working"], True)
        self.assertEqual(data[23]["working"], True)

        for i in range(24):
            self.assertEqual(data[i]["factory"], "малката-кофа-за-фотони")

        self.checkTime(2024, 5, 19, 12, 0, data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 13, 0, data[1]["start_interval"])
        self.checkTime(2024, 5, 19, 14, 0, data[2]["start_interval"])
        self.checkTime(2024, 5, 19, 15, 0, data[3]["start_interval"])
        self.checkTime(2024, 5, 19, 16, 0, data[4]["start_interval"])
        self.checkTime(2024, 5, 19, 17, 0, data[5]["start_interval"])
        self.checkTime(2024, 5, 19, 18, 0, data[6]["start_interval"])
        self.checkTime(2024, 5, 19, 19, 0, data[7]["start_interval"])
        self.checkTime(2024, 5, 19, 20, 0, data[8]["start_interval"])
        self.checkTime(2024, 5, 19, 21, 0, data[9]["start_interval"])
        self.checkTime(2024, 5, 19, 22, 0, data[10]["start_interval"])
        self.checkTime(2024, 5, 19, 23, 0, data[11]["start_interval"])
        self.checkTime(2024, 5, 20, 0, 0, data[12]["start_interval"])
        self.checkTime(2024, 5, 20, 1, 0, data[13]["start_interval"])
        self.checkTime(2024, 5, 20, 2, 0, data[14]["start_interval"])
        self.checkTime(2024, 5, 20, 3, 0, data[15]["start_interval"])
        self.checkTime(2024, 5, 20, 4, 0, data[16]["start_interval"])
        self.checkTime(2024, 5, 20, 5, 0, data[17]["start_interval"])
        self.checkTime(2024, 5, 20, 6, 0, data[18]["start_interval"])
        self.checkTime(2024, 5, 20, 7, 0, data[19]["start_interval"])
        self.checkTime(2024, 5, 20, 8, 0, data[20]["start_interval"])
        self.checkTime(2024, 5, 20, 9, 0, data[21]["start_interval"])
        self.checkTime(2024, 5, 20, 10, 0, data[22]["start_interval"])
        self.checkTime(2024, 5, 20, 11, 0, data[23]["start_interval"])

        self.checkTime(2024, 5, 19, 13, 0, data[0]["end_interval"])
        self.checkTime(2024, 5, 19, 14, 0, data[1]["end_interval"])
        self.checkTime(2024, 5, 19, 15, 0, data[2]["end_interval"])
        self.checkTime(2024, 5, 19, 16, 0, data[3]["end_interval"])
        self.checkTime(2024, 5, 19, 17, 0, data[4]["end_interval"])
        self.checkTime(2024, 5, 19, 18, 0, data[5]["end_interval"])
        self.checkTime(2024, 5, 19, 19, 0, data[6]["end_interval"])
        self.checkTime(2024, 5, 19, 20, 0, data[7]["end_interval"])
        self.checkTime(2024, 5, 19, 21, 0, data[8]["end_interval"])
        self.checkTime(2024, 5, 19, 22, 0, data[9]["end_interval"])
        self.checkTime(2024, 5, 19, 23, 0, data[10]["end_interval"])
        self.checkTime(2024, 5, 20, 0, 0, data[11]["end_interval"])
        self.checkTime(2024, 5, 20, 1, 0, data[12]["end_interval"])
        self.checkTime(2024, 5, 20, 2, 0, data[13]["end_interval"])
        self.checkTime(2024, 5, 20, 3, 0, data[14]["end_interval"])
        self.checkTime(2024, 5, 20, 4, 0, data[15]["end_interval"])
        self.checkTime(2024, 5, 20, 5, 0, data[16]["end_interval"])
        self.checkTime(2024, 5, 20, 6, 0, data[17]["end_interval"])
        self.checkTime(2024, 5, 20, 7, 0, data[18]["end_interval"])
        self.checkTime(2024, 5, 20, 8, 0, data[19]["end_interval"])
        self.checkTime(2024, 5, 20, 9, 0, data[20]["end_interval"])
        self.checkTime(2024, 5, 20, 10, 0, data[21]["end_interval"])
        self.checkTime(2024, 5, 20, 11, 0, data[22]["end_interval"])
        self.checkTime(2024, 5, 20, 12, 0, data[23]["end_interval"])

    def test_get_schedule_in_timewindow(self):
        self.test_create_schedule()
        data = {
            "factory": self.factory.slug,
            "start_interval": "2024-05-19T15:20+00:00",
            "end_interval": "2024-05-19T15:30:00+00:00",
        }

        response = self.client.get(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[0]["working"], False)
        self.checkTime(2024, 5, 19, 15, 0, response.data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 16, 0, response.data[0]["end_interval"])

        data = {
            "factory": self.factory.slug,
            "start_interval": "2024-05-19T12:00+00:00",
            "end_interval": "2024-05-19T15:30:00+00:00",
        }

        response = self.client.get(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        self.assertEqual(response.data[0]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[1]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[2]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[3]["factory"], "малката-кофа-за-фотони")

        self.assertEqual(response.data[0]["working"], False)
        self.assertEqual(response.data[1]["working"], False)
        self.assertEqual(response.data[2]["working"], False)
        self.assertEqual(response.data[3]["working"], False)

        self.checkTime(2024, 5, 19, 12, 0, response.data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 13, 0, response.data[1]["start_interval"])
        self.checkTime(2024, 5, 19, 14, 0, response.data[2]["start_interval"])
        self.checkTime(2024, 5, 19, 15, 0, response.data[3]["start_interval"])

        self.checkTime(2024, 5, 19, 13, 0, response.data[0]["end_interval"])
        self.checkTime(2024, 5, 19, 14, 0, response.data[1]["end_interval"])
        self.checkTime(2024, 5, 19, 15, 0, response.data[2]["end_interval"])
        self.checkTime(2024, 5, 19, 16, 0, response.data[3]["end_interval"])
