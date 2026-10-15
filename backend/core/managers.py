from typing import TypeVar

from django.db import models

from core.context import ctx
from core.errors import MissingTenantContextError, SystemScopeRequiredError

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


class AllSchoolsManager(models.Manager[_M]):
    """Unscoped manager for system jobs. Usable only inside `system_scope`."""

    def get_queryset(self) -> models.QuerySet[_M]:
        if ctx().system_scope_reason is None:
            raise SystemScopeRequiredError(
                f"{self.model.__name__}.all_schools used outside system_scope"
            )
        return super().get_queryset()
