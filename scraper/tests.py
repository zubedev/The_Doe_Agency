from http import HTTPStatus
from unittest import mock

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import QuerySet
from django.test import Client, TestCase
from django.urls import reverse
from requests import Response
from selenium.webdriver.chrome.webdriver import WebDriver

import scraper.views
from scraper import utils, tasks, check, scrape
from scraper.models import Website, Page, Proxy, Check, Scrape
from scraper.scrapers import sslp, spy1, fpls, fpcz

USER_MODEL = get_user_model()


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


class TasksTestCase(TestCase):
    def test_scrape_sites(self):
        with mock.patch("scraper.scrape.scrape") as mock_scrape:
            mock_scrape.return_value = []
            tasks.scrape_sites()
            self.assertEqual(mock_scrape.call_count, 1)

    def test_check_proxies(self):
        with mock.patch("scraper.check.check") as mock_check:
            tasks.check_proxies()
            self.assertEqual(mock_check.call_count, 1)


class ScrapeTestCase(TestCase):
    fixtures = [
        "group.json",
        "user.json",
        "crontabschedule.json",
        "intervalschedule.json",
        "website.json",
        "page.json",
    ]
    test_ip_port = {"ip": "127.1.2.3", "port": 8000}
    test_url = "http://127.1.2.3/"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.site = Website.objects.create(
            name="HTTPbin", code="HTTP", url="https://httpbin.org"
        )
        cls.page = Page.objects.create(site=cls.site, path="/")
        cls.proxy = Proxy.objects.create(
            ip="127.0.0.1",
            port="8000",
            country="BD",
            anonymity="ANM",
            protocol="HTTPS",
        )

    def test_get_sites(self) -> None:
        sites = utils.get_sites()
        self.assertIsInstance(sites, QuerySet)
        self.assertIsInstance(sites.first(), Website)  # depends on fixtures

    def test_get_pages(self) -> None:
        with self.assertRaises(ValueError):
            utils.get_pages()
        site = Website.objects.filter(is_active=True).first()

        pages = utils.get_pages(site)
        self.assertIsInstance(pages, QuerySet)
        self.assertIsInstance(pages.first(), Page)  # depends on fixtures

        pages = utils.get_pages(site__code=site.code)
        self.assertIsInstance(pages, QuerySet)
        self.assertIsInstance(pages.first(), Page)  # depends on fixtures

    def test_get_proxies(self) -> None:
        proxies = utils.get_proxies()
        self.assertIsInstance(proxies, QuerySet)
        self.assertIsInstance(proxies.first(), Proxy)

    @mock.patch("scraper.utils.test_ip_port")
    @mock.patch("scraper.utils.get_proxies")
    def test_get_random_working_proxy(self, mock_proxies, mock_test_ip_port):
        p_dict = {
            "ip": self.proxy.ip,
            "port": self.proxy.port,
            "protocol": self.proxy.protocol,
        }

        mock_proxies.return_value = Proxy.objects.none()
        proxy = utils.get_random_working_proxy()
        self.assertIsNone(proxy)

        mock_proxies.return_value = Proxy.objects.filter(pk=self.proxy.pk)
        mock_test_ip_port.return_value = False, p_dict
        proxy = utils.get_random_working_proxy()
        self.assertIsNone(proxy)

        mock_test_ip_port.return_value = True, p_dict
        proxy = utils.get_random_working_proxy()
        self.assertEqual(proxy, self.proxy)

        proxy = utils.get_random_working_proxy(output="dict")
        self.assertDictEqual(proxy, p_dict)

    @mock.patch("scraper.utils.get_random_working_proxy")
    def test_get_page_source(self, mock_proxy) -> None:
        mock_proxy.return_value = None
        content = utils.get_page_source(settings.TEST_URL)
        self.assertIsNotNone(content)
        content = utils.get_page_source(settings.TEST_URL + "/test", retry=0)
        self.assertIsNone(content)
        content = utils.get_page_source(self.test_url, retry=0)
        self.assertIsNone(content)

        mock_proxy.return_value = self.proxy
        with mock.patch.object(requests, "get") as mock_request:
            response = Response()
            response.status_code = 200
            response._content = b"content"
            mock_request.return_value = response
            content = utils.get_page_source(settings.TEST_URL)
            self.assertIsNotNone(content)

    @mock.patch("scraper.utils.get_random_working_proxy")
    def test_get_driver(self, mock_proxy) -> None:
        mock_proxy.return_value = None
        driver = utils.get_driver()
        self.assertIsInstance(driver, WebDriver)
        driver.quit()

        mock_proxy.return_value = self.proxy
        driver = utils.get_driver()
        self.assertIsInstance(driver, WebDriver)
        driver.quit()

    def test_get_js_page_source(self) -> None:
        content = utils.get_js_page_source(settings.TEST_URL)
        self.assertIsNotNone(content)
        content = utils.get_js_page_source(self.test_url, retry=0)
        self.assertIsNone(content)

    def test_get_content(self) -> None:
        with self.assertRaises(ValueError):
            utils.get_content()
        with mock.patch(
            "scraper.utils.get_js_page_source"
        ) as mock_page_source:
            mock_page_source.return_value = b'{"success": true}'
            content = utils.get_content(url=settings.TEST_URL, has_js=True)
            self.assertIsNotNone(content)
        with mock.patch("scraper.utils.get_page_source") as mock_page_source:
            mock_page_source.return_value = b'{"success": true}'
            content = utils.get_content(self.page)
            self.assertIsNotNone(content)

    def test_slurp(self) -> None:
        soup = BeautifulSoup(
            utils.get_content(url=self.page.full_path), "html.parser"
        )
        with self.assertRaises(ValueError):
            utils.slurp(soup, "qwerty")
        with self.assertRaises(ValueError):
            utils.slurp(soup)  # val or kv not provided

        slurpy = utils.slurp(soup, kv={"id": "swagger-ui"})
        self.assertIsNotNone(slurpy)
        slurpy = utils.slurp(soup, "select", val="small")
        self.assertIsNotNone(slurpy)

    def test_test_ip_port(self) -> None:
        with self.assertRaises(ValueError):
            utils.test_ip_port()

        with mock.patch.object(requests, "get") as mock_request:
            response = Response()
            response.status_code = 200
            mock_request.return_value = response
            result, proxy = utils.test_ip_port(self.test_ip_port)
            self.assertTrue(result)
            self.assertIn("ip", proxy)

            response.status_code = 404
            result, proxy = utils.test_ip_port(**self.test_ip_port)
            self.assertFalse(result)
            self.assertIn("ip", proxy)

    def test_get_tested(self) -> None:
        existing_ip_port = {"ip": self.proxy.ip, "port": self.proxy.port}
        with mock.patch("scraper.utils.test_ip_port") as mock_test_ip_port:
            mock_test_ip_port.return_value = True, self.test_ip_port
            tested = utils.get_tested([self.test_ip_port, existing_ip_port])
            self.assertIn(self.test_ip_port, tested)
            self.assertNotIn(existing_ip_port, tested)

    def test_save_to_db(self) -> None:
        proxy = self.test_ip_port.copy()
        proxy.update({"country": "AU", "anonymity": "NOA", "protocol": "HTTP"})
        saved = utils.save_to_db(self.page, [proxy, self.test_ip_port])
        self.assertIsInstance(saved[0], Proxy)

    @mock.patch("scraper.utils.get_proxies")
    def test_check(self, mock_get_proxies: mock.Mock) -> None:
        self.assertFalse(Check.objects.exists())
        mock_get_proxies.return_value = [self.proxy]

        with mock.patch("scraper.utils.test_ip_port") as mock_test_ip_port:
            mock_test_ip_port.return_value = True, {
                "ip": self.proxy.ip,
                "port": self.proxy.port,
                "protocol": self.proxy.protocol,
            }
            check.check()
            self.assertTrue(Check.objects.exists())

    @mock.patch.object(utils, "save_to_db")
    @mock.patch.object(utils, "get_tested")
    @mock.patch.object(utils, "get_content")
    def test_scrape_page(self, mock_content, mock_tested, mock_saved):
        with self.assertRaises(ValueError):
            scrape.scrape_page()

        proxies = scrape.scrape_page(pk=99)  # non-existing pk
        self.assertListEqual(proxies, [])
        proxies = scrape.scrape_page(self.page)
        self.assertListEqual(proxies, [])  # no parser found

        mock_content.return_value = """
            <html><body><table><tbody><tr>
                <td>169.192.168.254</td>
                <td>65533</td>
                <td>US</td>
                <td>ANM</td>
                <td>HTTP</td>
            </tr></tbody></table></body></html>
        """
        mock_tested.return_value = [
            {
                "ip": "169.192.168.254",
                "port": "65533",
                "country": "US",
                "anonymity": "ANM",
                "protocol": "HTTP",
            }
        ]
        mock_saved.return_value = [self.proxy]

        with mock.patch.object(Page, "get_parser") as parser:
            parser.return_value = lambda x: x
            proxies = scrape.scrape_page(self.page)
            self.assertListEqual(proxies, [self.proxy])
            mock_saved.side_effect = Exception
            proxies = scrape.scrape_page(self.page)
            self.assertListEqual(proxies, [])

    def test_scrape_site(self):
        scrape_obj = Scrape.objects.create()
        with self.assertRaises(ValueError):
            scrape.scrape_site()

        proxies, obj = scrape.scrape_site(pk=99, obj=scrape_obj)
        self.assertListEqual(proxies, [])
        self.assertEqual(obj, scrape_obj)

        proxies, obj = scrape.scrape_site(code="test", obj=scrape_obj)
        self.assertListEqual(proxies, [])
        self.assertEqual(obj, scrape_obj)

        with mock.patch("scraper.scrape.scrape_page") as mock_scrape_page:
            mock_scrape_page.return_value = [self.proxy]
            proxies, obj = scrape.scrape_site(self.site, obj=scrape_obj)
            self.assertListEqual(proxies, [self.proxy])
            self.assertEqual(obj, scrape_obj)

            mock_scrape_page.side_effect = Exception
            proxies, obj = scrape.scrape_site(self.site, obj=scrape_obj)
            self.assertListEqual(proxies, [])
            self.assertEqual(obj, scrape_obj)

    @mock.patch("scraper.scrape.scrape_site")
    def test_scrape(self, mock_scrape_site):
        self.assertFalse(Scrape.objects.exists())

        mock_scrape_site.return_value = [self.proxy], Scrape()
        proxies = scrape.scrape()
        self.assertTrue(proxies)
        self.assertTrue(Scrape.objects.exists())

        mock_scrape_site.side_effect = Exception
        proxies = scrape.scrape()
        self.assertListEqual(proxies, [])


