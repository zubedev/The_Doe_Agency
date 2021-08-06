from logging import getLogger

from bs4 import BeautifulSoup

from scraper.models import Anonymity
from scraper.utils import slurp

logger = getLogger(__name__)

content = """
<html>
    <body>
        <table id="proxy_list">
            <thead></thead>
            <tbody>
            <tr>
                <td>127.1.2.3</td>
                <td><span>12345</span></td>
                <td><small>HTTP</small></td>
                <td><div>
                    <img src="...">
                    <a href="/en/proxylist/country/BD/all/ping/all">...</a>
                </div></td>
                <td></td>
                <td></td>
                <td><small>Anonymous</small></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            </tbody>
        </table>
    </body>
</html
"""


def parse(soup: BeautifulSoup):
    logger.info("Commenced parsing...")
    proxies = []  # list of params for object creation

    table = slurp(soup, kv={"id": "proxy_list"})
    # headings = common.slurp(table, "select", "thead > tr > th")
    rows = slurp(table, "select", "tbody > tr")

    for r in rows:
        cols = slurp(r, "select", "td")  # get the columns in each row
        if len(cols) <= 1:
            continue  # invalid row, continue to next row

        ip = str(cols[0].text).strip()
        port = str(cols[1].find("span").text).strip()
        protocol = str(cols[2].find("small").text).strip()
        country = str(cols[3].find("a")["href"]).strip().split("/")[4]
        anonymity = str(cols[6].find("small").text).strip().split(" ")[0]

        anonymity = [
            a[0]
            for a in Anonymity.as_tuple()
            if a[1].upper() == anonymity.upper()
        ]

        proxies.append(
            {
                "ip": ip,
                "port": int(port),
                "country": country.upper(),
                "anonymity": anonymity[0]
                if anonymity
                else Anonymity.UNKNOWN[0],
                "protocol": protocol.upper(),
            }
        )

    logger.debug(f"Proxies: {proxies}")
    logger.info("Parsing complete")
    return proxies
