from django.core.management.base import BaseCommand, CommandError
from .include.oecd import OECDClient


class Command(BaseCommand):
    help = 'Generates user report'

    # def add_arguments(self, parser):
    #     parser.add_argument('user_id', nargs='+', type=int)

    def handle(self, *args, **kwargs):
        transformer = OECDClient()

        transformer.run_extract_transform_save()
