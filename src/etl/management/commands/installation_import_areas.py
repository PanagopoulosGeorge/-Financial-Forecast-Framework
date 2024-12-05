from django.core.management.base import BaseCommand
from pathlib import Path
from geography.models import Area
import csv
from django.conf import settings
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
REL_PATH_AREAS = 'install/postgres/areas.csv'


class Command(BaseCommand):
    help = """Import areas from a CSV file into the Area model.
    Only used during installation of the application."""

    def handle(self, *args, **kwargs):
        csv_file = Path(settings.BASE_DIR.parent.resolve() / REL_PATH_AREAS)

        if not csv_file.exists():
            self.stderr.write(f"File {csv_file} not found.")
            return

        self.stdout.write(f'Importing areas from {csv_file}')

        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                code, name, description, currency, created_at, updated_at, population = row
                population = int(population.replace(',', '')
                                 ) if population != '' else None
                if not Area.objects.filter(code=code, name=name).exists():
                    area_instance = Area.objects.create(
                        code=code,
                        name=name,
                        description=description,
                        currency=currency,
                        created_at=pd.to_datetime('now'),
                        updated_at=pd.to_datetime('now'),
                        population=population)
                    self.stdout.write(f"Area imported: {area_instance.name}")
                    continue

                self.stdout.write(f"Area {name} already exists")
        self.stdout.write(self.style.SUCCESS('Areas imported successfully!'))
