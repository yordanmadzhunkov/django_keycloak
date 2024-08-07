# Generated by Django 4.2.6 on 2023-11-23 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0010_userprofile_show_balance"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvestementInListing",
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
                    "amount",
                    models.DecimalField(decimal_places=2, default=10000, max_digits=12),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("IN", "Interested"),
                            ("CA", "Canceled"),
                            ("CO", "Completed"),
                        ],
                        default="IN",
                        max_length=2,
                    ),
                ),
                (
                    "investor_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.userprofile",
                    ),
                ),
                (
                    "listing",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.solarestatelisting",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="SolarEstateInvestor",
        ),
    ]
