from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.models import TimeStampedModel


class Website(TimeStampedModel):
    name = models.CharField(_("Name of Site"), max_length=100, unique=True)
    code = models.CharField(_("Unique Code"), max_length=4)
    url = models.URLField(_("Base URL"), unique=True)

    class Meta:
        indexes = (
            models.Index(fields=["id"]),
            models.Index(fields=["-id"]),
            models.Index(fields=["name"]),
            models.Index(fields=["-name"]),
            models.Index(fields=["code"]),
            models.Index(fields=["-code"]),
        )
        ordering = ("name",)

    def __str__(self):
        return f"<Website: {self.id}> {self.name}"


class Page(TimeStampedModel):
    site = models.ForeignKey(
        Website, on_delete=models.CASCADE, related_name="pages"
    )
    path = models.CharField(_("Page Path"), max_length=1000)
    has_js = models.BooleanField(_("JS Rendered"), default=False)

    class Meta:
        indexes = (
            models.Index(fields=["id"]),
            models.Index(fields=["-id"]),
        )
        ordering = ("id",)

    def __str__(self):
        return f"<Page: {self.id}> {self.full_path}"

    @cached_property
    def full_path(self):
        return f"{self.site.url}{self.path}"
