# Generated by Django 3.0.8 on 2020-07-27 16:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('musicstats', '0009_epgentry_day'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='epgentry',
            name='last_updated',
        ),
    ]
