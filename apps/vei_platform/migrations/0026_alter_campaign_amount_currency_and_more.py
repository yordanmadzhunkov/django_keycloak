# Generated by Django 4.2.4 on 2024-01-25 06:36

from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0025_remove_electricityprice_number_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="amount_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="electricityprice",
            name="price_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="investementincampaign",
            name="amount_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
    ]
