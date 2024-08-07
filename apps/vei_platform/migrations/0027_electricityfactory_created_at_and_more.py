# Generated by Django 4.2.4 on 2024-02-05 06:26

from django.db import migrations, models
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0026_alter_campaign_amount_currency_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="electricityfactory",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="electricityfactory",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="amount_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €"), ("USD", "USD $")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="electricityprice",
            name="price_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €"), ("USD", "USD $")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="investementincampaign",
            name="amount_currency",
            field=djmoney.models.fields.CurrencyField(
                choices=[("BGN", "BGN лв"), ("EUR", "EUR €"), ("USD", "USD $")],
                default="BGN",
                editable=False,
                max_length=3,
            ),
        ),
    ]
