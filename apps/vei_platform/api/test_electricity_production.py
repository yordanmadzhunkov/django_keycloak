from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.legal import LegalEntity
from vei_platform.models.factory_production import ElectricityFactoryProduction
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

    def test_factories_list_has_my_factory(self):
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
        #print(response.data[0])

    def test_post_production_to_factory(self):
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

