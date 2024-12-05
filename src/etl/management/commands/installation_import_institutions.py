from django.core.management.base import BaseCommand
from pathlib import Path
from institution.models import Institution
import csv
from django.conf import settings
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
REL_PATH_INSTITUTIONS = 'install/postgres/institutions.csv'


class Command(BaseCommand):
    help = """Import institutions from a CSV file into the Institutions model.
    Only used during installation of the application."""

    def handle(self, *args, **kwargs):
        csv_file = Path(settings.BASE_DIR.parent.resolve() /
                        REL_PATH_INSTITUTIONS)
        if not csv_file.exists():
            self.stderr.write(f"File {csv_file} not found.")
            return
        self.stdout.write(f'Importing institutions from {csv_file}...')
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(
                f, delimiter=',', quotechar='"', skipinitialspace=True)
            next(reader)
            for row in reader:
                abbreviation, name, description, url, type, country = row
                created_at = pd.to_datetime('now')
                if not Institution.objects.filter(abbreviation=abbreviation, name=name).exists():
                    institution_instance = Institution.objects.create(
                        abbreviation=abbreviation,
                        name=name,
                        description=description,
                        url=url,
                        type=type,
                        country=country,
                        created_at=created_at)
                    self.stdout.write(
                        f"Institution {institution_instance.abbreviation} imported.")
                    continue
                # institution_instance = Institutions.objects.create(instid=instid, name=name, abbreviation=abbreviation, description=description, url=url, country=country, type=type)
                self.stdout.write(
                    f"Institution {institution_instance.abbreviation} already exists.")
        self.stdout.write(self.style.SUCCESS(
            'Institutions imported successfully!'))
