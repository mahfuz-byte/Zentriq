import pytest
from django.core.management import CommandError, call_command

from core.context import system_scope, tenant_context
from modules.accounts.models import RoleAssignment, School, User

SEED_PASSWORD = "Local-Only-Seed-Password-2026"


def row_counts() -> tuple[int, int, int]:
    with system_scope("test: count seeded rows"):
        return (
            School.objects.count(),
            User.all_schools.count(),
            RoleAssignment.all_schools.count(),
        )


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_the_seed_creates_greenfield_with_one_user_per_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_PASSWORD", SEED_PASSWORD)

    call_command("seed")

    school = School.objects.get(slug="greenfield")
    with tenant_context(school.id):
        roles = {
            user.username: [a.role for a in user.role_assignments.all()]
            for user in User.objects.all()
        }
        assert roles == {
            "admin": ["SCHOOL_ADMIN"],
            "t.rivera": ["TEACHER"],
            "sara": ["STUDENT"],
        }
        for user in User.objects.all():
            assert user.is_active
            assert user.check_password(SEED_PASSWORD)


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_running_the_seed_twice_changes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_PASSWORD", SEED_PASSWORD)

    call_command("seed")
    first = row_counts()
    call_command("seed")

    assert row_counts() == first == (1, 3, 3)


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_the_seed_refuses_to_run_without_a_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEED_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="SEED_PASSWORD"):
        call_command("seed")
    assert not School.objects.exists()
