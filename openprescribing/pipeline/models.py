from __future__ import unicode_literals

from django.db import models

from django.contrib.postgres.fields import ArrayField, HStoreField


class Source(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    publisher = models.CharField(max_length=40)
    publication_schedule = models.CharField(max_length=40, null=True)
    publication_lag = models.CharField(max_length=40, null=True)
    notes = models.TextField(null=True)
    index_url = models.CharField(max_length=200)
    urls = HStoreField(null=True)
    requires_captcha = models.BooleanField(default=False)
    licence = models.CharField(max_length=40, null=True)
    licence_attributions = ArrayField(models.CharField(max_length=200), null=True)
    core_data = models.BooleanField(default=False)
    research = models.BooleanField(default=False)
