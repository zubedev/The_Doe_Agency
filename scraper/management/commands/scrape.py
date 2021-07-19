from django.core.management import BaseCommand

from scraper.scrapers import sslproxies


class Command(BaseCommand):
    def handle(self, *args, **options):
        sslproxies.scrape_index()
