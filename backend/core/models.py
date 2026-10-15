import uuid
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
        school_id = ctx().school_id
        if school_id is None:
            raise MissingTenantContextError(
                f"{type(self).__name__} saved with no school in the current context"
            )
        if self._state.adding and self.school_id is None:
            self.school_id = school_id
        if self.school_id != school_id:
            raise CrossTenantWriteError(
                f"{type(self).__name__} belongs to school {self.school_id}, "
                f"not the current school {school_id}"
            )
        if not self._state.adding and self.school_id != self._persisted_school_id:
            raise CrossTenantWriteError(f"{type(self).__name__} cannot move to another school")
        super().save(*args, **kwargs)
        self._persisted_school_id = self.school_id
