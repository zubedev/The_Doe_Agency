from django.urls import path, include
from rest_framework import routers

from scraper import views

app_name = "scraper"

router = routers.DefaultRouter()
router.register("sites", views.WebsiteViewSet)
router.register("pages", views.PageViewSet)
router.register("proxies", views.ProxyViewSet)

urlpatterns = [
    # router urls
    path("", include(router.urls)),
    path("scrape_sites/", views.ScrapeSitesAPI.as_view(), name="scrape_sites"),
    path(
        "check_proxies/", views.CheckProxiesAPI.as_view(), name="check_proxies"
    ),
]
