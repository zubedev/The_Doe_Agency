from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import escape, format_html

from core import models


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = "action_time"
    list_display = (
        "action_time",
        "user_link",
        "content_type",
        "object_link",
        "action_flag",
        "change_message",
    )
    list_filter = ("action_flag", "content_type")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__username",
        "object_repr",
        "change_message",
    )

    def has_add_permission(self, request: HttpRequest):
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj=None):
        return request.user.is_staff

    def user_link(self, obj: LogEntry):
        try:
            url = reverse("admin:core_user_change", args=[obj.user_id])
            link = f'<a href="{url}">{escape(obj.user)}</a>'
        except Exception:
            link = escape(obj.user)
        return format_html(link)

    user_link.admin_order_field = "user"
    user_link.short_description = "user"

    def object_link(self, obj: LogEntry):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            try:
                url = obj.get_admin_url()
                link = f'<a href="{url}">{escape(obj.object_repr)}</a>'
            except Exception:
                link = escape(obj.object_repr)
        return format_html(link)

    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"


@admin.register(models.User)
class UserAdmin(UserAdmin):
    model = models.User
    date_hierarchy = "date_joined"
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "last_login",
        "last_updated",
        "date_joined",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Roles", {"fields": ("is_staff", "is_superuser", "is_active")}),
        ("Dates", {"fields": ("last_login", "last_updated", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    readonly_fields = (
        "last_login",
        "last_updated",
        "date_joined",
    )
    search_fields = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
    )
