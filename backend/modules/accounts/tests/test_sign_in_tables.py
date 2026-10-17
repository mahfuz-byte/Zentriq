import pytest
from django.db import IntegrityError, transaction

from core.context import tenant_context
from modules.accounts.models import Invitation, PasswordResetToken, School
from modules.accounts.tests.factories import (
    InvitationFactory,
    OperatorAccountFactory,
    PasswordResetTokenFactory,
    SessionFactory,
    UserFactory,
    token_hash,
)

# These tests check storage rules, not expiry behaviour (P1-T03/T04): the factories
# use fixed times.


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_session_belongs_to_exactly_one_user_or_operator(school_a: School) -> None:
    operator = OperatorAccountFactory.create()
    with tenant_context(school_a.id):
        user = UserFactory.create()

    SessionFactory.create(user=user)
    SessionFactory.create(operator=operator)
    with pytest.raises(IntegrityError), transaction.atomic():
        SessionFactory.create(user=user, operator=operator)
    with pytest.raises(IntegrityError), transaction.atomic():
        SessionFactory.create()


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-005")
def test_each_token_hash_is_stored_once(school_a: School) -> None:
    with tenant_context(school_a.id):
        user = UserFactory.create()
        InvitationFactory.create(user=user, token_hash=token_hash("a"))
        PasswordResetTokenFactory.create(user=user, token_hash=token_hash("a"))

        with pytest.raises(IntegrityError), transaction.atomic():
            InvitationFactory.create(user=user, token_hash=token_hash("a"))
        with pytest.raises(IntegrityError), transaction.atomic():
            PasswordResetTokenFactory.create(user=user, token_hash=token_hash("a"))


@pytest.mark.django_db
@pytest.mark.req("NFR-SEC-003")
def test_invitations_and_reset_tokens_are_scoped_to_the_current_school(
    school_a: School, school_b: School
) -> None:
    with tenant_context(school_b.id):
        riverside_user = UserFactory.create()
        InvitationFactory.create(user=riverside_user)
        PasswordResetTokenFactory.create(user=riverside_user)

    with tenant_context(school_a.id):
        assert not Invitation.objects.exists()
        assert not PasswordResetToken.objects.exists()


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_operator_emails_are_unique_ignoring_case() -> None:
    OperatorAccountFactory.create(email="ops@as.test")

    with pytest.raises(IntegrityError), transaction.atomic():
        OperatorAccountFactory.create(email="OPS@as.test")


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_a_user_session_acts_as_a_real_role_and_an_operator_session_as_none(
    school_a: School,
) -> None:
    operator = OperatorAccountFactory.create()
    with tenant_context(school_a.id):
        user = UserFactory.create()

    with pytest.raises(IntegrityError), transaction.atomic():
        SessionFactory.create(user=user, active_role="WIZARD")
    with pytest.raises(IntegrityError), transaction.atomic():
        SessionFactory.create(user=user, active_role="")
    with pytest.raises(IntegrityError), transaction.atomic():
        SessionFactory.create(operator=operator, active_role="TEACHER")
