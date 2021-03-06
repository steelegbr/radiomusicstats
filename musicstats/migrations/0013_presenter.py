# Generated by Django 3.0.8 on 2020-10-15 18:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("musicstats", "0012_station_timezone"),
    ]

    operations = [
        migrations.CreateModel(
            name="Presenter",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField()),
                ("biography", models.TextField()),
                ("image", models.URLField()),
                (
                    "station",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="musicstats.Station",
                    ),
                ),
            ],
            options={
                "unique_together": {("name", "station")},
            },
        ),
    ]
