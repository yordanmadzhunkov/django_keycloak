# Generated by Django 4.2.4 on 2024-01-24 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vei_platform', '0022_electricityfactorycomponents_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electricityfactory',
            name='location',
            field=models.CharField(default='Bulgaria', max_length=100),
        ),
    ]