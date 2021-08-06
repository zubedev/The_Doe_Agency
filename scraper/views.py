from http import HTTPStatus

from rest_framework import views, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework.response import Response

from scraper import models, serializers, tasks
from scraper.utils import get_random_working_proxy


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


class GetProxyAPI(views.APIView):
    def get_proxy(
        self, output: str = "dict", test_urls: list or tuple = None
    ) -> Response:
        result = get_random_working_proxy(output="dict", test_urls=test_urls)
        if result:
            return Response(
                {"result": result, "status": "SUCCESS"}, status=HTTPStatus.OK
            )  # 200 OK
        else:
            return Response(
                {"status": "NO PROXY FOUND"}, status=HTTPStatus.NO_CONTENT
            )  # 204 No content

    def get(self, request: Request):
        return self.get_proxy()

    def post(self, request: Request):
        test_urls = request.POST.get("test_urls", None)
        if not test_urls:
            raise ParseError("Must provide test_urls for proxy check")
        if isinstance(test_urls, str):
            test_urls = (test_urls,)
        return self.get_proxy(test_urls=test_urls)
