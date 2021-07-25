from distutils.util import strtobool
from logging import getLogger

from bs4 import BeautifulSoup

from scraper.models import Anonymity, Protocol
from scraper.scrapers import common

logger = getLogger(__name__)

WEBSITE = "SSLProxies"
CODE = "SSLP"


def _extract_proxies(soup: BeautifulSoup):
    logger.info("Commenced parsing...")
    proxies = []  # list of params for object creation

    table = common.slurp(soup, kv={"id": "proxylisttable"})
    # headings = common.slurp(table, "select", "thead > tr > th")
    rows = common.slurp(table, "select", "tbody > tr")
    for r in rows:
        cols = common.slurp(r, "select", "td")  # get the columns in each row
        anonymity = [
            a[0]
            for a in Anonymity.as_tuple()
            if a[1].lower() in str(cols[4].text).strip().lower()
        ]
        protocol = (
            Protocol.HTTPS[0]
            if bool(strtobool(str(cols[6].text).strip()))
            else Protocol.HTTP[0]
        )
        proxies.append(
            {
                "ip": str(cols[0].text).strip(),
                "port": int(str(cols[1].text).strip()),
                "country": str(cols[2].text).strip(),
                "anonymity": anonymity[0]
                if anonymity
                else Anonymity.UNKNOWN[0],
                "protocol": protocol,
            }
        )

    logger.debug(f"Proxies: {proxies}")
    logger.info("Parsing complete")
    return proxies


def scrape():
    proxy_list = []
    pages = common.get_pages(site__code=CODE)

    for page in pages:
        logger.info(f"{page} Commenced scraping...")

        content = common.get_content(page)  # page source
        soup = BeautifulSoup(content, "html.parser")  # parse the html content
        proxies = _extract_proxies(soup)  # list of extracted proxies
        tested = common.get_tested(proxies)  # list of tested proxies
        saved_to_db = common.save_to_db(page, tested)  # list of saved proxies

        if saved_to_db:
            proxy_list += saved_to_db
        logger.info(f"{page} Scrape complete.")

    logger.debug(f"Proxies: {proxy_list}")
    return proxy_list
