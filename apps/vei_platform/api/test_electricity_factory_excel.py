from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.production import ElectricityFactoryProduction
from vei_platform.models.production import process_excel_report
from vei_platform.models.legal import LegalEntity
from vei_platform.models.electricity_price import (
    ElectricityPrice,
    ElectricityPricePlan,
    ElectricityBillingZone,
)
from datetime import date, datetime, timezone
from decimal import Decimal

import os


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
            electricity_unit="MWh",
            billing_zone=self.billing_zone_object,
            currency="BGN",
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
            factory_code="32Z140000211335I",
        )
        self.factory.save()

        self.factory2 = ElectricityFactory.objects.create(
            name="ФЕЦ ОБНОВА",
            factory_type=ElectricityFactory.PHOTOVOLTAIC,
            manager=self.user,
            primary_owner=self.legal_entity,
            owner_name=self.legal_entity.native_name,
            location="България, голямо село",
            opened=date(2022, 7, 1),
            capacity_in_mw=Decimal("0.4"),
            timezone="Europe/Sofia",
            plan=self.plan,
            factory_code="32Z140000237585R",
        )
        self.factory2.save()
        self.url = reverse("production_api")

    def tearDown(self):
        self.user.delete()
        self.factory.delete()
        self.factory2.delete()
        self.legal_entity.delete()

    def checkTime(self, year, month, day, hour, minute, resp):
        self.assertEqual(
            datetime(year, month, day, hour, minute, 00, tzinfo=timezone.utc),
            datetime.strptime(resp, "%Y-%m-%dT%H:%M:%S%z"),
        )

    def check_processed_report_keys(self, factories_from_excel):
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

    def test_create_electricity_production_with_user(self):
        """
        Ensure that we can submit a electricity produced in time window
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        excel_filename = dir_path + "/Справка м.07.2024_ГОФРИЛО КО ЕООД.xlsx"
        factories_from_excel = process_excel_report(excel_filename)
        self.check_processed_report_keys(factories_from_excel)
        factory_kneja = None
        factory_obnova = None
        for factory in factories_from_excel:
            self.assertEquals(factory["currency"], "BGN")
            self.assertEquals(factory["year"], 2024)
            self.assertEquals(factory["month"], 7)
            if factory["factory_name"] == "ФЕЦ КНЕЖА":
                factory_kneja = factory

            if factory["factory_name"] == "ФЕЦ ОБНОВА":
                factory_obnova = factory

        self.assertNotEqual(factory_kneja, None)
        self.assertNotEqual(factory_obnova, None)

        self.assertEquals(factory_kneja["factory_slug"], self.factory.slug)
        self.assertEquals(factory_obnova["factory_slug"], self.factory2.slug)
        self.assertEquals(factory_kneja["timezone"], "Europe/Sofia")
        self.assertEquals(factory_obnova["timezone"],  "Europe/Sofia")


        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)

        response = self.client.post(
            reverse("production_api"),
            data=factory_kneja["production_in_kwh"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 31 * 24)

    def test_create_electricity_production_with_user_and_daylight_change(self):
        """
        Ensure that we can submit a report file with changing daylight saving time
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        excel_filename = dir_path + "/Справка м.10.2024_ГОФРИЛО КО ЕООД.xlsx"
        factories_from_excel = process_excel_report(excel_filename)
        self.check_processed_report_keys(factories_from_excel)
        factory_kneja = None
        factory_obnova = None
        for factory in factories_from_excel:
            self.assertEquals(factory["currency"], "BGN")
            self.assertEquals(factory["year"], 2024)
            self.assertEquals(factory["month"], 10)
            if factory["factory_name"] == "ФЕЦ КНЕЖА":
                factory_kneja = factory

            if factory["factory_name"] == "ФЕЦ ОБНОВА":
                factory_obnova = factory

        self.assertNotEqual(factory_kneja, None)
        self.assertNotEqual(factory_obnova, None)

        self.assertEquals(factory_kneja["factory_slug"], self.factory.slug)
        self.assertEquals(factory_obnova["factory_slug"], self.factory2.slug)
        self.assertEquals(factory_kneja["timezone"], "Europe/Sofia")

        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)
        # print(factory_kneja["production_in_kwh"][38])
        response = self.client.post(
            reverse("production_api"),
            data=factory_kneja["production_in_kwh"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 31 * 24 + 1)
        ps = ElectricityFactoryProduction.objects.filter(factory=self.factory).order_by(
            "start_interval"
        )
        self.assertEqual(ps[1 * 24 + 7 + 0].energy_in_kwh, Decimal("1.5"))
        self.assertEqual(ps[26 * 24 + 25 + 0].energy_in_kwh, Decimal("0"))
        self.assertEqual(ps[30 * 24 + 16 + 1].energy_in_kwh, Decimal("4"))

        # for i in range(24):
        #    print(ps[24 + i])

    def test_create_electricity_production_from_old_report_with_user(self):
        """
        Ensure that we can submit a electricity produced in time window
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        excel_filename = dir_path + "/03-24_ГОФРИЛО КО ЕООД.xlsx"
        factories_from_excel = process_excel_report(excel_filename)
        # print(factories_from_excel)
        self.assertEquals(2, len(factories_from_excel))
        self.check_processed_report_keys(factories_from_excel)
        factory_kneja = None
        factory_obnova = None
        for factory in factories_from_excel:
            self.assertEquals(factory["currency"], "BGN")
            self.assertEquals(factory["year"], 2024)
            self.assertEquals(factory["month"], 3)

            if factory["factory_id"] == "32Z140000211335I":
                factory_kneja = factory

            if factory["factory_id"] == "32Z140000237585R":
                factory_obnova = factory

        self.assertNotEqual(factory_kneja, None)
        self.assertNotEqual(factory_obnova, None)
        self.assertEquals(factory_kneja["factory_slug"], self.factory.slug)
        self.assertEquals(factory_obnova["factory_slug"], self.factory2.slug)
        self.assertEquals(factory_kneja["timezone"], "EET")
        self.assertEquals(factory_obnova["timezone"], "EET")

        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)
        response = self.client.post(
            reverse("production_api"),
            data=factory_kneja["production_in_kwh"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 31 * 24 - 1)
        self.assertEqual(
            ElectricityPrice.objects.filter(plan=self.factory.plan).count(), 0
        )
        response = self.client.post(
            reverse("prices"),
            data=factory_kneja["prices"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 31 * 24 - 1)
        self.assertEqual(response.data[0]["plan"], self.factory.plan.slug)
        self.assertEqual(response.data[1]["plan"], self.factory.plan.slug)
        self.assertEqual(response.data[2]["plan"], self.factory.plan.slug)

        # self.assertEqual(response.data[0]["price"], "60.90") # EUR
        # self.assertEqual(response.data[1]["price"], "62.04") # EUR
        # self.assertEqual(response.data[2]["price"], "61.42") # EUR

        # self.assertEqual(response.data[0+30*24]["price"], "65.74") # 128.58 BGN
        # self.assertEqual(response.data[1+30*24]["price"], "60.47") # 118.27 BGN
        # self.assertEqual(response.data[2+30*24]["price"], "48.50") #  94.86 BGN
        # self.assertEqual(response.data[3+30*24]["price"], "31.17") #  60.96 BGN
        # self.assertEqual(response.data[4+30*24]["price"], "32.31") #  63.19 BGN
        # self.assertEqual(response.data[5+30*24]["price"], "40.50") #  79.21 BGN
        # self.assertEqual(response.data[6+30*24]["price"], "30.33") #  59.32 BGN
        # self.assertEqual(response.data[7+30*24]["price"], "32.66") #  63.88 BGN

        self.assertEqual(response.data[0 + 30 * 24]["price"], "128.58")
        self.assertEqual(response.data[1 + 30 * 24]["price"], "118.27")
        self.assertEqual(response.data[2 + 30 * 24]["price"], "94.86")
        self.assertEqual(response.data[3 + 30 * 24]["price"], "60.96")
        self.assertEqual(response.data[4 + 30 * 24]["price"], "63.19")
        self.assertEqual(response.data[5 + 30 * 24]["price"], "79.21")
        self.assertEqual(response.data[6 + 30 * 24]["price"], "59.32")
        self.assertEqual(response.data[7 + 30 * 24]["price"], "63.88")

        self.checkTime(2024, 2, 29, 22, 00, response.data[0]["start_interval"])
        self.checkTime(2024, 2, 29, 23, 00, response.data[1]["start_interval"])
        self.checkTime(2024, 3, 1, 00, 00, response.data[2]["start_interval"])

        self.checkTime(
            2024, 3, 30, 22, 00, response.data[0 + 30 * 24]["start_interval"]
        )
        self.checkTime(
            2024, 3, 30, 23, 00, response.data[1 + 30 * 24]["start_interval"]
        )
        self.checkTime(
            2024, 3, 31, 00, 00, response.data[2 + 30 * 24]["start_interval"]
        )
        self.checkTime(2024, 3, 31, 1, 00, response.data[3 + 30 * 24]["start_interval"])
        self.checkTime(2024, 3, 31, 2, 00, response.data[4 + 30 * 24]["start_interval"])
        self.checkTime(2024, 3, 31, 3, 00, response.data[5 + 30 * 24]["start_interval"])
        self.checkTime(2024, 3, 31, 4, 00, response.data[6 + 30 * 24]["start_interval"])
        self.checkTime(2024, 3, 31, 5, 00, response.data[7 + 30 * 24]["start_interval"])
        self.checkTime(
            2024, 3, 31, 20, 00, response.data[22 + 30 * 24]["start_interval"]
        )

        self.checkTime(2024, 2, 29, 23, 00, response.data[0]["end_interval"])
        self.checkTime(2024, 3, 1, 00, 00, response.data[1]["end_interval"])
        self.checkTime(2024, 3, 1, 1, 00, response.data[2]["end_interval"])

        self.assertEqual(
            ElectricityPrice.objects.filter(plan=self.factory.plan).count(), 31 * 24 - 1
        )

    def check_production(self, response, day, hour, value: str):
        self.assertEqual(Decimal(response.data[hour + day * 24]["energy_in_kwh"]), Decimal(value))



    def test_create_electricity_production_from_report_may_with_user(self):
        """
        Ensure that we can submit a electricity produced in time window
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        excel_filename = dir_path + "/Справка м.05.2024_ГОФРИЛО КО ЕООД.xlsx"
        factories_from_excel = process_excel_report(excel_filename)
        # print(factories_from_excel)
        self.assertEquals(2, len(factories_from_excel))
        self.check_processed_report_keys(factories_from_excel)
        factory_kneja = None
        factory_obnova = None
        for factory in factories_from_excel:
            self.assertEquals(factory["currency"], "BGN")
            self.assertEquals(factory["year"], 2024)
            self.assertEquals(factory["month"], 5)

            if factory["factory_id"] == "32Z140000211335I":
                factory_kneja = factory

            if factory["factory_id"] == "32Z140000237585R":
                factory_obnova = factory

        self.assertNotEqual(factory_kneja, None)
        self.assertNotEqual(factory_obnova, None)
        self.assertEquals(factory_kneja["factory_slug"], self.factory.slug)
        self.assertEquals(factory_obnova["factory_slug"], self.factory2.slug)
        self.assertEquals(factory_kneja["timezone"], "Europe/Sofia")
        self.assertEquals(factory_obnova["timezone"], "Europe/Sofia")

        self.assertEqual(ElectricityFactoryProduction.objects.count(), 0)
        response = self.client.post(
            reverse("production_api"),
            data=factory_obnova["production_in_kwh"],
            format="json",
        )
        self.check_production(response, 2, 0, '0')
        self.check_production(response, 2, 1, '0')
        self.check_production(response, 2, 2, '0')
        self.check_production(response, 2, 3, '0')
        self.check_production(response, 2, 4, '0')
        self.check_production(response, 2, 5, '0')
        self.check_production(response, 2, 6, '0.5')
        self.check_production(response, 2, 7, '7.5')
        self.check_production(response, 2, 8, '35.0')
        self.check_production(response, 2, 9, '34.0')
        self.check_production(response, 2, 10, '22.25')
        self.check_production(response, 2, 11, '9.75')
        self.check_production(response, 2, 12, '16.5')
        self.check_production(response, 2, 13, '34.0')
        self.check_production(response, 2, 14, '27.0')
        self.check_production(response, 2, 15, '21.25')
        self.check_production(response, 2, 16, '32.5')
        self.check_production(response, 2, 17, '11.0')
        self.check_production(response, 2, 18, '13.0')
        self.check_production(response, 2, 19, '5.75')
        self.check_production(response, 2, 20, '0')
        self.check_production(response, 2, 21, '0')
        self.check_production(response, 2, 22, '0')
        self.check_production(response, 2, 23, '0')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectricityFactoryProduction.objects.count(), 31 * 24)
        self.assertEqual(
            ElectricityPrice.objects.filter(plan=self.factory.plan).count(), 0
        )
        response = self.client.post(
            reverse("prices"),
            data=factory_kneja["prices"],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 31 * 24)
        self.assertEqual(response.data[0]["plan"], self.factory.plan.slug)
        self.assertEqual(response.data[1]["plan"], self.factory.plan.slug)
        self.assertEqual(response.data[2]["plan"], self.factory.plan.slug)


        self.assertEqual(response.data[0 + 30 * 24]["price"], "194.67")
        self.assertEqual(response.data[1 + 30 * 24]["price"], "175.56")
        self.assertEqual(response.data[2 + 30 * 24]["price"], "159.36")
        self.assertEqual(response.data[3 + 30 * 24]["price"], "164.10")
        self.assertEqual(response.data[4 + 30 * 24]["price"], "165.06")
        self.assertEqual(response.data[5 + 30 * 24]["price"], "170.29")
        self.assertEqual(response.data[6 + 30 * 24]["price"], "202.10")
        self.assertEqual(response.data[7 + 30 * 24]["price"], "191.99")


        self.checkTime(2024, 4, 30, 21, 00, response.data[0]["start_interval"])
        self.checkTime(2024, 4, 30, 22, 00, response.data[1]["start_interval"])
        self.checkTime(2024, 4, 30, 23, 00, response.data[2]["start_interval"])

        self.checkTime(2024, 4, 30, 22, 00, response.data[0]["end_interval"])
        self.checkTime(2024, 4, 30, 23, 00, response.data[1]["end_interval"])
        self.checkTime(2024, 5,  1, 0, 00, response.data[2]["end_interval"])

        self.checkTime(
            2024, 5, 30, 21, 00, response.data[0 + 30 * 24]["start_interval"]
        )
        self.checkTime(
            2024, 5, 30, 22, 00, response.data[1 + 30 * 24]["start_interval"]
        )
        self.checkTime(
            2024, 5, 30, 23, 00, response.data[2 + 30 * 24]["start_interval"]
        )
        self.checkTime(2024, 5, 31, 0, 00, response.data[3 + 30 * 24]["start_interval"])
        self.checkTime(2024, 5, 31, 1, 00, response.data[4 + 30 * 24]["start_interval"])
        self.checkTime(2024, 5, 31, 2, 00, response.data[5 + 30 * 24]["start_interval"])
        self.checkTime(2024, 5, 31, 3, 00, response.data[6 + 30 * 24]["start_interval"])
        self.checkTime(2024, 5, 31, 4, 00, response.data[7 + 30 * 24]["start_interval"])
        self.checkTime(
            2024, 5, 31, 19, 00, response.data[22 + 30 * 24]["start_interval"]
        )


        self.assertEqual(
            ElectricityPrice.objects.filter(plan=self.factory.plan).count(), 31 * 24
        )
