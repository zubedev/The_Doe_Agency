from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    # auto datetime field on object creation
    created_at = models.DateTimeField(auto_now_add=True)
    # auto datetime field on object save
    updated_at = models.DateTimeField(auto_now=True)
    # status field for object or instance
    is_active = models.BooleanField("Active Status", default=True)

    class Meta:
        abstract = True


class TaskLogModel(TimeStampedModel):
    # record all errors and traceback logs
    error = models.TextField(_("Error message"), blank=True, null=True)
    # task status field to record success or failure
    is_success = models.BooleanField(_("Success status"), default=False)
    # task completion datetime field
    completed_at = models.DateTimeField(
        _("Datetime of Completion"), blank=True, null=True
    )

    class Meta:
        abstract = True
