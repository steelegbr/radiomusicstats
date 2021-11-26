# Generated by Django 2.2.4 on 2019-09-17 19:51

import colorful.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import musicstats.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Artist",
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
                ("name", models.CharField(max_length=768, unique=True)),
                (
                    "thumbnail",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.artist_thumbnail_path
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.artist_image_path
                    ),
                ),
                ("musicbrainz_id", models.CharField(max_length=255)),
                ("wiki_content", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Song",
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
                ("display_artist", models.TextField()),
                ("title", models.TextField()),
                (
                    "thumbnail",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.song_thumbnail_path
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.song_image_path
                    ),
                ),
                ("musicbrainz_id", models.CharField(blank=True, max_length=255)),
                ("wiki_content", models.TextField(blank=True)),
                ("itunes_url", models.TextField(blank=True)),
                ("amazon_url", models.TextField(blank=True)),
                ("artists", models.ManyToManyField(to="musicstats.Artist")),
            ],
            options={
                "ordering": ["display_artist", "title"],
            },
        ),
        migrations.CreateModel(
            name="Station",
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
                ("name", models.CharField(max_length=768, unique=True)),
                (
                    "logo",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.logo_image_path
                    ),
                ),
                (
                    "logo_inverse",
                    models.ImageField(
                        blank=True, upload_to=musicstats.models.logo_inverse_path
                    ),
                ),
                ("slogan", models.TextField()),
                ("primary_colour", colorful.fields.RGBColorField()),
                ("text_colour", colorful.fields.RGBColorField()),
                ("stream_aac_high", models.URLField()),
                ("stream_aac_low", models.URLField()),
                ("stream_mp3_high", models.URLField()),
                ("stream_mp3_low", models.URLField()),
                (
                    "update_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SongPlay",
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
                ("date_time", models.DateTimeField(auto_now=True)),
                (
                    "song",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="musicstats.Song",
                    ),
                ),
                (
                    "station",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="musicstats.Station",
                    ),
                ),
            ],
        ),
    ]
