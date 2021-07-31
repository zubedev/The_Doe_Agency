from django.core.management import BaseCommand

from scraper.check import check


class Command(BaseCommand):
    def handle(self, *args, **options):
        check()
