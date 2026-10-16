import uuid

import pytest
from django.db.models import Model

from core.context import tenant_context
from modules.audit.models import AuditEvent


def record(action: str) -> AuditEvent:
    return AuditEvent.objects.create(
        actor_type=AuditEvent.ActorType.USER,
        actor_id=uuid.uuid4(),
        actor_role="SCHOOL_ADMIN",
        action=action,
        entity_type="accounts.User",
        entity_id=str(uuid.uuid4()),
        after={"status": "ACTIVE"},
        ip="203.0.113.7",
        request_id="req-1",
        prev_hash="0" * 64,
        hash="1" * 64,
    )


@pytest.mark.django_db
@pytest.mark.req("NFR-AUD-002")
def test_audit_events_are_scoped_to_the_current_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        record("user.activated")
    with tenant_context(school_a.pk):
        record("user.invited")

        assert [e.action for e in AuditEvent.objects.all()] == ["user.invited"]
