# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-21 14:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0054_auto_20160321_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='measurevalue',
            name='denom_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurevalue',
            name='denom_items',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurevalue',
            name='denom_quantity',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurevalue',
            name='num_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurevalue',
            name='num_items',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurevalue',
            name='num_quantity',
            field=models.FloatField(blank=True, null=True),
        ),
    ]