from datetime import timedelta
from logging import getLogger
import typing

import requests
import requests_cache
from bs4 import BeautifulSoup
from django.db.models import QuerySet
from django.utils import timezone
from requests import Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from project.settings import TEST_URL
from scraper.models import Website, Page, Proxy

logger = getLogger(__name__)


def get_sites(is_active=True, **kwargs) -> QuerySet[Website]:
    """Returns active <Website> queryset
    Args:
        is_active: a boolean active status of <Website> object
        kwargs: keyword arguments passed to <Website> objects filter
    Returns:
        Queryset[<Website>]: <Website> queryset
    """
    logger.info("Getting sites...")
    logger.debug(f"is_active: {is_active}, kwargs: {kwargs}")

    params = {"is_active": is_active, **kwargs}
    sites = Website.objects.filter(**params)

    logger.info("Returning website queryset")
    logger.debug(f"Sites: {sites}")
    return sites


def get_pages(
    site: Website = None, site__code: str = None, is_active=True, **kwargs
) -> list[Page]:
    """List of active(by default) pages for a given website or website code
    Args:
        site: a related <Website> object
        site__code: a related <Website> object code string field
        is_active: a boolean active status of page
        kwargs: keyword arguments passed to <Page> objects filter
    Returns:
        list: A list of pages
    Raises:
        ValueError: if neither site or site__code is provided
    """
    logger.info("Getting pages...")
    logger.debug(
        f"site: {site}, site__code: {site__code}, "
        f"is_active: {is_active}, kwargs: {kwargs}"
    )

    params = {"is_active": is_active}

    if site and isinstance(site, Website):
        params.update({"site": site})
    elif site__code and isinstance(site__code, str):
        params.update({"site__code": site__code.upper()})
    else:
        raise ValueError("Must provide a <Website> object or code (str)")

    params.update(**kwargs)
    pages = Page.objects.select_related("site").filter(**params)

    logger.info("Returning list of pages.")
    logger.debug(f"Pages: {pages}")
    return pages


def _get_page_source(url: str, timeout: int = 10) -> bytes or None:
    """Returns non JS rendered page source code"""
    try:  # catch requests exceptions
        res: Response = requests.get(url, timeout=timeout)
        if not res.ok:  # 4xx status
            logger.info(
                f"<{url}> Request failed, status_code={res.status_code}"
            )
            return
    except Exception as e:
        logger.error(e)
        logger.info(f"<{url}> Failed to get page source")
        return
    return res.content


def _get_driver(browser: str = "Chrome", headless: bool = True, *args):
    """Returns a configure selenium web driver"""
    arguments = ["--window-size=1920,1080", "--incognito", *args]
    if headless:
        arguments.append("--headless")

    if browser.lower() == "firefox":
        options = FirefoxOptions()
        for a in args:
            options.add_argument(a)
        driver = webdriver.Firefox(
            executable_path=GeckoDriverManager().install(), options=options
        )
    else:  # Chrome, by default
        options = ChromeOptions()
        for a in args:
            options.add_argument(a)
        driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=options
        )

    return driver


def _get_js_page_source(url: str):
    """Returns JS rendered page source code"""
    try:  # catch requests exceptions
        driver = _get_driver()
        driver.get(url)
        content = driver.page_source
        driver.quit()
    except Exception as e:
        logger.error(e)
        logger.info(f"<{url}> Failed to get page source")
        return
    return content


def get_content(
    page: Page = None,
    url: str = None,
    has_js: bool = None,
    cache: int = 5 * 60,
):
    """Gets the page source code or content from a given <Page> or url
    Args:
        page: a <Page> object
        url: a full path to the page, including protocol://domain/path/
        has_js: a boolean indicating if page is rendered with JavaScript
        cache: seconds to keep the request/response cached
    Returns:
        Page source or content typically for use in BeautifulSoup
    Raises:
        ValueError: if neither page nor url is provided
    """
    logger.info("Getting content...")
    logger.debug(f"page: {page}, url: {url}, has_js: {has_js}, cache: {cache}")

    if not page and not url:
        raise ValueError("Must provide a <Page> object or url (str)")
    elif page and not url:
        url = page.full_path
    if page and has_js is None:
        has_js = page.has_js

    # cache page for 5 minutes (default)
    requests_cache.install_cache(expire_after=timedelta(seconds=cache))

    if has_js:  # js rendered via selenium
        page_source = _get_js_page_source(url)
    else:  # non js html page source
        page_source = _get_page_source(url)

    logger.info("Returning page source.")
    logger.debug(f"Page source: {page_source}")
    return page_source


def slurp(
    soup: BeautifulSoup, attr: str = "find", val: str = None, kv: dict = None
):
    """Slurps up that tasty tasty soup!
    Args:
        soup: parsed <BeautifulSoup> object
        attr: method to slurp that soup, ie. `find` or `select` etc
        val: value to pass to the `attr` method
        kv: dict containing a key value pair to pass to the `attr` method
    Returns:
        A soup object or a list of soup objects
    Raises:
        ValueError: if `attr` is invalid or val/kv is not provided
    """
    logger.debug(f"soup: {soup}, attr: {attr}, val: {val}, kv: {kv}")
    if not hasattr(soup, attr):
        raise ValueError(f"Invalid attribute provided: {attr}")
    if not val and not kv:
        raise ValueError("Must provide either val or kv")
    if kv:
        slurpy = getattr(soup, attr)(**kv)
    else:
        slurpy = getattr(soup, attr)(val)
    logger.debug(f"slupry: {slurpy}")
    return slurpy