class ScrapersTestCase(TestCase):
    def test_sslp(self) -> None:
        soup = BeautifulSoup(sslp.content, "html.parser")
        proxies = sslp.parse(soup)
        self.assertDictEqual(
            proxies[0],
            {
                "ip": "127.1.2.3",
                "port": 12345,
                "country": "BD",
                "anonymity": "ANM",
                "protocol": "HTTP",
            },
        )

    def test_spy1(self) -> None:
        soup = BeautifulSoup(spy1.content, "html.parser")
        proxies = spy1.parse(soup)
        self.assertDictEqual(
            proxies[0],
            {
                "ip": "127.1.2.3",
                "port": 12345,
                "country": "BD",
                "anonymity": "ANM",
                "protocol": "HTTP",
            },
        )

    def test_fpls(self) -> None:
        soup = BeautifulSoup(fpls.content, "html.parser")
        proxies = fpls.parse(soup)
        self.assertDictEqual(
            proxies[0],
            {
                "ip": "127.1.2.3",
                "port": 12345,
                "country": "BD",
                "anonymity": "ANM",
                "protocol": "HTTP",
            },
        )

    def test_fpcz(self) -> None:
        soup = BeautifulSoup(fpcz.content, "html.parser")
        proxies = fpcz.parse(soup)
        self.assertDictEqual(
            proxies[0],
            {
                "ip": "127.1.2.3",
                "port": 12345,
                "country": "BD",
                "anonymity": "ANM",
                "protocol": "HTTP",
            },
        )


