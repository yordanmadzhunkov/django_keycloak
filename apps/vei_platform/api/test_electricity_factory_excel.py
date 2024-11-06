from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.production import ElectricityFactoryProduction
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
from django.core import mail
import os
from vei_platform.models.production import process_excel_report


class ElectricityProductionFromExcelWithUserTestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="123")
        self.client.force_authenticate(self.user)
        self.legal_entity = LegalEntity.objects.create(
            native_name="ГОФРИЛО КО ЕООД",
            latin_name="GOFRILO KO EOOD",
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
            name="ФЕЦ КНЕЖА",
            factory_type=ElectricityFactory.PHOTOVOLTAIC,
            manager=self.user,
            primary_owner=self.legal_entity,
            owner_name=self.legal_entity.native_name,
            location="България, голямо село",
            opened=date(2023, 7, 1),
            capacity_in_mw=Decimal("0.2"),
            timezone="Europe/Sofia",
            plan=self.plan,
        )
        self.factory.save()
        self.url = reverse("production_api")

    def tearDown(self):
        self.user.delete()
        self.factory.delete()
        self.legal_entity.delete()

    def test_create_electricity_production_with_user(self):
        """
        Ensure that we can submit a electricity produced in time window
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        excel_filename = dir_path + "/Справка м.07.2024_ГОФРИЛО КО ЕООД.xlsx"
        # print(excel_filename)
        factories_from_excel = process_excel_report(excel_filename)
        factory_kneja = None
        factory_obnova = None
        for factory in factories_from_excel:
            self.assertTrue("factory_name" in factory.keys())
            self.assertTrue("factory_slug" in factory.keys())
            self.assertTrue("timezone" in factory.keys())
            self.assertTrue("factory_id" in factory.keys())
            self.assertTrue("legal_entity" in factory.keys())
            self.assertTrue("month" in factory.keys())
            self.assertTrue("year" in factory.keys())
            self.assertTrue("production_in_kwh" in factory.keys())
            self.assertTrue("prices" in factory.keys())
            self.assertTrue("currency" in factory.keys())

            self.assertEquals(factory["currency"], "BGN")
            self.assertEquals(factory["year"], 2024)
            self.assertEquals(factory["month"], 7)
            if factory["factory_name"] == "ФЕЦ КНЕЖА":
                factory_kneja = factory

            if factory["factory_name"] == "ФЕЦ ОБНОВА":
                factory_obnova = factory

        self.assertNotEqual(factory_kneja, None)
        self.assertNotEqual(factory_obnova, None)
        # print("GO6o!!!")
        # print(factory['factory_slug'])
        self.assertEquals(factory_kneja["factory_slug"], self.factory.slug)
        self.assertEquals(factory_obnova["factory_slug"], None)
        self.assertEquals(factory_kneja["timezone"], "Europe/Sofia")

        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)

        response = self.client.post(
            reverse("production_api"),
            data=factory_kneja["production_in_kwh"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 31 * 24)

        # for p in ElectricityFactoryProduction.objects.filter(factory=self.factory):
        #    print(p)
        # , 'factory_slug', 'timezone', 'factory_id', 'legal_entity', 'month', 'year', 'production_in_kwh', 'prices', 'currency'
        # print(factory.keys())
        # url = self.url

        # response = self.client.post(reverse("production_api"), data=factory_kneja['production_in_kwh'], format="json")
        # self.assertEqual(ElectricityFactoryProduction.objects.count(), 31*24)
        # response = self.client.post(url, data, format="json")

        # self.assertEqual(ElectricityFactoryProduction.objects.count(), 1)
        # self.assertEqual(response.data["factory"], "малката-кофа-за-фотони")
        # self.assertEqual(Decimal(response.data["energy_in_kwh"]), Decimal("10.19"))
        # self.checkTime(2024, 5, 19, 9, 0, response.data["start_interval"])
        # self.checkTime(2024, 5, 19, 10, 0, response.data["end_interval"])
