import pytest


@pytest.mark.req("P0-T05")
def test_ci_blocks_a_failing_test() -> None:
    # Throwaway: proves a red test fails CI. Never merged.
    assert 1 + 1 == 3
