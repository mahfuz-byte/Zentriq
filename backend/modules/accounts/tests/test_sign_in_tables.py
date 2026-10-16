import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from django.db import IntegrityError, transaction

from core.context import tenant_context
from modules.accounts.models import (
    Invitation,
    OperatorAccount,
    PasswordResetToken,
    School,
    Session,
    User,
)

# Fixed times: these tests check storage rules, not expiry behaviour (P1-T03/T04).
LATER = datetime(2026, 11, 1, tzinfo=UTC)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(**owner: User | OperatorAccount | None) -> Session:
    return Session.objects.create(
        token_hash=token_hash(str(owner)),
        active_role="TEACHER",
        idle_expires_at=LATER,
        absolute_expires_at=LATER + timedelta(hours=12),
        **owner,
    )


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_session_belongs_to_exactly_one_user_or_operator(school_a: School) -> None:
    operator = OperatorAccount.objects.create(email="ops@as.test")
    with tenant_context(school_a.id):
        user = User.objects.create(username="t.rivera", display_name="T. Rivera")

    new_session(user=user)
    new_session(operator=operator)
    with pytest.raises(IntegrityError), transaction.atomic():
        new_session(user=user, operator=operator)
    with pytest.raises(IntegrityError), transaction.atomic():
        new_session()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-005")
def test_each_token_hash_is_stored_once(school_a: School) -> None:
    with tenant_context(school_a.id):
        user = User.objects.create(username="sara", display_name="Sara")
        Invitation.objects.create(user=user, token_hash=token_hash("a"), expires_at=LATER)
        PasswordResetToken.objects.create(user=user, token_hash=token_hash("a"), expires_at=LATER)

        with pytest.raises(IntegrityError), transaction.atomic():
            Invitation.objects.create(user=user, token_hash=token_hash("a"), expires_at=LATER)
        with pytest.raises(IntegrityError), transaction.atomic():
            PasswordResetToken.objects.create(
                user=user, token_hash=token_hash("a"), expires_at=LATER
            )


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_invitations_and_reset_tokens_are_scoped_to_the_current_school(
    school_a: School, school_b: School
) -> None:
    with tenant_context(school_b.id):
        riverside_user = User.objects.create(username="sara", display_name="Sara")
        Invitation.objects.create(
            user=riverside_user, token_hash=token_hash("b"), expires_at=LATER
        )
        PasswordResetToken.objects.create(
            user=riverside_user, token_hash=token_hash("b"), expires_at=LATER
        )

    with tenant_context(school_a.id):
        assert not Invitation.objects.exists()
        assert not PasswordResetToken.objects.exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_operator_emails_are_unique_ignoring_case() -> None:
    OperatorAccount.objects.create(email="ops@as.test")

    with pytest.raises(IntegrityError), transaction.atomic():
        OperatorAccount.objects.create(email="OPS@as.test")
