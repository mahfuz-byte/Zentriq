import uuid

from django.db import models

from core.managers import TenantManager


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    school = models.ForeignKey("accounts.School", on_delete=models.PROTECT)

    objects = TenantManager()

    class Meta:
        abstract = True
