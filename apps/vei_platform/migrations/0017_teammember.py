# Generated by Django 4.2.6 on 2023-12-08 06:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import vei_platform.models.team


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("vei_platform", "0016_alter_campaign_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamMember",
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
                    "image",
                    models.ImageField(
                        blank=True,
                        default=None,
                        null=True,
                        upload_to=vei_platform.models.team.user_team_image_upload_directory_path,
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("role", models.CharField(max_length=128)),
                ("description", models.TextField()),
                ("twitter", models.URLField(blank=True, default=None, null=True)),
                ("facebook", models.URLField(blank=True, default=None, null=True)),
                ("instagram", models.URLField(blank=True, default=None, null=True)),
                ("linkedin", models.URLField(blank=True, default=None, null=True)),
                ("order", models.IntegerField(default=100)),
                (
                    "profile",
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
    ]
