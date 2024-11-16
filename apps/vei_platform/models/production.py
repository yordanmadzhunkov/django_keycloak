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
import re

def exctract_timezone_currency_unit(sheet):
    if 'IBEX_DAM_Price' == sheet["B1"].value and 'лв./MWh' == sheet["B2"].value:
        r = re.match(r"Date\/(\S+)", sheet["A1"].value)
        if r:
            timezone_label = r.group(1)
            #print(timezone_label)
            num_factories = count_factories_old_format(sheet)
            #print(num_factories)
            #print("A1 = ", sheet["A1"].value)
            #print("A2 = ", sheet["A2"].value)
            if num_factories > 0:
                return timezone_label, 'BGN', 'MWh'
            #return num_factories > 0
    return None, None, None

def count_factories_old_format(sheet):
    res = 0
    for h in range(1024):
        v1 = sheet.cell(row=2, column=4 + 2 * h + 0).value
        v2 = sheet.cell(row=2, column=4 + 2 * h + 1).value
        if v1 == 'Производство, MWh' and v2 == 'Сума, лв.':
            res = res + 1
        else:
            #print ("v1 = %s", v1)
            #print ("v2 = %s", v2)
            break
    return res

def find_factory(search_id):
    factory_name = None
    factory_slug = None
    factory_id = None
    for id in search_id.split(' '):
        try:
            f = ElectricityFactory.objects.get(factory_code=id)
            factory_slug = f.slug
            factory_name = f.name
            factory_id = f.factory_code
            return factory_name, factory_slug, factory_id
        except ElectricityFactory.DoesNotExist:
            pass

    d = search_id.split(' ')
    if len(d) > 0:
        factory_id = d[0]
    return factory_name, factory_slug, factory_id


def add_production(production_in_kwh, prices, factory_slug, production_in_mwh, price, localtimezone, start_interval, end_interval=None):

    start = start_interval
    start = localtimezone.localize(start)
    start = start.astimezone(utc)
    end = start + timedelta(hours=1) if end_interval is None else end_interval

    energy_in_mwh = production_in_mwh if isinstance(production_in_mwh, Decimal) else Decimal("%0.4f" % production_in_mwh)
    energy_in_kwh = energy_in_mwh * Decimal(1000)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S%z")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S%z")

    price_decimal = price if isinstance(price, Decimal) else Decimal("%0.2f" % price)
       
    production_in_kwh.append({
                        "factory": factory_slug,
                        "energy_in_kwh": energy_in_kwh,
                        "start_interval": start_str,
                        "end_interval": end_str,
    })
    prices.append({
                        "factory": factory_slug,
                        "price": price_decimal,
                        "start_interval": start_str,
                        "end_interval": end_str,
    })


def extract_factory_production(sheet, h, timezone_label, currency, unit):
    errors = []
    factory_name = None
    factory_slug = None
    factory_id = None
    owner_legal = None
    month = None
    production_in_kwh = []
    prices = []
    localtimezone = timezone(timezone_label)


    v1 = sheet.cell(row=2, column=4 + 2 * h + 0).value
    v2 = sheet.cell(row=2, column=4 + 2 * h + 1).value
    start_interval, end_interval = None, None
    if v1 == 'Производство, MWh' and v2 == 'Сума, лв.':
        factory_name, factory_slug, factory_id = find_factory(sheet.cell(row=1, column=4 + 2 * h + 0).value)
        for r in range(4*24*31 + 10):
            start = sheet.cell(row=3 + r, column=1).value
            # end interval check
            #if end_interval is not None and end_interval == start:
            if end_interval is not None and num_intervals == 4:
                add_production(production_in_kwh, 
                               prices, 
                               factory_slug, 
                               price, 
                               total_prod, 
                               localtimezone, 
                               start_interval=start_interval)
                start_interval = end_interval
                end_interval = start_interval + timedelta(hours=1)
                total_prod = Decimal(0)
                num_intervals = 0

            #else: 
                #print("start = %s != %s" % (str(start), str(end_interval)))
                #print("end interval check %s" % )

            if not start:          
                break

            # start inteval check
            price = Decimal(str(sheet.cell(row=3 + r, column=2).value))
            prod = Decimal(str(sheet.cell(row=3 + r, column=4 + 2 * h + 0).value))

            if start_interval is None:
                start_interval = start
                end_interval = start_interval + timedelta(hours=1)
                total_prod = Decimal(0)
                num_intervals = 0

            if start_interval is not None:
                total_prod += prod
                num_intervals += 1
                if month is None:
                    month = start_interval
        
    res = {
            "factory_name": factory_name,
            "factory_slug": factory_slug,
            "timezone": timezone_label,
            "factory_id": factory_id,
            "legal_entity": owner_legal,
            "month": month.month,
            "year": month.year,
            "production_in_kwh": production_in_kwh,
            "prices": prices,
            "currency": currency,
            "errors": errors,
    }
    return res

def process_old_excel_report(sheet, timezone_label, currency, unit):
    factories = []
    num_factories = count_factories_old_format(sheet)
    for num_factory in range(num_factories):
        factories.append(extract_factory_production(sheet, num_factory, timezone_label, currency, unit))
    return factories



def process_excel_report(filename):
    # Open Excel file
    workbook = openpyxl.load_workbook(filename)
    factories = []

    for sheet_name in workbook.sheetnames:
        # print(sheet_name)
        sheet = workbook[sheet_name]  # Access sheet by name
        timezone_label, currency, unit = exctract_timezone_currency_unit(sheet)
        if timezone_label and currency and unit:
            return process_old_excel_report(sheet, timezone_label, currency, unit)

        errors = []
        # print(sheet)


        month = sheet["B1"].value
        owner_legal = sheet["C1"].value
        factory_name = sheet["C2"].value
        some_id = sheet["C3"].value

        if isinstance(month, datetime):
            num_days = calendar.monthrange(month.year, month.month)[1]
        else:
            errors.append(_("Report does not contain period in B1 cell, found %s") % str(month))
            num_days = 0    

        production_label = sheet["B4"].value
        if production_label != "Количество\nМВтч":
            errors.append("Expected B4 to be 'Количество\nМВтч'")
            res = {
                "errors": errors,
            }
            factories.append(res)
            continue


        factory_object = ElectricityFactory.objects.filter(name=factory_name).first()
        if factory_object:
            factory_slug = factory_object.slug
            timezone_label = factory_object.get_requested_timezone()
        else:
            errors.append(_("Factory with name `%s` not found") % factory_name)
            factory_slug = None
            timezone_label = "UTC"

        localtimezone = timezone(timezone_label)


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
                add_production(production_in_kwh, 
                               prices, 
                               factory_slug, 
                               price, 
                               production, 
                               localtimezone, 
                               start_interval=d1)
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
