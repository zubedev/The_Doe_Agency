from django.core.management import BaseCommand

from scraper.scrape import scrape


class Command(BaseCommand):
    def handle(self, *args, **options):
        return scrape()
