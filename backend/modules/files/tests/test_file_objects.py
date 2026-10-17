import pytest
from django.db import IntegrityError, transaction
from django.db.models import Model

from core.context import tenant_context
from modules.files.models import FileObject
from modules.files.tests.factories import FileObjectFactory


@pytest.mark.django_db
@pytest.mark.req("P1-T01", "DR-005")
def test_storage_keys_are_unique_and_files_start_unscanned(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        logo = FileObjectFactory.create(storage_key="k-1")
        assert FileObject.objects.get(pk=logo.pk).scan_status == FileObject.ScanStatus.PENDING

        with pytest.raises(IntegrityError), transaction.atomic():
            FileObjectFactory.create(storage_key="k-1")


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_files_are_scoped_to_the_current_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        FileObjectFactory.create()
    with tenant_context(school_a.pk):
        assert not FileObject.objects.exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T01", "DR-005")
def test_a_school_has_its_profile_and_a_logo(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        logo = FileObjectFactory.create()
    # The School model is looked up from the fixture: modules.files may not import
    # accounts.models (BUILD_PLAN §8.2).
    school_model = type(school_a)
    school_model._default_manager.filter(pk=school_a.pk).update(
        logo_file=logo, description="A fictional secondary school"
    )

    school = school_model._default_manager.filter(pk=school_a.pk).values(
        "status", "locale", "timezone", "settings", "logo_file_id"
    )
    assert list(school) == [
        {
            "status": "ACTIVE",
            "locale": "en",
            "timezone": "UTC",
            "settings": {},
            "logo_file_id": logo.id,
        }
    ]
