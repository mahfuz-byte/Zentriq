import pytest

from modules.accounts.models import School


@pytest.fixture
def school_a(db: None) -> School:
    return School.objects.create(slug="greenfield", name="Greenfield School")


@pytest.fixture
def school_b(db: None) -> School:
    return School.objects.create(slug="riverside", name="Riverside School")
