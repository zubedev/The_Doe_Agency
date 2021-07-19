from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

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


class Proxy(TimeStampedModel):
    ip = models.GenericIPAddressField(_("IP Address"))
    port = models.PositiveIntegerField(
        _("Port"), validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    country = CountryField()  # django-countries
    anonymity = models.CharField(
        _("Anonymity"),
        max_length=3,
        choices=(
            ("UNK", "Unknown"),
            ("NOA", "Transparent"),
            ("ANM", "Anonymous"),
            ("HIA", "Elite"),
        ),
    )
    protocol = models.CharField(
        _("Protocol"),
        max_length=7,
        choices=(
            ("HTTP", "HTTP"),
            ("HTTPS", "HTTPS"),
            ("SOCKS4", "SOCKS4"),
            ("SOCKS5", "SOCKS5"),
        ),
    )
    found_in = models.ManyToManyField(
        Page, related_name="found_in_pages", verbose_name="Found in Pages"
    )
    checked_at = models.DateTimeField(_("Last checked"), blank=True, null=True)
    checked_count = models.PositiveSmallIntegerField(
        _("Checked count"), default=0
    )
    is_dead = models.BooleanField(_("Dead status"), default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ip", "port"], name="unique_proxy")
        ]
        indexes = (
            models.Index(fields=["id"]),
            models.Index(fields=["-id"]),
            models.Index(fields=["ip", "port"]),
        )
        verbose_name_plural = "Proxies"
        ordering = ("ip", "port")

    def __str__(self):
        return f"<Proxy: {self.id}> {self.ip}:{self.port}"
