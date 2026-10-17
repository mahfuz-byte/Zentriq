import pytest
from django.apps import apps
from django.db import models
from django.db.models.functions import Lower
from django.test.utils import isolate_apps

from core.checks import tenant_model_errors
from core.models import TenantModel


@pytest.mark.req("C-01")
@isolate_apps("core.tests.tenancy_app")
def test_a_plain_many_to_many_between_tenant_models_is_an_error() -> None:
    class Badge(TenantModel):
        class Meta(TenantModel.Meta):
            app_label = "tenancy_app"

    class Student(TenantModel):
        badges = models.ManyToManyField(Badge)

        class Meta(TenantModel.Meta):
            app_label = "tenancy_app"

    [error] = tenant_model_errors([Badge, Student])
    assert error.id == "core.E001"
    assert error.obj is Student._meta.get_field("badges")


@pytest.mark.req("C-01")
def test_the_registered_models_pass_the_tenancy_checks() -> None:

    assert tenant_model_errors(apps.get_models()) == []


@pytest.mark.req("NFR-SEC-003")
@isolate_apps("core.tests.tenancy_app")
def test_a_tenant_model_that_drops_the_scoped_base_manager_is_an_error() -> None:
    # Declaring Meta without subclassing TenantModel.Meta loses base_manager_name,
    # so forward links would load rows from any school.
    class Report(TenantModel):
        class Meta:
            app_label = "tenancy_app"

    class Summary(TenantModel):
        class Meta(TenantModel.Meta):
            app_label = "tenancy_app"

    [error] = tenant_model_errors([Report, Summary])
    assert error.id == "core.E002"
    assert error.obj is Report


@pytest.mark.req("C-01")
@isolate_apps("core.tests.tenancy_app")
def test_a_tenant_models_declared_uniques_and_indexes_must_start_with_school() -> None:
    # A unique or index without school first serves every school at once: a unique
    # leaks whether a value exists in another school, and an index isn't used by
    # school-scoped queries.
    class Badge(TenantModel):
        code = models.CharField(max_length=20)
        awarded_at = models.DateTimeField()

        class Meta(TenantModel.Meta):
            app_label = "tenancy_app"
            constraints = [
                models.UniqueConstraint(fields=["code", "school"], name="badge_code_uniq"),
                models.UniqueConstraint(Lower("code"), "school", name="badge_lower_code_uniq"),
                models.UniqueConstraint("school", Lower("code"), name="badge_school_code_uniq"),
            ]
            indexes = [
                models.Index(fields=["awarded_at"], name="badge_awarded"),
                models.Index(fields=["school", "awarded_at"], name="badge_school_awarded"),
            ]

    errors = tenant_model_errors([Badge])

    assert [(e.id, e.obj) for e in errors] == [("core.E003", Badge)] * 3
    assert [e.msg.split("`")[1] for e in errors] == [
        "badge_code_uniq",
        "badge_lower_code_uniq",
        "badge_awarded",
    ]
