from django.db import models
from datetime import datetime, timezone
from decimal import Decimal
from .factory import ElectricityFactory
from .restricted_file_field import RestrictedFileField
from django.contrib.auth.models import User


class ElectricityFactoryProduction(models.Model):
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.CASCADE
    )

    start_interval = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        default=datetime(
            year=2024, month=1, day=1, hour=0, minute=0, tzinfo=timezone.utc
        ),
    )

    end_interval = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        default=datetime(
            year=2024, month=1, day=1, hour=1, minute=0, tzinfo=timezone.utc
        ),
    )

    energy_in_kwh = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal(0)
    )

    def __str__(self) -> str:
        return "%s %s kWh" % (
            self.start_interval.strftime("%y-%m-%d %H:%M %Z"),
            self.energy_in_kwh,
        )


def user_document_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    res = "documents/user_{0}/{1}".format(str(instance.owner), filename)
    print("-------->>>>>>>" + res)
    return res


class ElectricityFactoryUploadedProductionReport(models.Model):
    docfile = RestrictedFileField(
        upload_to=user_document_upload_directory_path,
        content_types=[
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
        max_upload_size=6 * 1024 * 1024,  # 5 MB
        default=None,
        null=False,
        blank=False,
    )
    owner = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ElectricityFactoryProductionReport(models.Model):
    months_selection = (
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    )

    report = models.ForeignKey(
        ElectricityFactoryUploadedProductionReport,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    factory = models.ForeignKey(
        ElectricityFactory, blank=False, null=False, on_delete=models.CASCADE
    )
    year = models.IntegerField("Year")
    month = models.IntegerField("Month", choices=months_selection)

    class Meta:
        unique_together = [["factory", "year", "month"]]


# import xlrd
# pip install xlrd==1.2.0
import openpyxl
from datetime import datetime, timedelta
from pytz import timezone, utc

import calendar
from decimal import Decimal
from vei_platform.models.factory import ElectricityFactory
from django.utils.translation import gettext as _


def process_excel_report(filename):
    # Open Excel file
    workbook = openpyxl.load_workbook(filename)
    factories = []

    for sheet_name in workbook.sheetnames:
        # print(sheet_name)
        sheet = workbook[sheet_name]  # Access sheet by name
        # print(sheet)

        month = sheet["B1"].value
        owner_legal = sheet["C1"].value
        factory_name = sheet["C2"].value
        some_id = sheet["C3"].value
        num_days = calendar.monthrange(month.year, month.month)[1]
        errors = []

        factory_object = ElectricityFactory.objects.filter(name=factory_name).first()
        if factory_object:
            factory_slug = factory_object.slug
            timezone_label = factory_object.get_requested_timezone()
        else:
            errors.append(_("Factory with name `%s` not found") % factory_name)
            factory_slug = None
            timezone_label = "UTC"

        localtimezone = timezone(timezone_label)

        production_label = sheet["B4"].value
        if production_label != "Количество\nМВтч":
            errors.append("Expected B4 to be 'Количество\nМВтч'")

        # print("Num Days %d" % num_days)
        # check hour labels
        for h in range(24):
            v = sheet.cell(row=4, column=3 + h).value
            c = sheet.cell(row=4, column=3 + h)
            if v != h + 1:
                errors.append(
                    "Expected value %d in cell %s%d" % (h + 1, c.column_letter, c.row)
                )

        production_in_kwh = []
        prices = []
        production = ElectricityFactoryProduction.objects.filter(factory=factory_object)
        for d in range(num_days):
            date_label = sheet.cell(row=5 + d, column=2).value
            # print(date_label)
            for h in range(24):
                production = sheet.cell(row=5 + d, column=3 + h).value
                price = sheet.cell(row=5 + d, column=3 + h + 27).value
                d1 = datetime(year=month.year, month=month.month, day=d + 1, hour=h)
                d1 = localtimezone.localize(d1)
                d1 = d1.astimezone(utc)
                energy_in_kwh = Decimal("%0.4f" % production) * Decimal(1000)
                # try:
                #     p = production.get(start_interval=d1)
                # except ElectricityFactoryProduction.DoesNotExist:
                #     ElectricityFactoryProduction.objects.create(factory_name=factory_object,
                #                                                 start_interval=d1,
                #                                                 end_interval=d1 + timedelta(hours=1),
                #                                                 energy_in_kwh=production_in_kwh)
                # finally:
                #     pass
                start_interval = d1.strftime("%Y-%m-%dT%H:%M:%S%z")
                end_interval = (d1 + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S%z")
                # print(type(production))

                price = Decimal("%0.2f" % price)
                # print(str(d1) + ' -> ' + str(p) + ' kWh @ ' + str(price) )
                production_in_kwh.append(
                    {
                        "factory": factory_slug,
                        "energy_in_kwh": energy_in_kwh,
                        "start_interval": start_interval,
                        "end_interval": end_interval,
                    }
                )

                prices.append(
                    {
                        "factory": factory_slug,
                        "price": price,
                        "start_interval": start_interval,
                        "end_interval": end_interval,
                    }
                )

        res = {
            "factory_name": factory_name,
            "factory_slug": factory_slug,
            "timezone": timezone_label,
            "factory_id": some_id,
            "legal_entity": owner_legal,
            "month": month.month,
            "year": month.year,
            "production_in_kwh": production_in_kwh,
            "prices": prices,
            "currency": "BGN",
            "errors": errors,
        }
        factories.append(res)

    return factories
