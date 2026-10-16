import pytest
from django.apps import apps
from django.db import models
from django.test.utils import isolate_apps

from core.checks import tenant_model_errors
from core.models import TenantModel


@pytest.mark.req("C-01")
@isolate_apps("core.tests.tenancy_app")
def test_a_plain_many_to_many_between_tenant_models_is_an_error() -> None:
    class Badge(TenantModel):
        class Meta:
            app_label = "tenancy_app"

    class Student(TenantModel):
        badges = models.ManyToManyField(Badge)

        class Meta:
            app_label = "tenancy_app"

    [error] = tenant_model_errors([Badge, Student])
    assert error.id == "core.E001"
    assert error.obj is Student._meta.get_field("badges")


@pytest.mark.req("C-01")
def test_the_registered_models_pass_the_tenancy_checks() -> None:

    assert tenant_model_errors(apps.get_models()) == []
