from django.core.management import BaseCommand

from scraper.scrapers.common import scrape
from scraper.check import check


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(scrape())
        print(check())
