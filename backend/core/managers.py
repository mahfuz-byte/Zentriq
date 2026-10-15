from collections.abc import Iterable, Sequence
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, TypeVar

from django.db import models

from core.context import ctx, require_school_id
from core.errors import SystemScopeRequiredError

if TYPE_CHECKING:
    from core.models import TenantModel

_Row = TypeVar("_Row", bound="TenantModel")

_rows_already_guarded: ContextVar[bool] = ContextVar("as_rows_already_guarded", default=False)


class TenantQuerySet(models.QuerySet[_Row]):
    """Bulk writes go through the same tenancy rules as `TenantModel.save()`."""

    def bulk_create(
        self,
        objs: Iterable[_Row],
        *args: Any,  # reason: passed through to Django's bulk_create unchanged
        **kwargs: Any,  # reason: as for *args
    ) -> list[_Row]:
        rows = list(objs)
        self.model.guard_writes(rows)
        created = super().bulk_create(rows, *args, **kwargs)
        for row in rows:
            row._mark_persisted()
        return created

    def bulk_update(
        self,
        objs: Iterable[_Row],
        fields: Sequence[str],
        *args: Any,  # reason: passed through to Django's bulk_update unchanged
        **kwargs: Any,  # reason: as for *args
    ) -> int:
        rows = list(objs)
        self.model.guard_writes(rows)
        # Django implements bulk_update as update() with Case/When expressions. The
        # rows were checked above, so that inner update() skips its own guard.
        token = _rows_already_guarded.set(True)
        try:
            return super().bulk_update(rows, fields, *args, **kwargs)
        finally:
            _rows_already_guarded.reset(token)

    def update(self, **kwargs: Any) -> int:  # reason: column values of any type, as in Django
        if not _rows_already_guarded.get():
            self.model.guard_update(kwargs)
        return super().update(**kwargs)


class TenantManager(models.Manager[_Row]):
    """Default manager of every TenantModel: sees only the current school's rows."""

    def get_queryset(self) -> TenantQuerySet[_Row]:
        school_id = require_school_id(f"{self.model.__name__} query")
        return TenantQuerySet(self.model, using=self._db).filter(school_id=school_id)


class TenantBaseManager(TenantManager[_Row]):
    """Django's base manager for TenantModel: forward links, save()'s UPDATE, delete
    cascades and refresh_from_db. Scoped like `objects`, except inside `system_scope`,
    where system jobs need those to reach every school's rows.
    """

    def get_queryset(self) -> TenantQuerySet[_Row]:
        if ctx().system_scope_reason is not None:
            return TenantQuerySet(self.model, using=self._db)
        return super().get_queryset()


class AllSchoolsManager(models.Manager[_Row]):
    """Unscoped manager for system jobs. Usable only inside `system_scope`.

    Its bulk_create/bulk_update skip the tenancy write rules (save() still applies
    them): system jobs own that risk.
    """

    def get_queryset(self) -> models.QuerySet[_Row]:
        if ctx().system_scope_reason is None:
            raise SystemScopeRequiredError(
                f"{self.model.__name__}.all_schools used outside system_scope"
            )
        return super().get_queryset()
