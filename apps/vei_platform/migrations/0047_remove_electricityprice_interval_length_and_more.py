# Generated by Django 4.2.4 on 2024-06-25 04:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0046_alter_electricityprice_start_interval"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="electricityprice",
            name="interval_length",
        ),
        migrations.AddField(
            model_name="electricityprice",
            name="end_interval",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 1, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
    ]
