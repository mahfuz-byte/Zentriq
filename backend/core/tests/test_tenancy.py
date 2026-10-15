import logging

import pytest

from core.context import system_scope, tenant_context
from core.errors import MissingTenantContextError, SystemScopeRequiredError
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


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_all_schools_is_refused_outside_a_system_scope(school_a):
    with pytest.raises(SystemScopeRequiredError):
        list(Course.all_schools.all())
    with tenant_context(school_a.id), pytest.raises(SystemScopeRequiredError):
        list(Course.all_schools.all())


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_all_schools_sees_every_school_inside_a_system_scope(school_a, school_b):
    with tenant_context(school_a.id):
        Course.objects.create(school=school_a, title="Greenfield Algebra")
    with tenant_context(school_b.id):
        Course.objects.create(school=school_b, title="Riverside Algebra")

    with system_scope("test: count courses in every school"):
        assert sorted(c.title for c in Course.all_schools.all()) == [
            "Greenfield Algebra",
            "Riverside Algebra",
        ]


@pytest.mark.req("P1-T02")
@pytest.mark.parametrize("reason", ["", "   "])
def test_system_scope_needs_a_reason(reason):
    with pytest.raises(ValueError), system_scope(reason):
        pass


@pytest.mark.req("P1-T02")
def test_entering_a_system_scope_logs_the_reason(caplog):
    with caplog.at_level(logging.INFO, logger="as.tenancy"), system_scope("nightly retention"):
        pass
    [record] = caplog.records
    assert record.reason == "nightly retention"


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_update_in_one_school_leaves_other_schools_untouched(school_a, school_b):
    with tenant_context(school_a.id):
        Course.objects.create(school=school_a, title="Algebra")
    with tenant_context(school_b.id):
        Course.objects.create(school=school_b, title="Algebra")

    with tenant_context(school_a.id):
        assert Course.objects.update(title="Renamed") == 1

    with system_scope("test: check school B"):
        assert Course.all_schools.get(school=school_b).title == "Algebra"


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_delete_in_one_school_leaves_other_schools_rows(school_a, school_b):
    with tenant_context(school_a.id):
        Course.objects.create(school=school_a, title="Algebra")
    with tenant_context(school_b.id):
        Course.objects.create(school=school_b, title="Algebra")

    with tenant_context(school_a.id):
        Course.objects.all().delete()

    with system_scope("test: check school B"):
        assert Course.all_schools.filter(school=school_b).count() == 1
        assert not Course.all_schools.filter(school=school_a).exists()
