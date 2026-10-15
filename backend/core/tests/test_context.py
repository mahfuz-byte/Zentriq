import threading
from uuid import UUID

import pytest

from core.context import ctx, request_context, tenant_context

SCHOOL_A = UUID("00000000-0000-0000-0000-00000000000a")
SCHOOL_B = UUID("00000000-0000-0000-0000-00000000000b")
USER_1 = UUID("00000000-0000-0000-0000-000000000001")
SESSION_1 = UUID("00000000-0000-0000-0000-000000000051")


@pytest.mark.req("P1-T02")
def test_outside_any_context_there_is_no_school():
    assert ctx().school_id is None


@pytest.mark.req("P1-T02")
def test_tenant_context_sets_the_school_only_inside_the_block():
    with tenant_context(SCHOOL_A):
        assert ctx().school_id == SCHOOL_A
    assert ctx().school_id is None


@pytest.mark.req("P1-T02")
def test_request_context_exposes_the_request_identity():
    with request_context(
        request_id="req-123",
        school_id=SCHOOL_A,
        user_id=USER_1,
        roles=("teacher", "admin"),
        active_role="teacher",
        session_id=SESSION_1,
    ):
        current = ctx()
        assert current.request_id == "req-123"
        assert current.school_id == SCHOOL_A
        assert current.user_id == USER_1
        assert current.roles == ("teacher", "admin")
        assert current.active_role == "teacher"
        assert current.session_id == SESSION_1
    assert ctx().user_id is None


@pytest.mark.req("P1-T02")
def test_nested_tenant_context_restores_the_outer_school():
    with tenant_context(SCHOOL_A):
        with tenant_context(SCHOOL_B):
            assert ctx().school_id == SCHOOL_B
        assert ctx().school_id == SCHOOL_A


@pytest.mark.req("P1-T02")
def test_context_does_not_leak_when_the_block_raises():
    with pytest.raises(RuntimeError), tenant_context(SCHOOL_A):
        raise RuntimeError("task failed")
    assert ctx().school_id is None


@pytest.mark.req("P1-T02")
def test_context_is_not_visible_from_another_thread():
    seen: list[UUID | None] = []
    with tenant_context(SCHOOL_A):
        worker = threading.Thread(target=lambda: seen.append(ctx().school_id))
        worker.start()
        worker.join()
    assert seen == [None]
