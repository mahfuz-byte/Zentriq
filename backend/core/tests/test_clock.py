from datetime import UTC, date, datetime, timedelta

import pytest

from core import clock

NOON = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


@pytest.mark.req("P0-T05")
def test_the_clock_reads_utc_time() -> None:
    before = datetime.now(UTC)  # noqa: TID251 - compared against the real clock on purpose
    now = clock.now()

    assert now.tzinfo is UTC
    assert abs(now - before) < timedelta(seconds=5)


@pytest.mark.req("P0-T05")
def test_the_clock_can_be_fixed_and_advanced() -> None:
    with clock.frozen(NOON) as frozen:
        assert clock.now() == NOON
        assert clock.today() == date(2026, 10, 17)

        frozen.advance(timedelta(hours=13))

        assert clock.now() == NOON + timedelta(hours=13)
        assert clock.today() == date(2026, 10, 18)


@pytest.mark.req("P0-T05")
def test_a_frozen_clock_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone"), clock.frozen(datetime(2026, 10, 17)):
        pass
