# Generated by Django 2.2.4 on 2019-09-20 17:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('musicstats', '0004_auto_20190919_2127'),
    ]

    operations = [
        migrations.CreateModel(
            name='EpgEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField()),
                ('description', models.TextField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('image', models.URLField()),
                ('start', models.TimeField()),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicstats.Station')),
            ],
        ),
    ]
