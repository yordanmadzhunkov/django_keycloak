# Generated by Django 4.2.4 on 2024-05-08 04:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0029_alter_campaign_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="electricityprice",
            name="when",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
    ]
