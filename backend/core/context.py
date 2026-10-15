from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
import logging
from uuid import UUID

from core.errors import MissingTenantContextError

logger = logging.getLogger("as.tenancy")


@dataclass(frozen=True)
class RequestContext:
    request_id: str | None = None
    school_id: UUID | None = None
    user_id: UUID | None = None
    roles: tuple[str, ...] = ()
    active_role: str | None = None
    session_id: UUID | None = None
    # Set only inside `system_scope`: why this code may read across schools.
    system_scope_reason: str | None = None


_current: ContextVar[RequestContext] = ContextVar("as_request_context", default=RequestContext())


def ctx() -> RequestContext:
    return _current.get()


def require_school_id(what: str) -> UUID:
    """The current school, or MissingTenantContextError naming `what` needed it."""
    school_id = ctx().school_id
    if school_id is None:
        raise MissingTenantContextError(f"{what} needs a school in the current context")
    return school_id


@contextmanager
def _entered(context: RequestContext) -> Iterator[RequestContext]:
    token = _current.set(context)
    try:
        yield context
    finally:
        _current.reset(token)


@contextmanager
def tenant_context(school_id: UUID) -> Iterator[RequestContext]:
    """Enter one school's scope outside a request: tests, seeds, Celery tasks."""
    with _entered(RequestContext(school_id=school_id)) as context:
        yield context


@contextmanager
def request_context(
    *,
    request_id: str,
    school_id: UUID | None,
    user_id: UUID | None,
    roles: tuple[str, ...],
    active_role: str | None,
    session_id: UUID | None,
) -> Iterator[RequestContext]:
    """Enter a request's scope. Used by the auth middleware."""
    context = RequestContext(
        request_id=request_id,
        school_id=school_id,
        user_id=user_id,
        roles=roles,
        active_role=active_role,
        session_id=session_id,
    )
    with _entered(context) as entered:
        yield entered


@contextmanager
def system_scope(reason: str) -> Iterator[RequestContext]:
    """Allow the unscoped `all_schools` manager for this block. Every use is recorded."""
    if not reason.strip():
        raise ValueError("system_scope needs a reason")
    # P1-T07 replaces this log event with an audit record.
    logger.info("system_scope entered", extra={"reason": reason, "school_id": ctx().school_id})
    with _entered(replace(ctx(), system_scope_reason=reason)) as context:
        yield context
