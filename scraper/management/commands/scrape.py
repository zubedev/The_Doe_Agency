from django.core.management import BaseCommand

from scraper.scrapers import sslproxies, spysone, freeproxylists


class Command(BaseCommand):
    def handle(self, *args, **options):
        sslproxies.scrape()
        # freeproxy.scrape()
        spysone.scrape()
        freeproxylists.scrape()
