from rest_framework import views, viewsets
from rest_framework.response import Response

from scraper import models, serializers, tasks


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = models.Website.objects.all()
    serializer_class = serializers.WebsiteSerializer
    filterset_fields = ("is_active",)
    search_field = ("name", "code", "url")
    ordering_fields = ("name", "code", "id")


class PageViewSet(viewsets.ModelViewSet):
    queryset = models.Page.objects.all()
    serializer_class = serializers.PageSerializer
    filterset_fields = ("is_active", "has_js")
    search_field = ("site__name", "site__code", "path")
    ordering_fields = ("site", "id")


class ProxyViewSet(viewsets.ModelViewSet):
    queryset = models.Proxy.objects.all()
    serializer_class = serializers.ProxySerializer
    filterset_fields = ("is_active", "is_dead", "anonymity", "protocol")
    search_field = ("ip", "port", "country")
    ordering_fields = ("id", "ip", "port", "country")


class ScrapeSitesAPI(views.APIView):
    def post(self, request):
        task = tasks.scrape_sites.apply_async()
        return Response({"task_id": task.id, "status": task.status})


class CheckProxiesAPI(views.APIView):
    def post(self, request):
        task = tasks.check_proxies.apply_async()
        return Response({"task_id": task.id, "status": task.status})
