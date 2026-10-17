import pytest
from django.db import IntegrityError, transaction
from django.test import override_settings

from config.settings import base as base_settings
from core.context import tenant_context
from modules.accounts.models import RoleAssignment, School, User
from modules.accounts.tests.factories import RoleAssignmentFactory, UserFactory


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_usernames_are_unique_per_school_only(school_a: School, school_b: School) -> None:
    with tenant_context(school_a.id):
        UserFactory(username="admin", display_name="Greenfield Admin")
    with tenant_context(school_b.id):
        UserFactory(username="admin", display_name="Riverside Admin")

        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(username="admin", display_name="Second Riverside Admin")


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_usernames_and_emails_ignore_case_within_a_school(school_a: School) -> None:
    with tenant_context(school_a.id):
        UserFactory(username="admin", email="head@greenfield.test", display_name="Head")

        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(username="Admin", display_name="Impostor")
        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(username="other", email="HEAD@greenfield.test", display_name="Copy")


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_email_is_optional(school_a: School) -> None:
    with tenant_context(school_a.id):
        UserFactory(username="s9a-01", display_name="Student One")
        UserFactory(username="s9a-02", display_name="Student Two")

        assert User.objects.filter(email__isnull=True).count() == 2


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_users_are_scoped_to_the_current_school(school_a: School, school_b: School) -> None:
    with tenant_context(school_a.id):
        UserFactory(username="admin", display_name="Greenfield Admin")
    with tenant_context(school_b.id):
        UserFactory(username="admin", display_name="Riverside Admin")

        assert [u.display_name for u in User.objects.all()] == ["Riverside Admin"]


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_user_holds_each_role_at_most_once(school_a: School) -> None:
    with tenant_context(school_a.id):
        user = UserFactory(username="t.rivera", display_name="T. Rivera")
        RoleAssignmentFactory(user=user, role=RoleAssignment.Role.TEACHER)
        RoleAssignmentFactory(user=user, role=RoleAssignment.Role.SCHOOL_ADMIN)

        with pytest.raises(IntegrityError), transaction.atomic():
            RoleAssignmentFactory(user=user, role=RoleAssignment.Role.TEACHER)
        assert sorted(user.role_assignments.values_list("role", flat=True)) == [
            "SCHOOL_ADMIN",
            "TEACHER",
        ]


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-005")
def test_passwords_are_hashed_with_argon2id(school_a: School) -> None:
    with override_settings(PASSWORD_HASHERS=base_settings.PASSWORD_HASHERS), tenant_context(
        school_a.id
    ):
        user = UserFactory(username="sara", display_name="Sara")
        user.set_password("correct horse battery staple")
        user.save()

        stored = User.objects.get(pk=user.pk)
        assert stored.password.startswith("argon2$argon2id$")
        assert stored.check_password("correct horse battery staple")


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_new_user_cannot_sign_in_until_a_password_is_set(school_a: School) -> None:
    with tenant_context(school_a.id):
        user = UserFactory(username="invited", display_name="Invited")

        stored = User.objects.get(pk=user.pk)
        assert not stored.has_usable_password()
        assert stored.status == User.Status.INVITED
        assert not stored.is_active


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_user_is_found_by_username_in_any_case(school_a: School, school_b: School) -> None:
    with tenant_context(school_b.id):
        UserFactory(username="Admin", display_name="Riverside Admin")
    with tenant_context(school_a.id):
        admin = UserFactory(username="Admin", display_name="Greenfield Admin")

        assert User.objects.get_by_natural_key("admin") == admin
        assert User.objects.get_by_natural_key("ADMIN") == admin
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key("nobody")
