"""Test data for accounts (BUILD_PLAN §9.3). School-owned rows take their school from
the tenant context, so create them inside `tenant_context(...)`.
"""

import hashlib
from datetime import UTC, datetime, timedelta

import factory

from modules.accounts.models import (
    Invitation,
    OperatorAccount,
    PasswordResetToken,
    RoleAssignment,
    Session,
    User,
)
from modules.accounts.roles import Role

# Fixed, far-off times: factories build valid rows, not expiry scenarios.
LATER = datetime(2026, 11, 1, tzinfo=UTC)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _unique_token_hash(n: int) -> str:
    return token_hash(f"factory-token-{n}")


class UserFactory(factory.django.DjangoModelFactory[User]):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    display_name = factory.Sequence(lambda n: f"User {n}")


class RoleAssignmentFactory(factory.django.DjangoModelFactory[RoleAssignment]):
    class Meta:
        model = RoleAssignment

    user = factory.SubFactory(UserFactory)
    role = Role.TEACHER


class OperatorAccountFactory(factory.django.DjangoModelFactory[OperatorAccount]):
    class Meta:
        model = OperatorAccount

    email = factory.Sequence(lambda n: f"ops-{n}@as.test")


class SessionFactory(factory.django.DjangoModelFactory[Session]):
    """Pass `user=` or `operator=`: a session belongs to exactly one."""

    class Meta:
        model = Session

    user = None
    operator = None
    token_hash = factory.Sequence(_unique_token_hash)
    active_role = factory.LazyAttribute(lambda o: Role.TEACHER if o.user else "")
    idle_expires_at = LATER
    absolute_expires_at = LATER + timedelta(hours=12)


class InvitationFactory(factory.django.DjangoModelFactory[Invitation]):
    class Meta:
        model = Invitation

    user = factory.SubFactory(UserFactory)
    token_hash = factory.Sequence(_unique_token_hash)
    expires_at = LATER


class PasswordResetTokenFactory(factory.django.DjangoModelFactory[PasswordResetToken]):
    class Meta:
        model = PasswordResetToken

    user = factory.SubFactory(UserFactory)
    token_hash = factory.Sequence(_unique_token_hash)
    expires_at = LATER
