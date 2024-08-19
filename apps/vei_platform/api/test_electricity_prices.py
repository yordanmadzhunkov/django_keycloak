from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# from rest_framework.test import APIRequestFactory
# from myproject.apps.core.models import Account
# import json
from rest_framework.exceptions import ErrorDetail
# from api.electricity_prices import ElectricityPricesSerializer

from django.contrib.auth.models import User

# from django.contrib.auth import get_user_model
# UserModel = get_user_model()
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


from vei_platform.models.electricity_price import (
    ElectricityPricePlan,
    ElectricityBillingZone,
)
from vei_platform.api.electricity_prices import ElectricityPriceSerializer
from vei_platform.models.electricity_price import ElectricityPrice

from datetime import datetime, timezone
from decimal import Decimal
from djmoney.money import Currency


class ElectricityPriceAPIWithUserTestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="123")
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.user.delete()

    def test_create_electricity_price_plan_with_user(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "MWh",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test plan 1")
        self.assertEqual(response.data["billing_zone"], "BG")
        self.assertEqual(response.data["description"], "Most basic test plan")
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["electricity_unit"], "MWh")
        self.assertEqual(response.data["slug"], "test-plan-1")
        self.assertEqual(response.data["owner"], "testuser")

    def test_create_electricity_price_plan_twice(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "MWh",
        }
        response = self.client.post(url, data, format="json")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test plan 1")
        self.assertEqual(response.data["billing_zone"], "BG")
        self.assertEqual(response.data["description"], "Most basic test plan")
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["electricity_unit"], "MWh")
        self.assertEqual(response.data["slug"], "test-plan-1")
        self.assertEqual(response.data["owner"], "testuser")

        self.assertFalse("pk" in response.data.keys())

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test plan 1")
        self.assertEqual(response.data["billing_zone"], "BG")
        self.assertEqual(response.data["description"], "Most basic test plan")
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["electricity_unit"], "MWh")
        self.assertEqual(response.data["owner"], "testuser")
        self.assertNotEqual(response.data["slug"], "test-plan-1")
        self.assertFalse("pk" in response.data.keys())

    def test_get_electricity_price_plans(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "MWh",
        }
        response = self.client.post(url, data, format="json")
        data = {}
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test plan 1")
        self.assertEqual(response.data[0]["billing_zone"], "BG")
        self.assertEqual(response.data[0]["description"], "Most basic test plan")
        self.assertEqual(response.data[0]["currency"], "EUR")
        self.assertEqual(response.data[0]["electricity_unit"], "MWh")
        self.assertEqual(response.data[0]["slug"], "test-plan-1")
        self.assertEqual(response.data[0]["owner"], "testuser")

    def test_create_electricity_price_plan_wrong_unit(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "dWh",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["electricity_unit"],
            [ErrorDetail(string='"dWh" is not a valid choice.', code="invalid_choice")],
        )


