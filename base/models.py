from django.db import models


class TimeStampedModel(models.Model):
    # auto datetime field on object creation
    created_at = models.DateTimeField(auto_now_add=True)
    # auto datetime field on object save
    updated_at = models.DateTimeField(auto_now=True)
    # status field for object or instance
    is_active = models.BooleanField("Active Status", default=True)

    class Meta:
        abstract = True
