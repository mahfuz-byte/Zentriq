import pytest
from django.db import IntegrityError, transaction
from django.db.models import Model

from core.context import tenant_context
from modules.audit.models import AuditEvent
from modules.audit.tests.factories import AuditEventFactory


@pytest.mark.django_db
@pytest.mark.req("NFR-AUD-002")
def test_audit_events_are_scoped_to_the_current_school(school_a: Model, school_b: Model) -> None:
    with tenant_context(school_b.pk):
        AuditEventFactory(action="user.activated")
    with tenant_context(school_a.pk):
        AuditEventFactory(action="user.invited")

        assert [e.action for e in AuditEvent.objects.all()] == ["user.invited"]


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_an_actor_role_is_a_school_role_or_empty(school_a: Model) -> None:
    with tenant_context(school_a.pk):
        AuditEventFactory(actor_role="")

        with pytest.raises(IntegrityError), transaction.atomic():
            AuditEventFactory(actor_role="WIZARD")
