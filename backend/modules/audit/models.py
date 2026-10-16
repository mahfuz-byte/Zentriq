from django.db import models

from core.models import TenantModel


class AuditEvent(TenantModel):
    """One audited action, hash-chained per school. The table only: append-only
    enforcement and the hash chain arrive in P1-T07.
    """

    class ActorType(models.TextChoices):
        USER = "USER"
        OPERATOR = "OPERATOR"
        SYSTEM = "SYSTEM"

    actor_type = models.CharField(max_length=20, choices=ActorType.choices)
    actor_id = models.UUIDField(null=True, blank=True)
    actor_role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)

    class Meta(TenantModel.Meta):
        indexes = [
            models.Index(fields=["school", "created_at"], name="audit_event_school_created"),
        ]
