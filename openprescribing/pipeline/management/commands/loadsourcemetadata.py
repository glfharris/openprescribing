import json
import os

from django.conf import settings
from django.core.management import BaseCommand

from ...models import Source


class Command(BaseCommand):
    help = 'Load metadata about sources from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?')

    def handle(self, *args, **kwargs):
        if kwargs['path'] is None:
            path = os.path.join(settings.SITE_ROOT, 'pipeline', 'data', 'sources.json')
        else:
            path = kwargs['path']

        with open(path) as f:
            records = json.load(f)

        for record in records:
            try:
                source = Source.objects.get(id=record['id'])
                changed = False
                for k, v in record.items():
                    if getattr(source, k) != v:
                        setattr(source, k, v)
                        changed = True
                if changed:
                    source.save()
                    self.stdout.write('Updated {}'.format(record['id']))
            except Source.DoesNotExist:
                Source.objects.create(**record)
                self.stdout.write('Created {}'.format(record['id']))