class ElectricityPriceAPITestCases(APITestCase):
    def test_billing_zones_get_objects(self):
        """
        Ensure we have at least one billing zone in data base
        """
        url = reverse("billing_zones")
        data = {}
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 45)
        self.assertEqual(
            self.client.post(url, data, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.put(url, data, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(url, data, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_billing_zones_has_bulgaria(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("billing_zones")
        data = {}
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 45)
        bg_code = {"code": "BG", "name": "Bulgaria"}
        foundBG = False
        for c in response.data:
            if c == bg_code:
                foundBG = True
                break
        self.assertTrue(foundBG)

    def test_get_electricity_price_plan(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        data = {}
        response = self.client.get(url, data, format="json")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_electricity_price_plan_no_access(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "MWh",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_electricity_price_plan_no_user(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse("price_series")
        bg_code = {"code": "BG", "name": "Bulgaria"}
        data = {
            "name": "Test plan 1",
            "billing_zone": bg_code["code"],
            "description": "Most basic test plan",
            "currency": "EUR",
            "electricity_unit": "MWh",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ElectricityPricePriceSeriesAPITestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="123")
        self.client.force_authenticate(self.user)
        self.billing_zone_object = ElectricityBillingZone.objects.filter(code="BG")[0]
        self.plan = ElectricityPricePlan.objects.create(
            name="Day ahead price pac",
            electricity_unit="kWh",
            billing_zone=self.billing_zone_object,
            currency="EUR",
            owner=self.user,
        )
        self.plan.save()

    def tearDown(self):
        self.plan.delete()
        self.user.delete()

    def checkTime(self, year, month, day, hour, minute, resp):
        self.assertEqual(
            datetime(year, month, day, hour, minute, 00, tzinfo=timezone.utc),
            datetime.strptime(resp, "%Y-%m-%dT%H:%M:%S%z"),
        )

    def test_get_price_day_1_hour(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse("prices")
        data = {
            "plan": self.plan.slug,
        }
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 0)

    def valid_data(self):
        return {
            "plan": self.plan.slug,
            "price": "10.19",
            "start_interval": "2024-05-19T11:00+00:00",
            "end_interval": "2024-05-19T12:00+00:00",
        }

    def test_electricity_price_serializer(self):
        """
        Serialize time and price
        """
        data = self.valid_data()
        serializer = ElectricityPriceSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=False))

    def test_create_price_day_1_hour(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse("prices")
        data = {
            "plan": self.plan.slug,
            "price": "10.19",
            "start_interval": "2024-05-19T11:00+02:00",
            "end_interval": "2024-05-19T12:00+02:00",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        self.checkTime(2024, 5, 19, 9, 0, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data["end_interval"])
        self.assertEqual(ElectricityPrice.objects.all().count(), 1)
        p = ElectricityPrice.objects.all().first()
        self.assertEqual(
            datetime(2024, 5, 19, 9, 0, 0, tzinfo=timezone.utc), p.start_interval
        )
        self.assertEqual(
            datetime(2024, 5, 19, 10, 0, 0, tzinfo=timezone.utc), p.end_interval
        )
        self.assertEqual(Decimal("10.19"), p.price.amount)
        self.assertEqual(Currency("EUR"), p.price.currency)

    def test_get_price_day_1_hour(self):
        """
        Get price for specific plan by a slug
        """
        self.test_create_price_day_1_hour()
        url = reverse("prices")
        data = {
            "plan": self.plan.slug,
        }
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plan"], self.plan.slug)
        self.assertEqual(response.data[0]["price"], "10.19")
        self.checkTime(2024, 5, 19, 9, 0, response.data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data[0]["end_interval"])

    def test_get_price_no_user(self):
        """
        Get price for specific plan by a slug without logged user
        """
        self.test_create_price_day_1_hour()
        self.client.logout()
        url = reverse("prices")
        data = {
            "plan": self.plan.slug,
        }
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plan"], self.plan.slug)
        self.assertEqual(response.data[0]["price"], "10.19")
        self.checkTime(2024, 5, 19, 9, 0, response.data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data[0]["end_interval"])

    def test_create_price_no_user(self):
        """
        Create price for specific plan without user
        """
        url = reverse("prices")
        data = self.valid_data()
        self.client.logout()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_create_price_duplicate(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        self.checkTime(2024, 5, 19, 11, 0, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 12, 0, response.data["end_interval"])

        # Second post
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_price_non_overlaping_time_windows(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        d = datetime.strptime(response.data["start_interval"], "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(datetime(2024, 5, 19, 11, 00, 00, tzinfo=timezone.utc), d)
        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T10:00+00:00",
            "end_interval": "2024-05-19T11:00:00+00:00",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T12:00+00:00",
            "end_interval": "2024-05-19T13:00:00+00:00",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_price_overlaping_time_windows_left(self):
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        self.checkTime(2024, 5, 19, 11, 00, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 12, 00, response.data["end_interval"])
        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T10:30+00:00",
            "end_interval": "2024-05-19T11:30:00+00:00",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_price_overlaping_time_windows_right(self):
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        self.checkTime(2024, 5, 19, 11, 00, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 12, 00, response.data["end_interval"])
        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T11:30+00:00",
            "end_interval": "2024-05-19T12:30:00+00:00",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_price_overlaping_time_windows_outer(self):
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        self.checkTime(2024, 5, 19, 11, 00, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 12, 00, response.data["end_interval"])
        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T10:30+00:00",
            "end_interval": "2024-05-19T13:30:00+00:00",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_price_overlaping_time_windows_inner(self):
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        d = datetime.strptime(response.data["start_interval"], "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(datetime(2024, 5, 19, 11, 00, 00, tzinfo=timezone.utc), d)
        d = datetime.strptime(response.data["end_interval"], "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(datetime(2024, 5, 19, 12, 00, 00, tzinfo=timezone.utc), d)

        data = {
            "plan": self.plan.slug,
            "price": "12.12",
            "start_interval": "2024-05-19T11:20+00:00",
            "end_interval": "2024-05-19T11:30:00+00:00",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_price_in_timewindow(self):
        url = reverse("prices")
        data = self.valid_data()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data["plan"], self.plan.slug)
        self.assertEqual(response.data["price"], "10.19")
        d = datetime.strptime(response.data["start_interval"], "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(datetime(2024, 5, 19, 11, 00, 00, tzinfo=timezone.utc), d)
        d = datetime.strptime(response.data["end_interval"], "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(datetime(2024, 5, 19, 12, 00, 00, tzinfo=timezone.utc), d)

        data = {
            "plan": self.plan.slug,
            "start_interval": "2024-05-19T11:20+00:00",
            "end_interval": "2024-05-19T11:30:00+00:00",
        }

        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["price"], "10.19")

        data = {
            "plan": self.plan.slug,
            "start_interval": "2024-05-19T01:20+00:00",
            "end_interval": "2024-05-19T03:30:00+00:00",
        }

        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        data = {
            "plan": self.plan.slug,
        }
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_price_bulk(self):
        """
        Get create a list of price for same plan
        """
        url = reverse("prices")
        data = [
            {
                "plan": self.plan.slug,
                "price": "10.19",
                "start_interval": "2024-05-19T11:00+00:00",
                "end_interval": "2024-05-19T12:00+00:00",
            },
            {
                "plan": self.plan.slug,
                "price": "11.21",
                "start_interval": "2024-05-19T12:00+00:00",
                "end_interval": "2024-05-19T13:00+00:00",
            },
            {
                "plan": self.plan.slug,
                "price": "12.10",
                "start_interval": "2024-05-19T13:00+00:00",
                "end_interval": "2024-05-19T14:00+00:00",
            },
        ]

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["plan"], self.plan.slug)
        self.assertEqual(response.data[1]["plan"], self.plan.slug)
        self.assertEqual(response.data[2]["plan"], self.plan.slug)

        self.assertEqual(response.data[0]["price"], "10.19")
        self.assertEqual(response.data[1]["price"], "11.21")
        self.assertEqual(response.data[2]["price"], "12.10")

        self.checkTime(2024, 5, 19, 11, 00, response.data[0]["start_interval"])
        self.checkTime(2024, 5, 19, 12, 00, response.data[1]["start_interval"])
        self.checkTime(2024, 5, 19, 13, 00, response.data[2]["start_interval"])

        self.checkTime(2024, 5, 19, 12, 00, response.data[0]["end_interval"])
        self.checkTime(2024, 5, 19, 13, 00, response.data[1]["end_interval"])
        self.checkTime(2024, 5, 19, 14, 00, response.data[2]["end_interval"])

    def test_create_price_bulk_one_overlap(self):
        """
        Get create a list of price for same plan
        """
        url = reverse("prices")
        data = [
            {
                "plan": self.plan.slug,
                "price": "10.19",
                "start_interval": "2024-05-19T11:00+00:00",
                "end_interval": "2024-05-19T12:00+00:00",
            },
            {
                "plan": self.plan.slug,
                "price": "11.21",
                "start_interval": "2024-05-19T12:00+00:00",
                "end_interval": "2024-05-19T13:00+00:00",
            },
            {
                "plan": self.plan.slug,
                "price": "12.10",
                "start_interval": "2024-05-19T13:00+00:00",
                "end_interval": "2024-05-19T14:00+00:00",
            },
        ]

        response = self.client.post(url, data[1], format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertGreaterEqual(len(response.data), 3)
        self.assertEqual(response.data[0], {})
        self.assertEqual(
            response.data[1]["non_field_errors"][0], "Price plan time window overlap"
        )
        self.assertEqual(response.data[2], {})

        response = self.client.get(
            path=reverse("prices"),
            data={
                "plan": self.plan.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
