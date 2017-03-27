from __future__ import print_function

from collections import OrderedDict
import json

with open('manifest.json') as f:
    raw_sources = json.load(f)

sources = []

keys = [
    'id',
    'title',
    'description',
    'publisher',
    'publication_schedule',
    'publication_lag',
    'index_url',
    'urls',
    'notes',
    'requires_captcha',
    'licence',
    'licence_attributions',
]

non_source_keys = [
    'fetcher',
    'depends_on',
    'always_import',
    'importers',
    'before_import',
    'after_import',
    'filename_pattern',
    'tags',
]

for raw_source in raw_sources:
    if not raw_source.get('publisher'):
        print('No publisher for {}'.format(raw_source['id']))
        continue
    for k in raw_source.keys():
        if k not in keys and k not in non_source_keys:
            print('Unexpected key {} for {}'.format(k, raw_source['id']))

    source = OrderedDict([[k, raw_source[k]] for k in keys if raw_source.get(k)])

    if 'core_data' in raw_source['tags']:
        source['core_data'] = True
    if 'research' in raw_source['tags']:
        source['research'] = True

    sources.append(source)


with open('data/sources.json', 'w') as f:
    json.dump(sources, f, indent=4)
