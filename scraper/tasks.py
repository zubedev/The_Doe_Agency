from celery import shared_task

from scraper import scrape
from scraper import check


@shared_task
def scrape_sites():
    """Task: Scrape active websites"""
    scrape.scrape()


@shared_task
def check_proxies():
    """Task: Check all available proxies"""
    check.check()
