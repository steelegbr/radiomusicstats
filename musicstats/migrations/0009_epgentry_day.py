# Generated by Django 3.0.8 on 2020-07-27 14:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("musicstats", "0008_auto_20190927_2110"),
    ]

    operations = [
        migrations.AddField(
            model_name="epgentry",
            name="day",
            field=models.IntegerField(
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(6),
                ],
            ),
        ),
    ]
