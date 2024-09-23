# Generated by Django 4.2.4 on 2024-09-15 05:16

import datetime
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0056_electricityfactoryschedule"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="electricityfactoryschedule",
            name="min_price",
        ),
        migrations.RemoveField(
            model_name="electricityfactoryschedule",
            name="min_price_currency",
        ),
        migrations.AddField(
            model_name="electricityfactoryschedule",
            name="end_interval",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 1, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
        migrations.AddField(
            model_name="electricityfactoryschedule",
            name="start_interval",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                ),
            ),
        ),
        migrations.AddField(
            model_name="electricityfactoryschedule",
            name="working",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="MinPriceCriteria",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "min_price_currency",
                    djmoney.models.fields.CurrencyField(
                        choices=[("BGN", "BGN лв"), ("EUR", "EUR €"), ("USD", "USD $")],
                        default="BGN",
                        editable=False,
                        max_length=3,
                    ),
                ),
                (
                    "min_price",
                    djmoney.models.fields.MoneyField(
                        decimal_places=2,
                        default=Decimal("0"),
                        default_currency="BGN",
                        max_digits=14,
                    ),
                ),
                (
                    "factory",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="vei_platform.electricityfactory",
                    ),
                ),
            ],
        ),
    ]
