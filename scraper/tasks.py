from celery import shared_task

from scraper.common import scrape
from scraper.check import check


@shared_task
def scrape_sites():
    """Task: Scrape active websites"""
    scrape()


@shared_task
def check_proxies():
    """Task: Check all available proxies"""
    check()