def test_ip_port(
    ip: str,
    port: typing.Union[int, str],
    protocol: str = "http",
    test_url: str = TEST_URL,
    timeout: int = 10,
) -> bool:
    """Returns True for a valid proxy"""
    logger.debug(f"Testing proxy ip: {ip}, port: {port}, protocol: {protocol}")
    proxy = {protocol.lower(): f"http://{ip}:{port}"}

    try:  # test the proxy
        with requests_cache.disabled():
            res = requests.get(test_url, proxies=proxy, timeout=timeout)
        return res.ok
    except Exception as e:
        logger.error(f"<{proxy}> {e}")
        return False


def get_tested(
    proxies: list[dict], test_url: str = TEST_URL, timeout: int = 10
) -> list[dict]:
    """Test extracted proxies against a TEST_URL
    Args:
        proxies: List of proxies in `dict` form containing `ip` and `port`, etc
        test_url: URL to test proxies against, default set in settings.py
        timeout: seconds to wait before timing out the testing request
    Returns:
        list: A list of tested proxies
    """
    logger.info("Commenced proxy testing...")
    tested = []  # list of tested proxies

    for p in proxies:
        if Proxy.objects.filter(ip=p["ip"], port=p["port"]).exists():
            continue  # no need to test proxy already in db
        status = test_ip_port(
            p["ip"], p["port"], p["protocol"], test_url, timeout
        )
        if status:  # add tested proxy to list if connectable
            tested.append(p)

    logger.info("Proxy testing complete")
    logger.debug(f"Tested proxies: {tested}")
    return tested


def save_to_db(page: Page, proxies: list[dict]) -> list[Proxy]:
    """Save a list of tested proxies to the database
    Args:
        page: <Page> object
        proxies: List of tested proxies in `dict`
    Returns:
        bool: status of the operation
    """
    logger.info("Commenced saving to database...")
    saved = []  # list of saved proxies to be returned

    for p in proxies:
        try:
            obj, _ = Proxy.objects.get_or_create(
                ip=p["ip"],  # ip address
                port=p["port"],  # port
                country=p["country"],  # country code
                anonymity=p["anonymity"],
                protocol=p["protocol"],
                checked_at=timezone.now(),
            )
            obj.found_in.add(page)  # add the m2m field
            obj.save()  # finally save the proxy
            saved.append(obj)
            logger.debug(f"{obj} saved in database")
        except Exception as e:
            logger.error(e)
            logger.debug(f"Failed to save tested proxy {p['ip']}:{p['port']}")

    logger.info("Saved to database.")
    logger.debug(f"Proxies: {saved}")
    return saved


def scrape_page(
    page: Page = None, pk: int = None, **kwargs: dict
) -> list[Proxy]:
    """Single <Page> scrape function
    Args:
        page: <Page> object
        pk: <Page> object pk/id (int)
        kwargs: keyword arguments passed to <Page> objects filter
    Returns:
        list: List of proxies in `dict`
    """
    if not page and not pk:
        raise ValueError("Must provide at least: `page` or `pk`")
    if not page and pk:
        params = {"pk": pk, **kwargs}
        page = Page.objects.select_related("site").filter(**params).first()
    if not page:
        return []

    parser = page.get_parser()
    if not parser:
        return []

    try:
        logger.info(f"{page} Commenced scraping...")

        content = get_content(page)  # page source
        soup = BeautifulSoup(content, "html.parser")  # parse the html content
        proxies = parser(soup)  # list of extracted proxies
        tested = get_tested(proxies)  # list of tested proxies
        saved_to_db = save_to_db(page, tested)  # list of saved proxies

        logger.info(f"{page} Scrape complete.")
        return saved_to_db
    except Exception as e:
        logger.error(f"{page} {e}")
        logger.warning(f"{page} Scrape failed.")
        return []


def scrape_site(
    site: Website = None, code: str = None, pk: int = None, **kwargs: dict
) -> list[Proxy]:
    """Single <Website> scrape function
    Args:
        site: <Website> object
        code: <Website> `code` value (str)
        pk: <Website> object pk/id (int)
        kwargs: keyword arguments passed to <Website> objects filter
    Returns:
        list: List of proxies in `dict`
    """
    if not site and not code and not pk:
        raise ValueError("Must provide at least: `site` or `code` or `pk`")
    if not site and (code or pk):
        params = {**kwargs}
        if pk:
            params.update({"pk": pk})
        elif code:
            params.update({"code": code})
        site = (
            Website.objects.prefetch_related("pages").filter(**params).first()
        )
    if not site:
        return []

    logger.info(f"{site} Commenced scraping...")
    pages = site.pages.select_related("site").filter(is_active=True)

    proxy_list: list[Proxy] = []
    for page in pages:
        try:
            proxy_list += scrape_page(page)
        except Exception as e:  # continue to next loop for any error
            logger.error(e)
            continue

    logger.info(f"{site} Scrape complete.")
    return proxy_list


def scrape(
    sites: typing.Union[list[Website], QuerySet[Website]] = None
) -> list[Proxy]:
    """Main scrape function
    Args:
        sites: List of <Website> or QuerySet[<Website>]
    Returns:
        list: List of proxies in `dict`
    """
    if not sites:
        sites = get_sites()  # is_active=True (default)

    proxy_list: list[Proxy] = []
    for site in sites:
        try:
            proxy_list += scrape_site(site)
        except Exception as e:  # continue to next loop for any error
            logger.error(e)
            continue

    logger.debug(f"Proxies: {proxy_list}")
    return proxy_list