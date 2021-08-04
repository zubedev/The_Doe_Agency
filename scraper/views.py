from rest_framework.response import Response
from rest_framework.views import APIView

from scraper.tasks import scrape_sites, check_proxies


class ScrapeSitesAPI(APIView):
    def post(self, request):
        task = scrape_sites.apply_async()
        return Response({"task_id": task.id, "status": task.status})


class CheckProxiesAPI(APIView):
    def post(self, request):
        task = check_proxies.apply_async()
        return Response({"task_id": task.id, "status": task.status})
