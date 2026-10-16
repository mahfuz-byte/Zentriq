import logging

import pytest
from django.db import transaction
from django.db.models import F, Model

from core.context import system_scope, tenant_context
from core.errors import (
    CrossTenantWriteError,
    MissingTenantContextError,
    SystemScopeRequiredError,
)
from core.tests.tenancy_app.models import Course, CourseTag, Lesson, Syllabus, Tag


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_another_schools_row_is_invisible_by_primary_key(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        other = Course.objects.create(school_id=school_b.pk, title="Riverside Algebra")

    with tenant_context(school_a.pk):
        assert Course.objects.filter(pk=other.pk).first() is None
        with pytest.raises(Course.DoesNotExist):
            Course.objects.get(pk=other.pk)


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_counts_and_iteration_see_only_the_current_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(school_id=school_a.pk, title="Greenfield Algebra")
    with tenant_context(school_b.pk):
        Course.objects.create(school_id=school_b.pk, title="Riverside Algebra")
        Course.objects.create(school_id=school_b.pk, title="Riverside Geometry")

    with tenant_context(school_a.pk):
        assert Course.objects.count() == 1
        assert [c.title for c in Course.objects.all()] == ["Greenfield Algebra"]
        assert not Course.objects.filter(title="Riverside Algebra").exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_querying_without_a_tenant_context_fails_loudly(school_a: Model) -> None:
    with pytest.raises(MissingTenantContextError):
        list(Course.objects.all())


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_all_schools_is_refused_outside_a_system_scope(school_a: Model) -> None:
    with pytest.raises(SystemScopeRequiredError):
        list(Course.all_schools.all())
    with tenant_context(school_a.pk), pytest.raises(SystemScopeRequiredError):
        list(Course.all_schools.all())


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_all_schools_sees_every_school_inside_a_system_scope(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(school_id=school_a.pk, title="Greenfield Algebra")
    with tenant_context(school_b.pk):
        Course.objects.create(school_id=school_b.pk, title="Riverside Algebra")

    with system_scope("test: count courses in every school"):
        assert sorted(c.title for c in Course.all_schools.all()) == [
            "Greenfield Algebra",
            "Riverside Algebra",
        ]


@pytest.mark.req("P1-T02")
@pytest.mark.parametrize("reason", ["", "   "])
def test_system_scope_needs_a_reason(reason: str) -> None:
    with pytest.raises(ValueError), system_scope(reason):
        pass


@pytest.mark.req("P1-T02")
def test_entering_a_system_scope_logs_the_reason(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="as.tenancy"), system_scope("nightly retention"):
        pass
    [record] = caplog.records
    assert record.__dict__["reason"] == "nightly retention"


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_update_in_one_school_leaves_other_schools_untouched(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(school_id=school_a.pk, title="Algebra")
    with tenant_context(school_b.pk):
        Course.objects.create(school_id=school_b.pk, title="Algebra")

    with tenant_context(school_a.pk):
        assert Course.objects.update(title="Renamed") == 1

    with system_scope("test: check school B"):
        assert Course.all_schools.get(school_id=school_b.pk).title == "Algebra"


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_delete_in_one_school_leaves_other_schools_rows(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(school_id=school_a.pk, title="Algebra")
    with tenant_context(school_b.pk):
        Course.objects.create(school_id=school_b.pk, title="Algebra")

    with tenant_context(school_a.pk):
        Course.objects.all().delete()

    with system_scope("test: check school B"):
        assert Course.all_schools.filter(school_id=school_b.pk).count() == 1
        assert not Course.all_schools.filter(school_id=school_a.pk).exists()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_a_new_row_takes_its_school_from_the_context(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        course = Course.objects.create(title="Algebra")
    assert course.school_id == school_a.pk


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_a_school_supplied_as_input_is_never_honoured(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk), pytest.raises(CrossTenantWriteError):
        Course.objects.create(school_id=school_b.pk, title="Smuggled")

    with system_scope("test: nothing was written"):
        assert not Course.all_schools.exists()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_an_existing_row_cannot_move_to_another_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        course = Course.objects.create(title="Algebra")

    course.school_id = school_b.pk
    with tenant_context(school_b.pk), pytest.raises(CrossTenantWriteError):
        course.save()

    with system_scope("test: the row stayed put"):
        assert Course.all_schools.get(pk=course.pk).school_id == school_a.pk


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_saving_without_a_tenant_context_fails_loudly(school_a: Model) -> None:
    with pytest.raises(MissingTenantContextError):
        Course(school_id=school_a.pk, title="Algebra").save()


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_a_row_cannot_link_to_another_schools_row(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk), pytest.raises(CrossTenantWriteError):
        Lesson.objects.create(course=riverside_course, title="Smuggled lesson")

    with system_scope("test: nothing was written"):
        assert not Lesson.all_schools.exists()


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_bulk_create_cannot_link_to_another_schools_row(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        greenfield_course = Course.objects.create(title="Greenfield Algebra")
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk), pytest.raises(CrossTenantWriteError):
        Lesson.objects.bulk_create(
            [
                Lesson(school_id=school_a.pk, course=greenfield_course, title="Fine"),
                Lesson(school_id=school_a.pk, course=riverside_course, title="Smuggled"),
            ]
        )

    with system_scope("test: nothing was written"):
        assert not Lesson.all_schools.exists()


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_bulk_update_cannot_repoint_rows_at_another_schools_row(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")
    with tenant_context(school_a.pk):
        lesson = Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="L1")
        lesson.course_id = riverside_course.id
        with pytest.raises(CrossTenantWriteError):
            Lesson.objects.bulk_update([lesson], ["course"])

    with system_scope("test: the link is unchanged"):
        assert Lesson.all_schools.get(pk=lesson.pk).course_id != riverside_course.id


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_bulk_create_takes_the_school_from_the_context(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        Course.objects.bulk_create([Course(title="Algebra"), Course(title="Geometry")])
        with pytest.raises(CrossTenantWriteError):
            Course.objects.bulk_create([Course(school_id=school_b.pk, title="Smuggled")])

    with system_scope("test: where the rows went"):
        assert sorted(Course.all_schools.values_list("title", "school_id")) == [
            ("Algebra", school_a.pk),
            ("Geometry", school_a.pk),
        ]


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_links_within_one_school_save_on_every_path(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        algebra = Course.objects.create(title="Algebra")
        geometry = Course.objects.create(title="Geometry")
        single = Lesson.objects.create(course=algebra, title="Single")
        [bulk] = Lesson.objects.bulk_create([Lesson(course=algebra, title="Bulk")])
        bulk.course = geometry
        Lesson.objects.bulk_update([bulk], ["course"])

        assert sorted(Lesson.objects.values_list("title", "course__title")) == [
            ("Bulk", "Geometry"),
            ("Single", "Algebra"),
        ]
        assert single.school_id == bulk.school_id == school_a.pk


def _corrupt_link(lesson: Lesson, course: Course) -> None:
    """Point a lesson at another school's course, bypassing the write guards."""
    with system_scope("test: corrupt a link"):
        Lesson.all_schools.filter(pk=lesson.pk).update(course_id=course.pk)


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_following_a_link_never_returns_another_schools_row(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")
    with tenant_context(school_a.pk):
        lesson = Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="L1")
    _corrupt_link(lesson, riverside_course)

    with tenant_context(school_a.pk):
        reloaded = Lesson.objects.get(pk=lesson.pk)
        with pytest.raises(Course.DoesNotExist):
            reloaded.course  # noqa: B018 - the attribute access is the behaviour under test


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_reverse_relations_never_include_another_schools_rows(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_a.pk):
        algebra = Course.objects.create(title="Algebra")
        Lesson.objects.create(course=algebra, title="Greenfield lesson")
    with tenant_context(school_b.pk):
        riverside_lesson = Lesson.objects.create(
            course=Course.objects.create(title="Riverside Algebra"), title="Riverside lesson"
        )
    _corrupt_link(riverside_lesson, algebra)

    with tenant_context(school_a.pk):
        assert [lesson.title for lesson in algebra.lessons.all()] == ["Greenfield lesson"]


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_following_a_relation_without_a_tenant_context_fails_loudly(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        algebra = Course.objects.create(title="Algebra")
        lesson = Lesson.objects.create(course=algebra, title="L1")
        lesson = Lesson.objects.get(pk=lesson.pk)

    with pytest.raises(MissingTenantContextError):
        list(algebra.lessons.all())
    with pytest.raises(MissingTenantContextError):
        lesson.course  # noqa: B018 - the attribute access is the behaviour under test


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_update_cannot_move_rows_to_another_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(title="Algebra")
        with pytest.raises(CrossTenantWriteError):
            Course.objects.update(school_id=school_b.pk)
        with pytest.raises(CrossTenantWriteError):
            Course.objects.update(school=school_b)

    with system_scope("test: the row stayed put"):
        assert not Course.all_schools.filter(school_id=school_b.pk).exists()


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_update_cannot_link_rows_to_another_schools_row(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")
    with tenant_context(school_a.pk):
        lesson = Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="L1")
        with pytest.raises(CrossTenantWriteError):
            Lesson.objects.update(course=riverside_course)
        with pytest.raises(CrossTenantWriteError):
            Lesson.objects.update(course_id=riverside_course.id)

    # add() in school B updates through the scoped base manager, so it can't reach
    # school A's lesson at all.
    with tenant_context(school_b.pk):
        riverside_course.lessons.add(lesson)

    with system_scope("test: the link is unchanged"):
        assert Lesson.all_schools.get(pk=lesson.pk).course_id != riverside_course.id


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_update_refuses_a_link_it_cannot_check(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="L1")
        with pytest.raises(CrossTenantWriteError):
            Lesson.objects.update(course_id=F("course_id"))


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_a_one_to_one_link_cannot_cross_schools(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk), pytest.raises(CrossTenantWriteError):
        Syllabus.objects.create(course=riverside_course)


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_a_many_to_many_link_cannot_cross_schools(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_tag = Tag.objects.create(name="exam-prep")
    with tenant_context(school_a.pk):
        algebra = Course.objects.create(title="Algebra")
        # add() writes inside atomic(savepoint=False); give the refused write its own
        # savepoint so the test's transaction stays usable.
        with pytest.raises(CrossTenantWriteError), transaction.atomic():
            algebra.tags.add(riverside_tag)

    with system_scope("test: nothing was linked"):
        assert not CourseTag.all_schools.exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T02")
def test_a_system_job_can_delete_and_follow_links_across_schools(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_a.pk):
        Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="A1")
    with tenant_context(school_b.pk):
        Lesson.objects.create(course=Course.objects.create(title="Algebra"), title="B1")

    with system_scope("test: retention across schools"):
        assert sorted(lesson.course.title for lesson in Lesson.all_schools.all()) == [
            "Algebra",
            "Algebra",
        ]
        Course.all_schools.all().delete()  # cascades to every school's lessons
        assert not Lesson.all_schools.exists()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_objects_stays_scoped_inside_a_system_scope(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_a.pk):
        Course.objects.create(title="Greenfield Algebra")
    with tenant_context(school_b.pk):
        Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk), system_scope("test: objects is unchanged"):
        assert [c.title for c in Course.objects.all()] == ["Greenfield Algebra"]


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_bulk_create_allows_links_within_the_same_batch(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        algebra = Course(title="Algebra")
        calculus = Course(title="Calculus", prerequisite=algebra)
        Course.objects.bulk_create([algebra, calculus])

        assert Course.objects.get(title="Calculus").prerequisite == algebra


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_a_self_link_to_another_schools_row_is_still_refused(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk):
        with pytest.raises(CrossTenantWriteError):
            Course.objects.bulk_create(
                [Course(title="Fine"), Course(title="Calculus", prerequisite=riverside_course)]
            )
        with pytest.raises(CrossTenantWriteError):
            Course.objects.create(title="Calculus", prerequisite=riverside_course)


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_deleting_another_schools_row_is_refused(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")
        Lesson.objects.create(course=riverside_course, title="B1")

    with tenant_context(school_a.pk):
        with pytest.raises(CrossTenantWriteError):
            Course(id=riverside_course.id).delete()
        with pytest.raises(CrossTenantWriteError):
            riverside_course.delete()

    with system_scope("test: school B is untouched"):
        assert Course.all_schools.filter(pk=riverside_course.pk).exists()
        assert Lesson.all_schools.filter(course=riverside_course).exists()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-002")
def test_bulk_create_refuses_upserts(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk), pytest.raises(CrossTenantWriteError):
        Course.objects.bulk_create(
            [Course(id=riverside_course.id, title="Taken over")],
            update_conflicts=True,
            update_fields=["title", "school"],
            unique_fields=["id"],
        )

    with system_scope("test: school B is untouched"):
        row = Course.all_schools.get(pk=riverside_course.pk)
        assert (row.title, row.school_id) == ("Riverside Algebra", school_b.pk)


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_ignored_conflicts_cannot_smuggle_a_link_to_another_school(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")

    with tenant_context(school_a.pk):
        # The decoy reuses B's id, so its insert is skipped and the link would land on B's row.
        decoy = Course(id=riverside_course.id, title="Decoy")
        with pytest.raises(CrossTenantWriteError):
            Course.objects.bulk_create(
                [decoy, Course(title="Calculus", prerequisite=decoy)], ignore_conflicts=True
            )
        assert not Course.objects.exists()


@pytest.mark.django_db
@pytest.mark.req("C-01")
def test_a_system_scope_inside_a_school_still_writes_only_that_school(
    school_a: Model, school_b: Model
) -> None:
    with tenant_context(school_a.pk):
        greenfield_course = Course.objects.create(title="Greenfield Algebra")
    with tenant_context(school_b.pk):
        riverside_course = Course.objects.create(title="Riverside Algebra")
        riverside_lesson = Lesson.objects.create(course=riverside_course, title="B1")

    with tenant_context(school_a.pk), system_scope("test: relink attempt"):
        greenfield_course.lessons.add(riverside_lesson)
        Lesson._base_manager.filter(pk=riverside_lesson.pk).update(course=greenfield_course)

    with system_scope("test: school B is untouched"):
        assert Lesson.all_schools.get(pk=riverside_lesson.pk).course_id == riverside_course.id
