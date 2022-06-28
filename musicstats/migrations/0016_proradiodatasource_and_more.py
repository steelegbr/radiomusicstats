# Generated by Django 4.0.5 on 2022-06-28 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("musicstats", "0015_auto_20211126_1932"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProRadioDataSource",
            fields=[
                (
                    "epgdatasource_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="musicstats.epgdatasource",
                    ),
                ),
                ("schedule_url", models.URLField()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("musicstats.epgdatasource",),
        ),
        migrations.AlterField(
            model_name="epgdatasource",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AlterField(
            model_name="presenterdatasource",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
    ]