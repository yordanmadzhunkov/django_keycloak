# Generated by Django 4.2.4 on 2024-02-05 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vei_platform', '0027_electricityfactory_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legalentitysources',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='legalentitysources',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
