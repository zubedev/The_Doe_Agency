from distutils.util import strtobool
from logging import getLogger

from bs4 import BeautifulSoup

from scraper.models import Anonymity, Protocol
from scraper.utils import slurp

logger = getLogger(__name__)


def parse(soup: BeautifulSoup) -> list[dict]:
    logger.info("Commenced parsing...")
    proxies = []  # list of params for object creation

    table = slurp(soup, kv={"id": "proxylisttable"})
    # headings = slurp(table, "select", "thead > tr > th")
    rows = slurp(table, "select", "tbody > tr")
    for r in rows:
        cols = slurp(r, "select", "td")  # get the columns in each row
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
