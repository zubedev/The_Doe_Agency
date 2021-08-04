from django.urls import path

from scraper import views

app_name = "scraper"

urlpatterns = [
    path("scrape_sites/", views.ScrapeSitesAPI.as_view(), name="scrape_sites"),
    path(
        "check_proxies/", views.CheckProxiesAPI.as_view(), name="check_proxies"
    ),
]
