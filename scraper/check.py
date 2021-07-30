from logging import getLogger

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from django.utils import timezone

from scraper.models import Proxy, Check
from scraper.scrapers.common import test_ip_port

logger = getLogger(__name__)


def get_proxies(is_active: bool = True, **kwargs: dict):
    """Returns available active proxies queryset"""
    params = {"is_active": is_active, **kwargs}
    return Proxy.objects.filter(**params)


def check(**kwargs: dict) -> None:
    """Updates or deletes proxies once checked
    Args:
        kwargs [dict]: keyword arguments passed to <Proxy> filter
    """
    logger.info("Commencing all available proxy check...")
    proxies = get_proxies(**kwargs)

    obj = Check.objects.create()
    if proxies:
        obj.proxies.add(*proxies)

    with ThreadPoolExecutor() as executor:
        futures = []
        proxies = proxies.values("ip", "port", "protocol")
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

    # Check object
    obj.completed_at = timezone.now()
    obj.is_success = True
    obj.save()
    logger.info("Proxy check completed!")
