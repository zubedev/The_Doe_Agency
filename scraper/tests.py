from unittest import mock

from django.core.management import call_command
from django.test import TestCase


class CommandTestCase(TestCase):
    def test_scrape_sites(self):
        with mock.patch("scraper.scrape.scrape") as mock_scrape:
            mock_scrape.return_value = []
            call_command("scrape_sites")
            self.assertEqual(mock_scrape.call_count, 1)

    def test_check_proxies(self):
        with mock.patch("scraper.check.check") as mock_check:
            call_command("check_proxies")
            self.assertEqual(mock_check.call_count, 1)