class APIViewTests(TestCase):
    fixtures = [
        "group.json",
        "user.json",
        "crontabschedule.json",
        "intervalschedule.json",
        "website.json",
        "page.json",
    ]
    scrape_sites_url = reverse("scraper:scrape_sites")
    check_proxies_url = reverse("scraper:check_proxies")

    def setUp(self) -> None:
        self.testuser = USER_MODEL.objects.get(username="testuser")
        self.client = Client()

    def test_anonymous_view(self) -> None:
        self.client.logout()  # sanity check
        response = self.client.post(self.scrape_sites_url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)  # 401
        response = self.client.post(self.check_proxies_url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)  # 401

    def test_authenticated_view(self) -> None:
        self.client.force_login(self.testuser)
        task = mock.Mock()
        task.id = "task_id"
        task.status = "PENDING"

        with mock.patch.object(
            scraper.tasks.scrape_sites, "apply_async"
        ) as mock_scrape:
            mock_scrape.return_value = task
            response = self.client.post(self.scrape_sites_url)
            self.assertEqual(response.status_code, HTTPStatus.OK)  # 200
            self.assertTrue(mock_scrape.called)  # called once
        with mock.patch.object(
            scraper.tasks.check_proxies, "apply_async"
        ) as mock_check:
            mock_check.return_value = task
            response = self.client.post(self.check_proxies_url)
            self.assertEqual(response.status_code, HTTPStatus.OK)  # 200
            self.assertTrue(mock_check.called)  # called once
