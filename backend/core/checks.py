from collections.abc import Iterable
from typing import Any

from django.apps import apps
from django.core import checks
from django.db import models

from core.models import TenantModel, is_tenant_model


def tenant_model_errors(model_classes: Iterable[type[models.Model]]) -> list[checks.CheckMessage]:
    """Tenancy rules the ORM guards can't enforce at runtime.

    A TenantModel must keep the scoped base manager: a `Meta` that doesn't subclass
    `TenantModel.Meta` drops `base_manager_name`, and forward links then load rows
    from any school.

    A many-to-many between school-owned models needs a `through` model that is
    itself a TenantModel: Django's auto-created link table has no school and skips
    the write guards, so add() could link rows across schools.

    A unique constraint or index declared in Meta starts with `school` (BUILD_PLAN
    §5.4): a unique across schools reveals whether a value exists in another school,
    and an index that doesn't lead with school doesn't serve school-scoped queries.
    Field-level `unique=True` is for deliberately global values (token hashes,
    storage keys) and isn't checked.
    """
    errors: list[checks.CheckMessage] = []
    for model in model_classes:
        if not is_tenant_model(model):
            continue
        if model._meta.base_manager_name != TenantModel._meta.base_manager_name:
            errors.append(
                checks.Error(
                    "A TenantModel's Meta must subclass TenantModel.Meta, "
                    "or it loses the school-scoped base manager.",
                    obj=model,
                    id="core.E002",
                )
            )
        for name in _declared_without_school_first(model):
            errors.append(
                checks.Error(
                    f"`{name}` must start with `school`, like every unique constraint "
                    "and index of a school-owned model.",
                    obj=model,
                    id="core.E003",
                )
            )
        for field in model._meta.local_many_to_many:
            if is_tenant_model(field.related_model) and not is_tenant_model(
                field.remote_field.through
            ):
                errors.append(
                    checks.Error(
                        "A many-to-many between school-owned models must use a "
                        "`through` model that is a TenantModel.",
                        obj=field,
                        id="core.E001",
                    )
                )
    return errors


def _declared_without_school_first(model: type[models.Model]) -> list[str]:
    declared = [
        *(c for c in model._meta.constraints if isinstance(c, models.UniqueConstraint)),
        *model._meta.indexes,
    ]
    return [d.name for d in declared if _first_column(d) not in {"school", "school_id"}]


def _first_column(declared: models.UniqueConstraint | models.Index) -> str | None:
    if declared.fields:
        return declared.fields[0].removeprefix("-")
    first = declared.expressions[0] if declared.expressions else None
    return first.name if isinstance(first, models.F) else None


@checks.register(checks.Tags.models)
def check_tenant_models(app_configs: Any = None, **kwargs: Any) -> list[checks.CheckMessage]:  # reason: Django's check signature
    return tenant_model_errors(apps.get_models())
