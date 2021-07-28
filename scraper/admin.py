from django.contrib import admin

from scraper import models


class PageInline(admin.StackedInline):
    model = models.Page
    readonly_fields = ("created_at", "updated_at")
    extra = 1  # extra form
    can_delete = True


@admin.register(models.Website)
class WebsiteAdmin(admin.ModelAdmin):
    model = models.Website
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    list_display = (
        "__str__",
        "code",
        "url",
        "created_at",
        "updated_at",
        "is_active",
    )
    list_display_links = ("__str__",)
    list_filter = ("is_active",)
    search_fields = ("id", "name", "code", "url", "created_at", "updated_at")
    inlines = (PageInline,)

    def get_inline_instances(self, request, obj=None):
        """hides inlines during 'add object' view"""
        return obj and super().get_inline_instances(request, obj) or []


@admin.register(models.Proxy)
class ProxyAdmin(admin.ModelAdmin):
    model = models.Proxy
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "checked_at",
        "checked_count",
    )
    list_display = (
        "__str__",
        "protocol",
        "anonymity",
        "country",
        "created_at",
        "checked_at",
        "updated_at",
        "is_dead",
        "is_active",
    )
    list_display_links = ("__str__",)
    list_filter = ("is_active", "is_dead", "anonymity", "protocol")
    search_fields = ("id", "ip", "port", "protocol", "anonymity", "country")


@admin.register(models.Scrape)
class ScrapeAdmin(admin.ModelAdmin):
    model = models.Scrape
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
    )
    list_display = (
        "__str__",
        "proxies",
        "completed_at",
        "is_success",
        "error",
        "created_at",
        "updated_at",
        "is_active",
    )
    list_display_links = ("__str__",)
    list_filter = ("is_active", "is_success")
    search_fields = ("id", "error")
