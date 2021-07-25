from logging import getLogger

from bs4 import BeautifulSoup

from scraper.models import Anonymity, Protocol
from scraper.scrapers import common

logger = getLogger(__name__)

WEBSITE = "FreeProxyLists"
CODE = "FPLS"


def _extract_proxies(soup: BeautifulSoup):
    logger.info("Commenced parsing...")
    proxies = []  # list of params for object creation

    table = common.slurp(soup, kv={"class": "DataGrid"})
    # headings = common.slurp(table, kv={"class": "Caption"}).select("td")
    rows = common.slurp(table, "select", "tbody > tr")[1:]  # ignore 1st row

    for r in rows:
        cols = common.slurp(r, "select", "td")  # get the columns in each row
        if len(cols) <= 1:  # ADs or invalid data row
            continue  # invalid row, continue to next row

        ip = str(cols[0].find("a").text).strip()
        port = str(cols[1].text).strip()
        protocol = str(cols[2].text).strip()
        anonymity = str(cols[3].text).strip()
        country = (
            str(cols[4].find("img")["src"])
            .strip()
            .split("/")[-1]
            .split(".")[0]
            .upper()
        )

        anonymity = (
            Anonymity.ELITE[0]
            if "HIGH" in anonymity.upper()
            else Anonymity.ANONYMOUS[0]
        )
        protocol = [
            p[0]
            for p in Protocol.as_tuple()
            if p[0].upper() == protocol.upper()
        ]

        proxies.append(
            {
                "ip": ip,
                "port": port,
                "country": country,
                "anonymity": anonymity,
                "protocol": protocol[0] if protocol else Protocol.HTTP[0],
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
