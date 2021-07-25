from django.core.management import BaseCommand

from scraper.scrapers.common import scrape


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(scrape())
