from django.conf import settings
from django.db import models

from core.models import TenantModel


class FileObject(TenantModel):
    """Metadata of a stored file. The bytes live in object storage under a random key."""

    class ScanStatus(models.TextChoices):
        PENDING = "PENDING"
        CLEAN = "CLEAN"
        INFECTED = "INFECTED"
        ERROR = "ERROR"

    class Purpose(models.TextChoices):
        SCHOOL_LOGO = "SCHOOL_LOGO"

    storage_key = models.CharField(max_length=200, unique=True)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    scan_status = models.CharField(
        max_length=20, choices=ScanStatus.choices, default=ScanStatus.PENDING
    )
    purpose = models.CharField(max_length=40, choices=Purpose.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
