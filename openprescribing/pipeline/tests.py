import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from .models import Source


class LoadSourceMetadataTests(TestCase):
    def test_source_added(self):
        '''Test loading metadata when source is added'''
        call_command('loadsourcemetadata', self._source_path(0))
        call_command('loadsourcemetadata', self._source_path(1))
        self.assertEqual(Source.objects.count(), 3)
        source = Source.objects.get(id='source-c')
        self.assertEqual(source.title, 'Source C')

    def test_source_changed(self):
        '''Test loading metadata when source has changed'''
        call_command('loadsourcemetadata', self._source_path(0))
        call_command('loadsourcemetadata', self._source_path(2))
        self.assertEqual(Source.objects.count(), 2)
        source = Source.objects.get(id='source-b')
        self.assertEqual(source.title, 'Sauce B')

    def test_no_changes(self):
        '''Test loading metadata with no changes'''
        call_command('loadsourcemetadata', self._source_path(0))
        call_command('loadsourcemetadata', self._source_path(0))
        self.assertEqual(Source.objects.count(), 2)

    def test_with_real_data(self):
        '''Test that real data in sources.json can be loaded'''
        call_command('loadsourcemetadata')

        source = Source.objects.get(id='bnf_codes')
        self.assertEqual(source.title, 'Human readable terms for BNF prescription codes')

    def _source_path(self, ix):
        return os.path.join(settings.SITE_ROOT, 'pipeline', 'test-data', 'sources-{}.json'.format(ix))
