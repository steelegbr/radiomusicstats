# Generated by Django 2.2.4 on 2019-09-27 20:10

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('musicstats', '0007_station_logo_square'),
    ]

    operations = [
        migrations.AddField(
            model_name='station',
            name='liner_ratio',
            field=models.DecimalField(decimal_places=1, default=0.0, max_digits=2, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]),
        ),
        migrations.AddField(
            model_name='station',
            name='use_liners',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Podcast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('feed', models.URLField()),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicstats.Station')),
            ],
            options={
                'unique_together': {('name', 'station')},
            },
        ),
        migrations.CreateModel(
            name='MarketingLiner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line', models.TextField()),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicstats.Station')),
            ],
            options={
                'unique_together': {('line', 'station')},
            },
        ),
    ]