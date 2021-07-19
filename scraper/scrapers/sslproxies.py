from datetime import timedelta
from distutils.util import strtobool
from logging import getLogger

import requests
from django.utils import timezone
from requests import Response
import requests_cache
from bs4 import BeautifulSoup

from scraper.models import Page, Proxy, Anonymity, Protocol

logger = getLogger(__name__)

WEBSITE = "SSLProxies"
CODE = "SSLP"
TEST_URL = "https://httpbin.org/ip"


def scrape_index():
    page = (
        Page.objects.select_related("site")
        .filter(
            site__code=CODE,
            path__in=["#/", "index.html", "home.html"],
            is_active=True,
        )
        .first()
    )

    # dont continue scrape if no page object
    if not page:
        logger.info(f"<{WEBSITE}: {CODE}> Index page not found, exiting")
        return
    logger.info(f"{page} Commenced scraping...")

    # cache page for 5 minutes
    requests_cache.install_cache(expire_after=timedelta(minutes=5))
    # get the html page
    try:  # catch requests exceptions
        res: Response = requests.get(page.full_path, timeout=10)
        if not res.ok:  # 4xx status
            logger.info(
                f"<{WEBSITE}: {CODE}> {page} "
                f"Request failed, status_code={res.status_code}"
            )
            return
    except Exception as e:
        logger.error(e)
        logger.info(
            f"<{WEBSITE}: {CODE}> {page} "
            f"Exception occurred for url={page.full_path}"
        )
        return

    logger.info(f"{page} Commenced parsing...")
    proxies = []  # list of params for object creation
    try:  # catch bs4 exceptions
        # parse the html content with bs4
        soup = BeautifulSoup(res.content, "html.parser")
        # get the table with data
        table = soup.find(id="proxylisttable")
        # get the table headings
        # headings = table.select("thead > tr > th")
        # get the proxy data rows
        rows = table.select("tbody > tr")
        for r in rows:
            # get the columns in each row
            cols = r.select("td")
            proxies.append(
                (
                    str(cols[0].text).strip(),  # ip address
                    int(str(cols[1].text).strip()),  # port
                    str(cols[2].text).strip(),  # country code
                    str(cols[4].text).strip(),  # anonymity
                    bool(strtobool(str(cols[6].text).strip())),  # https
                )
            )
    except Exception as e:
        logger.error(e)
        logger.info(f"{page} Exception occurred parsing content, exiting")
        return
    logger.debug(f"{page} Proxies={proxies}")
    logger.info(f"{page} Parsing complete")

    # lets find working proxies
    tested = []  # list of tested proxies
    logger.info(f"{page} Commenced proxy testing...")
    for p in proxies:
        if Proxy.objects.filter(ip=p[0], port=p[1]).exists():
            continue  # no need to test proxy already in db

        proxy = {}  # build the proxy dict
        if p[-1]:
            proxy.update({"https": f"http://{p[0]}:{p[1]}"})
        else:
            proxy.update({"http": f"http://{p[0]}:{p[1]}"})

        try:  # test the proxy
            logger.debug(f"Testing proxy {p[0]}:{p[1]} ...")
            with requests_cache.disabled():
                res = requests.get(TEST_URL, proxies=proxy, timeout=10)
            if res.ok:  # add to tested list
                tested.append(p)
                logger.debug(f"Working proxy {p[0]}:{p[1]} added to list")
        except Exception as e:
            logger.error(e)
            logger.debug(f"Testing failed with proxy {p[0]}:{p[1]}")
    logger.info(f"{page} Proxy testing complete")

    if not tested:
        logger.info(f"{page} No new working proxies found, exiting")
        return

    # save the tested proxies to db
    logger.info(f"{page} Commenced save to database...")
    for t in tested:
        try:
            anonymity = [
                a[0]
                for a in Anonymity.as_tuple()
                if a[1].lower() in t[3].lower()
            ]
            obj, _ = Proxy.objects.get_or_create(
                ip=t[0],  # ip address
                port=t[1],  # port
                country=t[2],  # country code
                anonymity=anonymity[0],
                protocol=Protocol.HTTPS[0] if t[4] else Protocol.HTTP[0],
                checked_at=timezone.now(),
            )
            obj.found_in.add(page)  # add the m2m field
            obj.save()  # finally save the proxy
            logger.debug(f"{obj} saved in database")
        except Exception as e:
            logger.error(e)
            logger.debug(f"Failed to save tested proxy {t[0]}:{t[1]}")

    logger.info(f"{page} Scrape complete!")
    return True  # completion status
