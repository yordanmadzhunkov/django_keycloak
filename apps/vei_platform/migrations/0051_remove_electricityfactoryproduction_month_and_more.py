# Generated by Django 4.2.4 on 2024-08-19 06:33

import datetime
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "vei_platform",
            "0050_rename_electricityworkinghourspermonth_electricityfactoryproduction",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="electricityfactoryproduction",
            name="month",
        ),
        migrations.RemoveField(
            model_name="electricityfactoryproduction",
            name="number",
        ),
        migrations.RemoveField(
            model_name="electricityfactoryproduction",
            name="plan",
        ),
        migrations.AddField(
            model_name="electricityfactory",
            name="slug",
            field=models.SlugField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="electricityfactoryproduction",
            name="end_interval",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 1, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
        migrations.AddField(
            model_name="electricityfactoryproduction",
            name="energy_in_kwh",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=14
            ),
        ),
        migrations.AddField(
            model_name="electricityfactoryproduction",
            name="factory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="vei_platform.electricityfactory",
            ),
        ),
        migrations.AddField(
            model_name="electricityfactoryproduction",
            name="start_interval",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
        migrations.DeleteModel(
            name="FactoryProductionPlan",
        ),
    ]