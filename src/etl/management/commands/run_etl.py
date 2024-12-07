from django.core.management.base import BaseCommand, CommandError
from .include.oecd import OECDClient
from .include.imf import IMFClient


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
        if source not in ('oecd', 'imf'):
            raise CommandError("Invalid source. Use 'oecd' or 'imf'")
        
        if source == 'oecd':
            print("Running ETL for OECD")
            oecd_client = OECDClient(mode)
            oecd_client.run()
        elif source == 'imf':
            print("Running ETL for IMF")
            imf_client = IMFClient(mode)
            imf_client.run()
        else:
            raise CommandError("Source does not exist")
        