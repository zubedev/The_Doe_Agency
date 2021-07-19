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
        "name",
        "code",
        "url",
        "created_at",
        "updated_at",
        "is_active",
    )
    list_display_links = ("name",)
    list_filter = ("is_active",)
    search_fields = ("id", "name", "code", "url", "created_at", "updated_at")
    inlines = (PageInline,)

    def get_inline_instances(self, request, obj=None):
        """hides inlines during 'add object' view"""
        return obj and super().get_inline_instances(request, obj) or []
