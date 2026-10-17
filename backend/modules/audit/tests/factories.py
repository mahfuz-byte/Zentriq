"""Test data for audit (BUILD_PLAN §9.3). Create rows inside `tenant_context(...)`."""

import uuid

import factory

from modules.accounts.roles import Role
from modules.audit.models import AuditEvent


class AuditEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditEvent

    actor_type = AuditEvent.ActorType.USER
    actor_id = factory.LazyFunction(uuid.uuid4)
    actor_role = Role.SCHOOL_ADMIN
    action = "user.invited"
    entity_type = "accounts.User"
    entity_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    after = factory.LazyFunction(lambda: {"status": "ACTIVE"})
    ip = "203.0.113.7"
    request_id = "req-1"
    prev_hash = "0" * 64
    hash = "1" * 64
