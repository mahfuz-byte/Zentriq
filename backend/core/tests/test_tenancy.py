import pytest

from core.context import tenant_context
from core.tests.tenancy_app.models import Course


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_another_schools_row_is_invisible_by_primary_key(school_a, school_b):
    with tenant_context(school_b.id):
        other = Course.objects.create(school=school_b, title="Riverside Algebra")

    with tenant_context(school_a.id):
        assert Course.objects.filter(pk=other.pk).first() is None
        with pytest.raises(Course.DoesNotExist):
            Course.objects.get(pk=other.pk)
