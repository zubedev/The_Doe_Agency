from celery import shared_task

from scraper.scrapers.common import scrape as scrape_sites
from scraper.check import check as check_proxies


@shared_task
def scrape():
    """Task: Scrape active websites"""
    scrape_sites()


@shared_task
def check():
    """Task: Check all available proxies"""
    check_proxies()
