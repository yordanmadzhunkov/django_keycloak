# Generated by Django 4.2.4 on 2024-05-08 04:45

from django.db import migrations
from datetime import datetime, timezone


def set_my_defaults(apps, schema_editor):
    ElectricityPrice = apps.get_model("vei_platform", "electricityprice")
    count = 0
    for pr in ElectricityPrice.objects.all():
        old = pr.month
        old_date = datetime(
            year=old.year,
            month=old.month,
            day=old.day,
            hour=0,
            minute=0,
            second=0,
            tzinfo=timezone.utc,
        )
        pr.when = old_date
        pr.save()
        count = count + 1


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0030_electricityprice_when"),
    ]

    operations = [
        migrations.RunPython(set_my_defaults),
    ]
