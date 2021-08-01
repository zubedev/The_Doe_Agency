from logging import getLogger

from bs4 import BeautifulSoup

from scraper.models import Anonymity, Protocol
from scraper.utils import slurp

logger = getLogger(__name__)

content = """
<html>
    <body>
        <table class="DataGrid">
            <tbody>
            <tr></tr>
            <tr>
                <td><a href="">127.1.2.3</a></td>
                <td>12345</td>
                <td>HTTP</td>
                <td>Anonymous</td>
                <td><img src="path/BD.jpg"></td>
            </tr>
            </tbody>
        </table>
    </body>
</html
"""


def parse(soup: BeautifulSoup):
    logger.info("Commenced parsing...")
    proxies = []  # list of params for object creation

    table = slurp(soup, kv={"class": "DataGrid"})
    # headings = slurp(table, kv={"class": "Caption"}).select("td")
    rows = slurp(table, "select", "tbody > tr")[1:]  # ignore 1st row

    for r in rows:
        cols = slurp(r, "select", "td")  # get the columns in each row
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
                "port": int(port),
                "country": country,
                "anonymity": anonymity,
                "protocol": protocol[0] if protocol else Protocol.HTTP[0],
            }
        )

    logger.debug(f"Proxies: {proxies}")
    logger.info("Parsing complete")
    return proxies
