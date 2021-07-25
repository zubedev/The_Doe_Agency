# Generated by Django 3.2.5 on 2021-07-19 07:49

import django.core.validators
from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ("scraper", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Proxy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, verbose_name="Active Status"
                    ),
                ),
                (
                    "ip",
                    models.GenericIPAddressField(verbose_name="IP Address"),
                ),
                (
                    "port",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(65535),
                        ],
                        verbose_name="Port",
                    ),
                ),
                (
                    "country",
                    django_countries.fields.CountryField(max_length=2),
                ),
                (
                    "anonymity",
                    models.CharField(
                        choices=[
                            ("UNK", "Unknown"),
                            ("NOA", "Transparent"),
                            ("ANM", "Anonymous"),
                            ("HIA", "Elite"),
                        ],
                        max_length=3,
                        verbose_name="Anonymity",
                    ),
                ),
                (
                    "protocol",
                    models.CharField(
                        choices=[
                            ("HTTP", "HTTP"),
                            ("HTTPS", "HTTPS"),
                            ("SOCKS4", "SOCKS4"),
                            ("SOCKS5", "SOCKS5"),
                        ],
                        max_length=7,
                        verbose_name="Protocol",
                    ),
                ),
                (
                    "checked_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Last checked"
                    ),
                ),
                (
                    "checked_count",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Checked count"
                    ),
                ),
                (
                    "is_dead",
                    models.BooleanField(
                        default=False, verbose_name="Dead status"
                    ),
                ),
                (
                    "found_in",
                    models.ManyToManyField(
                        related_name="found_in_pages",
                        to="scraper.Page",
                        verbose_name="Found in Pages",
                    ),
                ),
            ],
            options={
                "ordering": ("ip", "port"),
                "verbose_name_plural": "Proxies",
            },
        ),
        migrations.AddIndex(
            model_name="proxy",
            index=models.Index(
                fields=["id"], name="scraper_pro_id_76f0d4_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="proxy",
            index=models.Index(
                fields=["-id"], name="scraper_pro_id_e2a5c5_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="proxy",
            index=models.Index(
                fields=["ip", "port"], name="scraper_pro_ip_b3c48f_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="proxy",
            constraint=models.UniqueConstraint(
                fields=("ip", "port"), name="unique_proxy"
            ),
        ),
    ]