from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from django.db import models

from core.context import ctx
from core.errors import MissingTenantContextError, SystemScopeRequiredError

if TYPE_CHECKING:
    from core.models import TenantModel

_M = TypeVar("_M", bound=models.Model)


class TenantQuerySet(models.QuerySet[_M]):
    """Bulk writes go through the same tenancy rules as `TenantModel.save()`."""

    def bulk_create(self, objs: Iterable[_M], *args: Any, **kwargs: Any) -> list[_M]:
        rows = list(objs)
        self._tenant_model().guard_writes(rows)  # type: ignore[arg-type]  # reason: _M is a TenantModel here
        created = super().bulk_create(rows, *args, **kwargs)
        for row in rows:
            row._persisted_school_id = row.school_id  # type: ignore[attr-defined]  # reason: as above
        return created

    def bulk_update(self, objs: Iterable[_M], fields: Sequence[str], *args: Any, **kwargs: Any) -> int:
        rows = list(objs)
        self._tenant_model().guard_writes(rows)  # type: ignore[arg-type]  # reason: as above
        return super().bulk_update(rows, fields, *args, **kwargs)

    def _tenant_model(self) -> "type[TenantModel]":
        return self.model  # type: ignore[return-value]  # reason: only TenantModel uses this queryset


class TenantManager(models.Manager[_M]):
    """Default manager of every TenantModel: sees only the current school's rows."""

    def get_queryset(self) -> TenantQuerySet[_M]:
        school_id = ctx().school_id
        if school_id is None:
            raise MissingTenantContextError(
                f"{self.model.__name__} queried with no school in the current context"
            )
        return TenantQuerySet(self.model, using=self._db).filter(school_id=school_id)


class AllSchoolsManager(models.Manager[_M]):
    """Unscoped manager for system jobs. Usable only inside `system_scope`.

    Its bulk_create/bulk_update skip the tenancy write rules (save() still applies
    them): system jobs own that risk.
    """

    def get_queryset(self) -> models.QuerySet[_M]:
        if ctx().system_scope_reason is None:
            raise SystemScopeRequiredError(
                f"{self.model.__name__}.all_schools used outside system_scope"
            )
        return super().get_queryset()
