# Generated by Django 4.2.4 on 2024-06-23 04:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0041_alter_electricitypriceplan_owner"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="electricityprice",
            constraint=models.CheckConstraint(
                check=models.Q(("start_interval__gt", models.F("start_interval"))),
                name="check_start_date",
            ),
        ),
    ]
