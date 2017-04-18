# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 14:14
from __future__ import unicode_literals

from django.db import migrations, models
import musicstats.models


class Migration(migrations.Migration):

    dependencies = [
        ('musicstats', '0004_vote_vote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='image',
            field=models.ImageField(blank=True, upload_to=musicstats.models.artist_image_path),
        ),
        migrations.AlterField(
            model_name='artist',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to=musicstats.models.artist_thumbnail_path),
        ),
        migrations.AlterField(
            model_name='artist',
            name='wiki_content',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='amazon_url',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='image',
            field=models.ImageField(blank=True, upload_to=musicstats.models.song_image_path),
        ),
        migrations.AlterField(
            model_name='song',
            name='itunes_url',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='musicbrainz_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='song',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to=musicstats.models.song_thumbnail_path),
        ),
        migrations.AlterField(
            model_name='song',
            name='wiki_content',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='station',
            name='logo',
            field=models.ImageField(blank=True, upload_to=musicstats.models.logo_image_path),
        ),
        migrations.AlterField(
            model_name='station',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to=musicstats.models.logo_thumbnail_path),
        ),
    ]
