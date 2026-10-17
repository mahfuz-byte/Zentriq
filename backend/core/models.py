import functools
import uuid
from collections.abc import Sequence
from typing import Any, Self, TypeGuard

from django.apps import apps
from django.db import models

from core.context import require_school_id
from core.errors import CrossTenantWriteError
from core.managers import AllSchoolsManager, TenantBaseManager, TenantManager

# Foreign keys to school-owned rows, each with the target keys a write would link to.
_LinkTargets = dict["models.ForeignKey[Any, Any]", set[Any]]  # reason: any key type


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    school = models.ForeignKey("accounts.School", on_delete=models.PROTECT)

    objects = TenantManager()  # declared first, so it is the default manager
    all_schools = AllSchoolsManager()
    _base_rows = TenantBaseManager()

    class Meta:
        abstract = True
        # Django uses the base manager for forward foreign keys, save()'s UPDATE and
        # delete cascades. It is scoped like `objects`, except in a school-less system_scope.
        base_manager_name = "_base_rows"

    # The school this row has in the database; None until it is saved or loaded.
    _persisted_school_id: uuid.UUID | None = None

    @classmethod
    def from_db(
        cls,
        db: str | None,
        field_names: Sequence[str],
        values: Sequence[Any],  # reason: raw column values of any type, as in Django
    ) -> Self:
        instance = super().from_db(db, field_names, values)
        instance._mark_persisted()
        return instance

    def save(
        self,
        *args: Any,  # reason: passed through to Django's save unchanged
        **kwargs: Any,  # reason: as for *args
    ) -> None:
        type(self).guard_writes([self])
        super().save(*args, **kwargs)
        self._mark_persisted()

    def delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        # Django deletes by primary key alone, so check the row is one the base
        # manager may reach: the current school's, or any school's in a system job.
        if self.pk is not None and not type(self)._base_manager.filter(pk=self.pk).exists():
            raise CrossTenantWriteError(
                f"{type(self).__name__} {self.pk} is not a row of the current school"
            )
        return super().delete(using=using, keep_parents=keep_parents)

    def _mark_persisted(self) -> None:
        """Record the school this row now has in the database."""
        self._persisted_school_id = self.school_id

    @classmethod
    def guard_writes(cls, rows: Sequence["TenantModel"], trust_batch_links: bool = True) -> None:
        """Apply the tenancy write rules to rows about to be saved, singly or in bulk.

        New rows without a school get the current school. Every row must belong to
        the current school, must not move from the school it was saved in, and must
        not point at another school's row. Links to rows in the same batch are
        allowed only when `trust_batch_links` says every row will really be written.
        """
        school_id = require_school_id(f"saving {cls.__name__}")
        for row in rows:
            if row._state.adding and row.school_id is None:
                row.school_id = school_id
            if row.school_id != school_id:
                raise CrossTenantWriteError(
                    f"{cls.__name__} belongs to school {row.school_id}, "
                    f"not the current school {school_id}"
                )
            if not row._state.adding and row.school_id != row._persisted_school_id:
                raise CrossTenantWriteError(f"{cls.__name__} cannot move to another school")
        cls._guard_links(rows, trust_batch_links)

    @classmethod
    def guard_update(cls, values: dict[str, Any]) -> None:  # reason: column values of any type
        """Apply the tenancy write rules to the values of a QuerySet.update()."""
        if values.keys() & {"school", "school_id"}:
            raise CrossTenantWriteError(f"{cls.__name__} rows cannot move to another school")
        links: _LinkTargets = {}
        for name, value in values.items():
            field = cls._meta.get_field(name)
            if not _links_to_tenant_rows(field) or value is None:
                continue
            if hasattr(value, "resolve_expression"):
                raise CrossTenantWriteError(
                    f"{cls.__name__}.{field.name} cannot be updated from an expression: "
                    "its target school can't be checked"
                )
            if isinstance(value, models.Model):
                value = getattr(value, field.target_field.attname)
            links[field] = {value}
        cls._check_links(links)

    @classmethod
    def _guard_links(cls, rows: Sequence["TenantModel"], trust_batch_links: bool) -> None:
        links: _LinkTargets = {}
        for field in cls._meta.concrete_fields:
            if not _links_to_tenant_rows(field):
                continue
            ids = {getattr(row, field.attname) for row in rows} - {None}
            if trust_batch_links and field.related_model is cls:
                # Rows in this batch already passed the school checks, and the ones
                # being created can't be found by a query yet.
                ids -= {getattr(row, field.target_field.attname) for row in rows}
            links[field] = ids
        cls._check_links(links)

    @classmethod
    def _check_links(cls, links: _LinkTargets) -> None:
        # The scoped manager only sees the current school, so a target it cannot find
        # is in another school (or missing). One query per foreign key.
        for field, ids in links.items():
            lookup = {f"{field.target_field.attname}__in": ids}
            if ids and field.related_model.objects.filter(**lookup).count() != len(ids):
                raise CrossTenantWriteError(
                    f"{cls.__name__}.{field.name} points at a row outside the current school"
                )


@functools.cache
def tenant_models() -> tuple[type[TenantModel], ...]:
    """The TENANT_MODELS registry: every installed, concrete TenantModel (DR-002). RLS
    (P7-T02) and the cross-tenant suite are generated from it.

    A function rather than a module constant because models aren't loaded when this
    module is imported. Computed once, on the first call after the app registry is
    ready (before that, apps.get_models() raises and nothing is cached).
    """
    return tuple(model for model in apps.get_models() if is_tenant_model(model))


def is_tenant_model(model: object) -> TypeGuard[type[TenantModel]]:
    """Whether `model` is a school-owned model class."""
    return isinstance(model, type) and issubclass(model, TenantModel)


def _links_to_tenant_rows(field: Any) -> TypeGuard["models.ForeignKey[Any, Any]"]:  # reason: any model field
    # ForeignKey includes OneToOneField.
    return isinstance(field, models.ForeignKey) and is_tenant_model(
        getattr(field, "related_model", None)
    )
