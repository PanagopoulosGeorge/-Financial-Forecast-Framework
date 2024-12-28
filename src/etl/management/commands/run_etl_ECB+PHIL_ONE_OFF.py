from django.core.management.base import BaseCommand, CommandError
from .include.oecd import OECDClient
from .include.imf import IMFClient
from .include.philadephia import PhiladelphiaClient
from .include.ecb import ECBClient
import time

class Command(BaseCommand):
    help = 'Run ETL process for each data source'

    def add_arguments(self, parser):
        parser.add_argument('--mode', type=str,
                            help='Mode to run the ETL process (t, e, l, etl for full process)')
        parser.add_argument('--source', type=str,
                            help='Run ETL process for a specific source')
        
    def handle(self, *args, **kwargs):
        mode = kwargs['mode']
        source = kwargs['source']
        if mode not in ['t', 'e', 'l', 'etl']:
            raise CommandError("Invalid mode. Use 't', 'e', 'l', or 'etl'")
        if source not in ('oecd', 'imf', 'philadelphia', 'ecb'):
            raise CommandError("Invalid source. Use 'oecd' or 'imf' or 'philadelphia' or 'ecb'")
        
        if source == 'oecd':
            print("Running ETL for OECD")
            oecd_client = OECDClient(mode)
            oecd_client.run()
        elif source == 'imf':
            print("Running ETL for IMF")
            imf_client = IMFClient(mode)
            imf_client.run()
        elif source == 'philadelphia':
            print("Running ETL for Philadelphia")
            start_year = 2020
            end_year = 2024
            start_quarter = 1
            end_quarter = 4
            for year in range(start_year, end_year+1):
                for quarter in range(start_quarter, end_quarter+1):
                    url = f'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/spf-q{quarter}-{year}'
                    philly_client = PhiladelphiaClient(url, mode)
                    philly_client.run()
                    time.sleep(2)
                    self.stdout.write(self.style.SUCCESS(f"Successfully extracted data for {year} Q{quarter}"))
                    time.sleep(2)
            
        elif source == 'ecb':
            print("Running ETL for ECB")
            start_year = 2020
            end_year = 2024
            start_quarter = 1
            end_quarter = 4
            for year in range(start_year, end_year+1):
                for quarter in range(start_quarter, end_quarter+1):
                    url = f'https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/table_3_{year}q{quarter}.en.html'
                    ecb_client = ECBClient(url, mode)
                    ecb_client.run()
                    time.sleep(2)
                    self.stdout.write(self.style.SUCCESS(f"Successfully extracted data for {year} Q{quarter}"))
                    time.sleep(2)
        else:
            raise CommandError("Source does not exist")
        