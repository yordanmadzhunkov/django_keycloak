# Generated by Django 4.2.4 on 2024-08-14 06:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0049_reset_all_prices_currencies"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ElectricityWorkingHoursPerMonth",
            new_name="ElectricityFactoryProduction",
        ),
    ]
