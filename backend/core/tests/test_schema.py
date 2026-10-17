import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from core.models import tenant_models


def has_school_link(model: type[models.Model]) -> bool:
    try:
        field = model._meta.get_field("school")
    except FieldDoesNotExist:
        return False
    return isinstance(field, models.ForeignKey) and field.related_model is apps.get_model(
        "accounts", "School"
    )


@pytest.mark.req("DR-002")
def test_tenant_models_are_exactly_the_models_with_a_school() -> None:
    linked = {m for m in apps.get_models() if has_school_link(m)}

    assert set(tenant_models()) == linked


@pytest.mark.req("DR-002")
def test_tenant_models_cover_the_school_owned_tables() -> None:
    labels = {m._meta.label for m in tenant_models()}

    assert {
        "accounts.User",
        "accounts.RoleAssignment",
        "accounts.Invitation",
        "accounts.PasswordResetToken",
        "audit.AuditEvent",
        "files.FileObject",
    } <= labels
    assert labels.isdisjoint({"accounts.School", "accounts.Session", "accounts.OperatorAccount"})
