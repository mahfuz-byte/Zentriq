import pytest

from core.context import tenant_context
from core.errors import MissingTenantContextError
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


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_counts_and_iteration_see_only_the_current_school(school_a, school_b):
    with tenant_context(school_a.id):
        Course.objects.create(school=school_a, title="Greenfield Algebra")
    with tenant_context(school_b.id):
        Course.objects.create(school=school_b, title="Riverside Algebra")
        Course.objects.create(school=school_b, title="Riverside Geometry")

    with tenant_context(school_a.id):
        assert Course.objects.count() == 1
        assert [c.title for c in Course.objects.all()] == ["Greenfield Algebra"]
        assert not Course.objects.filter(title="Riverside Algebra").exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_querying_without_a_tenant_context_fails_loudly(school_a):
    with pytest.raises(MissingTenantContextError):
        list(Course.objects.all())
