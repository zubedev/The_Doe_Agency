from logging import getLogger

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from django.utils import timezone

from scraper.models import Proxy
from scraper.scrapers.common import test_ip_port

logger = getLogger(__name__)


def get_proxies(is_active: bool = True, **kwargs: dict):
    """Returns active proxies queryset dict with only ip, port and protocol"""
    params = {"is_active": is_active, **kwargs}
    return Proxy.objects.filter(**params).values("ip", "port", "protocol")


def check(**kwargs: dict) -> None:
    """Updates or deletes proxies once checked
    Args:
        kwargs [dict]: keyword arguments passed to <Proxy> filter
    """
    proxies = get_proxies(**kwargs)

    with ThreadPoolExecutor() as executor:
        futures = []
        for proxy in proxies:
            futures.append(executor.submit(test_ip_port, **proxy))
        for future in concurrent.futures.as_completed(futures):
            try:
                status, proxy = future.result()
                qs = Proxy.objects.filter(
                    ip=proxy.get("ip"), port=proxy.get("port")
                )
                if status:
                    logger.info(f"Updating: {qs}")
                    qs.update(checked_at=timezone.now())
                else:
                    logger.info(f"Deleting: {qs}")
                    qs.delete()
            except Exception as e:
                logger.error(e)
