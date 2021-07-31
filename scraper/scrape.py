from logging import getLogger
import typing

from bs4 import BeautifulSoup
from django.db.models import QuerySet
from django.utils import timezone

from scraper.models import Website, Page, Proxy, Scrape
from scraper.utils import get_sites, get_content, get_tested, save_to_db

logger = getLogger(__name__)


def scrape_page(
    page: Page = None, pk: int = None, **kwargs: dict
) -> list[Proxy]:
    """Single <Page> scrape function
    Args:
        page: <Page> object
        pk: <Page> object pk/id (int)
        kwargs: keyword arguments passed to <Page> objects filter
    Returns:
        list: List of <Proxy>
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
    site: Website = None,
    code: str = None,
    pk: int = None,
    obj: Scrape = None,
    **kwargs: dict,
) -> tuple[list[Proxy], Scrape]:
    """Single <Website> scrape function
    Args:
        site: <Website> object
        code: <Website> `code` value (str)
        pk: <Website> object pk/id (int)
        obj: <Scrape> object for recording
        kwargs: keyword arguments passed to <Website> objects filter
    Returns:
        tuple: List of <Proxy>, <Scrape> obj
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
        return [], obj

    logger.info(f"{site} Commenced scraping...")
    pages = site.pages.select_related("site").filter(is_active=True)
    if obj and pages:
        obj.pages.add(*pages)

    proxy_list: list[Proxy] = []
    for page in pages:
        try:
            proxy_list += scrape_page(page)
        except Exception as e:  # continue to next loop for any error
            logger.error(e)
            continue

    logger.info(f"{site} Scrape complete.")
    return proxy_list, obj


def scrape(
    sites: typing.Union[list[Website], QuerySet[Website]] = None
) -> list[Proxy]:
    """Main scrape function
    Args:
        sites: List of <Website> or QuerySet[<Website>]
    Returns:
        list: List of proxies in `dict`
    """
    obj = Scrape.objects.create()  # record the scrape

    if not sites:
        sites = get_sites()  # is_active=True (default)
        if sites:
            obj.sites.add(*sites)

    proxy_list: list[Proxy] = []
    for site in sites:
        try:
            proxies, obj = scrape_site(site, obj=obj)
            proxy_list += proxies
        except Exception as e:  # continue to next loop for any error
            logger.error(e)
            continue

    # Scrape object
    obj.proxies = len(proxy_list)
    obj.completed_at = timezone.now()
    obj.is_success = True
    obj.save()

    logger.debug(f"Scrape: {obj}, Proxies: {proxy_list}")
    return proxy_list
