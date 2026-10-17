from collections.abc import Iterable
from typing import Any

from django.apps import apps
from django.core import checks
from django.db import models

from core.models import is_tenant_model


def tenant_model_errors(model_classes: Iterable[type[models.Model]]) -> list[checks.CheckMessage]:
    """Tenancy rules the ORM guards can't enforce at runtime.

    A many-to-many between school-owned models needs a `through` model that is
    itself a TenantModel: Django's auto-created link table has no school and skips
    the write guards, so add() could link rows across schools.
    """
    errors: list[checks.CheckMessage] = []
    for model in model_classes:
        if not is_tenant_model(model):
            continue
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


@checks.register(checks.Tags.models)
def check_tenant_models(app_configs: Any = None, **kwargs: Any) -> list[checks.CheckMessage]:  # reason: Django's check signature
    return tenant_model_errors(apps.get_models())
