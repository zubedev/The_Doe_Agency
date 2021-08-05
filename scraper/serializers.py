from rest_framework import serializers

from scraper.models import Website, Page, Proxy


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class PageSerializer(serializers.ModelSerializer):
    site = WebsiteSerializer(required=False, read_only=True)

    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class ProxySerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        exclude = ["found_in", "checked_count", "is_dead"]
        read_only_fields = ("created_at", "updated_at", "checked_at")
