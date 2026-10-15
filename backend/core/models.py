import uuid
from collections.abc import Sequence
from typing import Any, Self

from django.db import models

from core.context import ctx
from core.errors import CrossTenantWriteError, MissingTenantContextError
from core.managers import AllSchoolsManager, TenantManager


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    school = models.ForeignKey("accounts.School", on_delete=models.PROTECT)

    objects = TenantManager()
    all_schools = AllSchoolsManager()

    class Meta:
        abstract = True

    # The school this row has in the database; None until it is saved or loaded.
    _persisted_school_id: uuid.UUID | None = None

    @classmethod
    def from_db(cls, db: str | None, field_names: Any, values: Any) -> Self:
        instance = super().from_db(db, field_names, values)
        instance._persisted_school_id = instance.school_id
        return instance

    def save(self, *args: Any, **kwargs: Any) -> None:
        type(self).guard_writes([self])
        super().save(*args, **kwargs)
        self._persisted_school_id = self.school_id

    @classmethod
    def guard_writes(cls, rows: Sequence["TenantModel"]) -> None:
        """Apply the tenancy write rules to rows about to be saved, singly or in bulk.

        New rows without a school get the current school. Every row must belong to
        the current school, must not move from the school it was saved in, and must
        not point at another school's row.
        """
        school_id = ctx().school_id
        if school_id is None:
            raise MissingTenantContextError(
                f"{cls.__name__} saved with no school in the current context"
            )
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
        cls._guard_links(rows)

    @classmethod
    def _guard_links(cls, rows: Sequence["TenantModel"]) -> None:
        # The scoped manager only sees the current school, so a target it cannot find
        # is in another school (or missing). One query per foreign key.
        for field in cls._meta.concrete_fields:
            target = field.related_model
            if not (field.many_to_one and isinstance(target, type) and issubclass(target, TenantModel)):
                continue
            ids = {getattr(row, field.attname) for row in rows} - {None}
            lookup = {f"{field.target_field.attname}__in": ids}
            if ids and target.objects.filter(**lookup).count() != len(ids):
                raise CrossTenantWriteError(
                    f"{cls.__name__}.{field.name} points at a row outside the current school"
                )
