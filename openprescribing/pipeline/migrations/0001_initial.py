# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-03-26 15:35
from __future__ import unicode_literals

from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        HStoreExtension(),
    ]