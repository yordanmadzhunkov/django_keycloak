# Generated by Django 4.2.4 on 2023-10-07 07:11

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import vei_platform.models.factory
import vei_platform.models.profile


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BankLoan",
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
                ("start_date", models.DateField()),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, default=10000, max_digits=12),
                ),
                ("duration", models.IntegerField(default=180)),
            ],
        ),
        migrations.CreateModel(
            name="ElectricityFactory",
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
                ("name", models.CharField(max_length=128)),
                (
                    "factory_type",
                    models.CharField(
                        choices=[
                            ("FEV", "Photovoltaic"),
                            ("WIN", "Wind turbine"),
                            ("HYD", "Hydropower"),
                            ("BIO", "Biomass"),
                            ("RGS", "Renewable gas"),
                        ],
                        default="FEV",
                        max_length=3,
                    ),
                ),
                (
                    "fraction_on_platform",
                    models.DecimalField(decimal_places=6, default=0, max_digits=9),
                ),
                ("location", models.CharField(default="България", max_length=100)),
                ("opened", models.DateField(null=True)),
                (
                    "capacity_in_mw",
                    models.DecimalField(decimal_places=3, default=0, max_digits=9),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        default=None,
                        null=True,
                        upload_to=vei_platform.models.factory.user_image_upload_directory_path,
                    ),
                ),
                (
                    "tax_id",
                    models.CharField(
                        blank=True, default=None, max_length=128, null=True
                    ),
                ),
                ("owner_name", models.CharField(default="Unknown", max_length=128)),
                (
                    "manager",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ElectricityPricePlan",
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
                ("name", models.CharField(max_length=128)),
                (
                    "start_year",
                    models.IntegerField(
                        default=2022,
                        validators=[
                            django.core.validators.MaxValueValidator(2050),
                            django.core.validators.MinValueValidator(1990),
                        ],
                    ),
                ),
                (
                    "end_year",
                    models.IntegerField(
                        default=2025,
                        validators=[
                            django.core.validators.MaxValueValidator(2050),
                            django.core.validators.MinValueValidator(1990),
                        ],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FactoryProductionPlan",
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
                ("name", models.CharField(max_length=128)),
                (
                    "start_year",
                    models.IntegerField(
                        default=2022,
                        validators=[
                            django.core.validators.MaxValueValidator(2050),
                            django.core.validators.MinValueValidator(1990),
                        ],
                    ),
                ),
                (
                    "end_year",
                    models.IntegerField(
                        default=2025,
                        validators=[
                            django.core.validators.MaxValueValidator(2050),
                            django.core.validators.MinValueValidator(1990),
                        ],
                    ),
                ),
                (
                    "factory",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.electricityfactory",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LegalEntity",
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
                ("native_name", models.CharField(max_length=1024)),
                ("latin_name", models.CharField(max_length=1024)),
                ("legal_form", models.CharField(max_length=4, null=True)),
                ("tax_id", models.CharField(max_length=48, null=True, unique=True)),
                ("founded", models.DateField(null=True)),
                ("person", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="SolarEstateListing",
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
                ("start_date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "persent_from_profit",
                    models.DecimalField(decimal_places=2, max_digits=2),
                ),
                ("duration", models.IntegerField(default=180)),
                (
                    "commision",
                    models.DecimalField(decimal_places=2, default=1.5, max_digits=2),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
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
                    "avatar",
                    models.ImageField(
                        blank=True,
                        default=None,
                        null=True,
                        upload_to=vei_platform.models.profile.user_profile_image_upload_directory_path,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StakeHolder",
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
                    "stake_type",
                    models.CharField(
                        choices=[
                            ("OWN", "Owner"),
                            ("EOW", "Ex-Owner"),
                            ("BoD", "Director in board"),
                            ("EMP", "Employee"),
                            ("CEO", "CEO"),
                            ("Inv", "Investor"),
                            ("LOA", "Loan provider"),
                            ("TRD", "Trader"),
                        ],
                        default=None,
                        max_length=3,
                    ),
                ),
                (
                    "percent",
                    models.DecimalField(
                        decimal_places=6, default=None, max_digits=9, null=True
                    ),
                ),
                ("start_date", models.DateField(blank=True, default=None, null=True)),
                ("end_date", models.DateField(blank=True, default=None, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stakeholders",
                        to="vei_platform.legalentity",
                    ),
                ),
                (
                    "holder",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.legalentity",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SolarEstateInvestor",
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
                ("name", models.CharField(max_length=128)),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, default=10000, max_digits=12),
                ),
                (
                    "solar_estates",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.solarestatelisting",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LegalEntitySources",
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
                ("url", models.CharField(max_length=1024)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "entity",
                    models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="vei_platform.legalentity",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FinancialPlan",
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
                ("name", models.TextField()),
                ("start_month", models.DateField()),
                ("span_in_months", models.IntegerField()),
                (
                    "capitalization",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "manager_capital",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "factory",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.electricityfactory",
                    ),
                ),
                (
                    "loan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.bankloan",
                    ),
                ),
                (
                    "prices",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.electricitypriceplan",
                    ),
                ),
                (
                    "solar_estates",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.solarestatelisting",
                    ),
                ),
                (
                    "working_hours",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.factoryproductionplan",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ElectricityWorkingHoursPerMonth",
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
                ("month", models.DateField()),
                ("number", models.DecimalField(decimal_places=2, max_digits=6)),
                (
                    "plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="vei_platform.factoryproductionplan",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ElectricityPrice",
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
                ("month", models.DateField()),
                ("number", models.DecimalField(decimal_places=2, max_digits=6)),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="vei_platform.electricitypriceplan",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="electricityfactory",
            name="primary_owner",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="vei_platform.legalentity",
            ),
        ),
        migrations.CreateModel(
            name="BankLoanInterest",
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
                ("month", models.DateField()),
                ("number", models.DecimalField(decimal_places=2, max_digits=6)),
                (
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="vei_platform.bankloan",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="bankloan",
            name="factory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="vei_platform.electricityfactory",
            ),
        ),
        migrations.AddConstraint(
            model_name="legalentitysources",
            constraint=models.UniqueConstraint(
                fields=("entity", "url"), name="URL should be unique for each company"
            ),
        ),
    ]
