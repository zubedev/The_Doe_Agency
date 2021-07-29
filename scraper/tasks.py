from celery import shared_task

from scraper.scrapers import common


@shared_task
def scrape():
    common.scrape()
