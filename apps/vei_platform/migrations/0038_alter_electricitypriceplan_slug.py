# Generated by Django 4.2.4 on 2024-05-25 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vei_platform', '0037_auto_20240525_0522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electricitypriceplan',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]