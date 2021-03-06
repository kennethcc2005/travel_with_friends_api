# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-27 20:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel_with_friends', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SnippetsSnippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('highlighted', models.TextField()),
                ('created', models.DateTimeField()),
                ('title', models.CharField(max_length=100)),
                ('code', models.TextField()),
                ('linenos', models.BooleanField()),
                ('language', models.CharField(max_length=100)),
                ('style', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'snippets_snippet',
                'managed': False,
            },
        ),
        migrations.AlterModelTable(
            name='poidetailtablev2',
            table='poi_detail_table_v2',
        ),
    ]
