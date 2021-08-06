import concurrent.futures
import random
import typing
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from logging import getLogger

import requests
import requests_cache
from bs4 import BeautifulSoup
from django.db.models import QuerySet
from django.utils import timezone
from requests import Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from project.test_urls import TEST_URLS
from project.user_agents import USER_AGENTS
from scraper.models import Website, Page, Proxy, Anonymity

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
) -> QuerySet[Page]:
    """List of active(by default) pages for a given website or website code
    Args:
        site: a related <Website> object
        site__code: a related <Website> object code string field
        is_active: a boolean active status of page
        kwargs: keyword arguments passed to <Page> objects filter
    Returns:
        QuerySet[Page]: A queryset of pages
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


def get_proxies(is_active: bool = True, **kwargs) -> QuerySet[Proxy]:
    """Returns available active proxies queryset
    Args:
        is_active[bool]: a boolean active status of proxy
        kwargs[dict]: keyword arguments passed to <Proxy> objects filter
    Returns:
        QuerySet[Proxy]
    """
    params = {"is_active": is_active, **kwargs}
    return Proxy.objects.filter(**params)


def get_random_working_proxy(
    output: str = "object", test_urls: list or tuple = None, **kwargs
) -> typing.Union[Proxy, dict, None]:
    """Returns a random working proxy in the form of object or dictionary
    Args:
        output[str]: Return type; <Proxy> object or values dictionary
        test_url[str]: URL to check the proxy against
        kwargs[dict]: extra filter to pass while retrieving proxies
    Returns:
        <Proxy> object | values dictionary
    """
    proxies = list(
        get_proxies(
            anonymity__in=[Anonymity.ANONYMOUS[0], Anonymity.ELITE[0]],
            **kwargs,
        )
    )
    if not proxies:
        return None

    random.shuffle(proxies)
    for proxy in proxies:
        kw = {"ip": proxy.ip, "port": proxy.port, "protocol": proxy.protocol}
        if test_urls:
            kw.update({"test_urls": test_urls})
        status, p_dict = test_ip_port(**kw)
        if status:
            if "dict" in output:
                return p_dict
            else:
                return proxy
    return None  # no working proxies fallback


def get_page_source(
    url: str, timeout: int = 30, retry: int = 3, use_proxy: bool = False
) -> bytes or None:
    """Returns non JS rendered page source code"""
    proxy_param = None
    if use_proxy:
        proxy = get_random_working_proxy()
        if proxy:
            proxy_param = {
                proxy.protocol.lower(): f"http://{proxy.ip}:{proxy.port}"
            }

    content = None
    try:  # catch requests exceptions
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        res: Response = requests.get(
            url, headers=headers, timeout=timeout, proxies=proxy_param
        )
        if res.ok:  # 2xx/3xx status
            content = res.content
        else:  # 4xx/5xx status
            logger.info(
                f"<{url}> Request failed, status_code={res.status_code}"
            )
    except Exception as e:
        logger.error(e)
        logger.info(f"<{url}> Failed to get page source")

    if not content and retry:
        return get_page_source(url, timeout, retry - 1)
    if not content and not retry and use_proxy:
        return get_page_source(url, timeout, 0, False)  # dont use proxy
    return content


def get_driver(headless: bool = True, add_proxy: bool = False, *args):
    """Returns a configure selenium web driver"""
    arguments = []
    if headless:
        arguments.append("--headless")

    arguments += [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--ignore-certificate-errors",
        "--window-size=1920x1080",
        f"--user-agent={random.choice(USER_AGENTS)}",
        "--incognito",
        *args,
    ]

    if add_proxy:
        proxy = get_random_working_proxy()
        proxy = (
            f"{proxy.protocol.lower()}://{proxy.ip}:{proxy.port}"
            if proxy
            else None
        )
        if proxy:
            arguments.append(f"--proxy-server={proxy}")

    options = ChromeOptions()
    for a in arguments:
        options.add_argument(a)
    return webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=options
    )


def get_js_page_source(url: str, retry: int = 3, use_proxy: bool = False):
    """Returns JS rendered page source code"""
    content = None
    try:  # catch requests exceptions
        driver = get_driver(add_proxy=use_proxy)
        driver.get(url)
        content = driver.page_source
        driver.quit()
    except Exception as e:
        logger.error(e)
        logger.info(f"<{url}> Failed to get page source")
    if not content and retry:
        return get_js_page_source(url, retry - 1)
    if not content and not retry and use_proxy:
        return get_js_page_source(url, 0, False)  # dont use proxy
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
        page_source = get_js_page_source(url)
    else:  # non js html page source
        page_source = get_page_source(url)

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
    proxy: dict = None,
    ip: str = None,
    port: typing.Union[int, str] = None,
    protocol: str = "http",
    test_urls: typing.Union[tuple, list] = tuple(
        random.choices(TEST_URLS, k=3)
    ),
    timeout: int = 30,
) -> tuple[bool, dict]:
    """Tests for a working proxy
    Args:
        proxy [dict]: Dictionary containing ip, port, protocol, etc
        ip [str]: If proxy[dict] not given, must provide the ip address
        port [str|int]: Must provide a port paired with ip address
        protocol [str]: Proxy protocol; default=http
        test_urls[tuple|list]: URLs to test the proxy against
        timeout [int]: Connection timeout in seconds; default=30
    Returns:
        tuple[bool, dict]: Status of Proxy, Proxy details
    Raises:
        ValueError: if proxy[dict] or ip:port not provided
    """
    if proxy and not ip and not port:
        ip = proxy.get("ip", None)
        port = proxy.get("port", None)
        protocol = proxy.get("protocol", protocol)
    if not ip and not port:
        raise ValueError("Must provide proxy or ip:port")
    if not proxy and ip and port:
        proxy = {"ip": ip, "port": port, "protocol": protocol}

    logger.debug(f"Testing proxy ip: {ip}, port: {port}, protocol: {protocol}")
    params = {protocol.lower(): f"http://{ip}:{port}"}

    count = 0
    for url in test_urls:
        try:  # test the proxy
            with requests_cache.disabled():
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                res = requests.get(
                    url, headers=headers, timeout=timeout, proxies=params
                )
            if res.ok:
                count += 1
        except Exception as e:
            logger.error(f"<{params}> {e}")

    if count >= len(test_urls) - 1:
        return True, proxy
    else:
        return False, proxy


def get_tested(proxies: list[dict], timeout: int = 30) -> list[dict]:
    """Test extracted proxies against a TEST_URL
    Args:
        proxies: List of proxies in `dict` form containing `ip` and `port`, etc
        timeout: seconds to wait before timing out the testing request
    Returns:
        list: A list of tested proxies
    """
    logger.info("Commenced proxy testing...")
    tested = []  # list of tested proxies

    with ThreadPoolExecutor() as executor:
        futures = []

        for p in proxies:
            if Proxy.objects.filter(ip=p["ip"], port=p["port"]).exists():
                continue  # skip testing existing proxy, will bulk test in bg
            kwargs = {"proxy": p, "timeout": timeout}
            futures.append(executor.submit(test_ip_port, **kwargs))

        for future in concurrent.futures.as_completed(futures):
            try:
                status, proxy = future.result()
                if status:  # add tested proxy to list if connectable
                    tested.append(proxy)
            except Exception as e:
                logger.error(e)

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
