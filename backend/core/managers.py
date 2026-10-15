from typing import TypeVar

from django.db import models

from core.context import ctx
from core.errors import MissingTenantContextError

_M = TypeVar("_M", bound=models.Model)


class TenantManager(models.Manager[_M]):
    """Default manager of every TenantModel: sees only the current school's rows."""

    def get_queryset(self) -> models.QuerySet[_M]:
        school_id = ctx().school_id
        if school_id is None:
            raise MissingTenantContextError(
                f"{self.model.__name__} queried with no school in the current context"
            )
        return super().get_queryset().filter(school_id=school_id)
