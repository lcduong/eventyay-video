# Generated by Django 4.2.14 on 2024-09-17 03:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0065_chat_mentions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="world",
            name="domain",
            field=models.CharField(
                blank=True,
                max_length=250,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        regex="^[a-z0-9-.:]+(/[a-zA-Z0-9-_./]*)?$"
                    )
                ],
            ),
        ),
    ]
