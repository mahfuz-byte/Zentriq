import pytest
from django.apps import apps
from django.db.models import Model


# Shared by core and modules tests. core must not import modules (BUILD_PLAN §8.2),
# so the tenant root is looked up by name.
def _create_school(slug: str, name: str) -> Model:
    return apps.get_model("accounts", "School").objects.create(slug=slug, name=name)


@pytest.fixture
def school_a(db: None) -> Model:
    return _create_school("greenfield", "Greenfield School")


@pytest.fixture
def school_b(db: None) -> Model:
    return _create_school("riverside", "Riverside School")
