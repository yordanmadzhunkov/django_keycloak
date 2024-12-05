from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.legal import LegalEntity
from vei_platform.models.production import ElectricityFactoryProduction
from datetime import date, datetime, timezone
from decimal import Decimal


class ElectricityProductionAPIWithUserTestCases(APITestCase):
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
        self.factory = ElectricityFactory.objects.create(
            name="Малката кофа за фотони",
            factory_type=ElectricityFactory.PHOTOVOLTAIC,
            manager=self.user,
            primary_owner=self.legal_entity,
            owner_name=self.legal_entity.native_name,
            location="България, голямо село",
            opened=date(2023, 7, 1),
            capacity_in_mw=Decimal("0.2"),
        )
        self.factory.save()
        self.url = reverse("production_api")

    def tearDown(self):
        self.user.delete()
        self.factory.delete()

    def checkTime(self, year, month, day, hour, minute, resp):
        self.assertEqual(
            datetime(year, month, day, hour, minute, 00, tzinfo=timezone.utc),
            datetime.strptime(resp, "%Y-%m-%dT%H:%M:%S%z"),
        )

    def test_get_factories_list_of_user(self):
        """
        Get list of factories and check if my factory is there
        """
        url = reverse("my_factories_api")
        data = {}
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Малката кофа за фотони")
        self.assertEqual(response.data[0]["slug"], "малката-кофа-за-фотони")

    def test_create_electricity_production_with_user(self):
        """
        Ensure that we can submit a electricity produced in time window
        """
        data = {
            "factory": "малката-кофа-за-фотони",
            "energy_in_kwh": "10.19",
            "start_interval": "2024-05-19T11:00+02:00",
            "end_interval": "2024-05-19T12:00+02:00",
        }
        url = self.url
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 1)
        self.assertEqual(response.data["factory"], "малката-кофа-за-фотони")
        self.assertEqual(Decimal(response.data["energy_in_kwh"]), Decimal("10.19"))
        self.checkTime(2024, 5, 19, 9, 0, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data["end_interval"])
        # ElectricityFactoryProduction.objects.all().delete()

    def test_create_electricity_production_bulk(self):
        """
        Get create a list of production for same factory
        """
        url = self.url
        data = [
            {
                "factory": "малката-кофа-за-фотони",
                "energy_in_kwh": "44.19",
                "start_interval": "2024-06-19T11:00+00:00",
                "end_interval": "2024-06-19T12:00+00:00",
            },
            {
                "factory": "малката-кофа-за-фотони",
                "energy_in_kwh": "11.21",
                "start_interval": "2024-06-19T12:00+00:00",
                "end_interval": "2024-06-19T13:00+00:00",
            },
            {
                "factory": "малката-кофа-за-фотони",
                "energy_in_kwh": "12.10",
                "start_interval": "2024-06-19T13:00+00:00",
                "end_interval": "2024-06-19T14:00+00:00",
            },
        ]

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[1]["factory"], "малката-кофа-за-фотони")
        self.assertEqual(response.data[2]["factory"], "малката-кофа-за-фотони")

        self.assertEqual(Decimal(response.data[0]["energy_in_kwh"]), Decimal("44.19"))
        self.assertEqual(Decimal(response.data[1]["energy_in_kwh"]), Decimal("11.21"))
        self.assertEqual(Decimal(response.data[2]["energy_in_kwh"]), Decimal("12.10"))

        self.checkTime(2024, 6, 19, 11, 00, response.data[0]["start_interval"])
        self.checkTime(2024, 6, 19, 12, 00, response.data[1]["start_interval"])
        self.checkTime(2024, 6, 19, 13, 00, response.data[2]["start_interval"])

        self.checkTime(2024, 6, 19, 12, 00, response.data[0]["end_interval"])
        self.checkTime(2024, 6, 19, 13, 00, response.data[1]["end_interval"])
        self.checkTime(2024, 6, 19, 14, 00, response.data[2]["end_interval"])

    def test_create_factory_production_duplicate(self):
        """
        Tests if creating a production that overlaps within previously
        created production timewindow leads to error
        """
        data = {
            "factory": "малката-кофа-за-фотони",
            "energy_in_kwh": "12.29",
            "start_interval": "2024-05-19T11:00+02:00",
            "end_interval": "2024-05-19T12:00+02:00",
        }
        url = self.url

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data["factory"], "малката-кофа-за-фотони")
        self.assertEqual(Decimal(response.data["energy_in_kwh"]), Decimal("12.29"))
        self.checkTime(2024, 5, 19, 9, 0, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data["end_interval"])

        # Second post
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0].code, "invalid")
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "Factory production time window overlap",
        )

    def test_get_factory_production(self):
        """
        Tests for errors when creating a production
        """
        data = {
            "factory": "малката-кофа-за-фотони",
            "energy_in_kwh": "12.29",
            "start_interval": "2024-05-19T11:00+02:00",
            "end_interval": "2024-05-19T12:00+02:00",
        }
        url = self.url

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data["factory"], "малката-кофа-за-фотони")
        self.assertEqual(Decimal(response.data["energy_in_kwh"]), Decimal("12.29"))
        self.checkTime(2024, 5, 19, 9, 0, response.data["start_interval"])
        self.checkTime(2024, 5, 19, 10, 0, response.data["end_interval"])

        data = {
            "factory": "малката-кофа-за-фотони",
            "start_interval": "2024-05-19T00:00+00:00",
            "end_interval": "2024-05-19T23:30:00+00:00",
        }

        # Second post
        response = self.client.get(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_factory_production_reported_price_per_mwh(self):
        """
        Tests for errors when creating a production including reproted price
        """
        data = {
            "factory": "малката-кофа-за-фотони",
            "energy_in_kwh": "12.29",
            "reported_price_per_mwh": "103.20",
            "reported_price_per_mwh_currency": "USD",
            "start_interval": "2024-05-19T11:00+02:00",
            "end_interval": "2024-05-19T12:00+02:00",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 1)

        data = {
            "factory": "малката-кофа-за-фотони",
            "start_interval": "2024-05-19T00:00+00:00",
            "end_interval": "2024-05-19T23:30:00+00:00",
        }
        response = self.client.get(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

        self.assertEqual(
            Decimal(response.data[0]["reported_price_per_mwh"]), Decimal("103.2")
        )
        self.assertEqual(response.data[0]["reported_price_per_mwh_currency"], "USD")
