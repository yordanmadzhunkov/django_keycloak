# Generated by Django 4.2.6 on 2024-01-05 11:14

from django.db import migrations
import vei_platform.models.factory
import vei_platform.models.restricted_file_field


class Migration(migrations.Migration):

    dependencies = [
        ("vei_platform", "0020_electricityfactorycomponents_docfile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="electricityfactorycomponents",
            name="docfile",
            field=vei_platform.models.restricted_file_field.RestrictedFileField(
                blank=True,
                default=None,
                null=True,
                upload_to=vei_platform.models.factory.factory_component_file_upload_directory_path,
            ),
        ),
    ]
