# Generated by Django 4.2.4 on 2024-06-15 04:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vei_platform', '0039_rename_when_electricityprice_start_interval_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electricitypriceplan',
            name='owner',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
