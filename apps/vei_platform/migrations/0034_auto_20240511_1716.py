# Generated by Django 4.2.4 on 2024-05-11 17:16

from django.db import migrations



def create_europe_billing_zones(apps, schema_editor):
    billing_zones = {
                "AT": "Austria",
                "BE": "Belgium",
                "BG": "Bulgaria",
                "CH": "Switzerland",
                "CZ": "Czech Republic",
                "DE-LU": "Germany, Luxembourg",
                "DE-AT-LU": "Germany, Austria, Luxembourg",
                "DK1": "Denmark 1",
                "DK2": "Denmark 2",
                "EE": "Estionia",
                "ES": "Spain",
                "FI": "Finland",
                "FR": "France",
                "GR": "Greece",
                "HR": "Croatia",
                "HU": "Hungary",
                "IT-Calabria": "Italy Calabria",
                "IT-Centre-North": "Italy Centre North",
                "IT-Centre-South": "Italy Centre South",
                "IT-North": "Italy North",
                "IT-SACOAC": "Italy Sardinia Corsica AC",
                "IT-SACODC": "Italy Sardinia Corsica DC",
                "IT-Sardinia": "Italy Sardinia",
                "IT-Sicily": "Italy Sicily",
                "IT-South": "Italy South",
                "LT": "Lithuania",
                "LV": "Latvia",
                "ME": "Montenegro",
                "NL": "Netherlands",
                "NO1": "Norway 1",
                "NO2": "Norway 2",
                "NO2NSL": "Norway North Sea Link",
                "NO3": "Norway 3",
                "NO4": "Norway 4",
                "NO5": "Norway 5",
                "PL": "Poland",
                "PT": "Portugal",
                "RO": "Romania",
                "RS": "Serbia",
                "SE1": "Sweden 1",
                "SE2": "Sweden 2",
                "SE3": "Sweden 3",
                "SE4": "Sweden 4",
                "SI": "Slovenia",
                "SK": "Slovakia",
    }
    ElectricityBillingZone = apps.get_model('vei_platform', 'electricitybillingzone')
    for code, name in billing_zones.items():
        u = ElectricityBillingZone.objects.create(code=code, name=name)
        u.save()



class Migration(migrations.Migration):

    dependencies = [
        ('vei_platform', '0033_electricitybillingzone'),
    ]

    operations = [
        migrations.RunPython(create_europe_billing_zones),
    ]