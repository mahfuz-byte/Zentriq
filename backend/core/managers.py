from collections.abc import Collection, Iterable
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, TypeVar

from django.db import models

from core.context import ctx, require_school_id
from core.errors import CrossTenantWriteError, SystemScopeRequiredError

if TYPE_CHECKING:
    from core.models import TenantModel

_Row = TypeVar("_Row", bound="TenantModel")

_rows_already_guarded: ContextVar[bool] = ContextVar("as_rows_already_guarded", default=False)


class TenantQuerySet(models.QuerySet[_Row]):
    """Bulk writes go through the same tenancy rules as `TenantModel.save()`."""

    def bulk_create(
        self,
        objs: Iterable[_Row],
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
        update_conflicts: bool = False,
        update_fields: Collection[str] | None = None,
        unique_fields: Collection[str] | None = None,
    ) -> list[_Row]:
        if update_conflicts:
            # An upsert overwrites whatever row holds the key, in any school.
            raise CrossTenantWriteError(
                f"{self.model.__name__}.bulk_create cannot update on conflict"
            )
        rows = list(objs)
        # With ignore_conflicts a row may be skipped because its key is taken, maybe by
        # another school's row, so links to rows in the batch can't be trusted.
        self.model.guard_writes(rows, trust_batch_links=not ignore_conflicts)
        created = super().bulk_create(
            rows,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )
        for row in rows:
            row._mark_persisted()
        return created

    def bulk_update(
        self,
        objs: Iterable[_Row],
        fields: Iterable[str],
        batch_size: int | None = None,
    ) -> int:
        rows = list(objs)
        self.model.guard_writes(rows)
        # Django implements bulk_update as update() with Case/When expressions. The
        # rows were checked above, so that inner update() skips its own guard.
        token = _rows_already_guarded.set(True)
        try:
            return super().bulk_update(rows, fields, batch_size=batch_size)
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
    cascades, related add() and refresh_from_db. Scoped like `objects`, except in a
    `system_scope` with no school, where system jobs need those to reach every
    school's rows. A system scope inside a school stays within that school.
    """

    def get_queryset(self) -> TenantQuerySet[_Row]:
        context = ctx()
        if context.in_system_scope and context.school_id is None:
            return TenantQuerySet(self.model, using=self._db)
        return super().get_queryset()


class AllSchoolsManager(models.Manager[_Row]):
    """Unscoped manager for system jobs. Usable only inside `system_scope`.

    Its update(), delete(), bulk_create() and bulk_update() skip the tenancy write
    rules (save() still applies them): system jobs own that risk.
    """

    def get_queryset(self) -> models.QuerySet[_Row]:
        if not ctx().in_system_scope:
            raise SystemScopeRequiredError(
                f"{self.model.__name__}.all_schools used outside system_scope"
            )
        return super().get_queryset()
