from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management import BaseCommand

from scraper import utils


class Command(BaseCommand):
    def handle(self, *args, **options):
        sites = utils.get_sites()
        for site in sites:
            page = site.pages.filter(is_active=True).first()
            content = utils.get_content(page)
            soup = BeautifulSoup(content, "html.parser")
            file = (
                settings.BASE_DIR / "scraper" / "html" / f"{site.code.lower()}"
            )
            with open(file, "w") as f:
                f.write(soup.prettify())
