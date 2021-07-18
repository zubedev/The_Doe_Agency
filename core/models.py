from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("Email address"), unique=True)
    last_updated = models.DateTimeField(_("Last updated"), auto_now=True)

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        indexes = (
            models.Index(fields=["id"]),
            models.Index(fields=["-id"]),
            models.Index(fields=["username"]),
            models.Index(fields=["-username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["-email"]),
        )
        ordering = ("username",)
