from django.db import models

from core.models import BaseModel


class School(BaseModel):
    """The tenant root. Not a TenantModel: it has no school of its own."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
