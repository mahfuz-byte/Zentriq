"""The only place the application reads the time (BUILD_PLAN §8.4).

Everything else calls `now()` or `today()`, so tests can fix the time with `frozen()`.
Reading the clock any other way fails lint.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta


@dataclass
class FrozenClock:
    """A fixed time for tests. `advance()` moves it forward."""

    at: datetime

    def advance(self, delta: timedelta) -> None:
        self.at += delta


_frozen: ContextVar[FrozenClock | None] = ContextVar("as_frozen_clock", default=None)


def now() -> datetime:
    """The current time, in UTC."""
    frozen = _frozen.get()
    return frozen.at if frozen is not None else datetime.now(UTC)


def today() -> date:
    """Today's date in UTC. Show dates in the school's time zone at the edges."""
    return now().date()


@contextmanager
def frozen(at: datetime) -> Iterator[FrozenClock]:
    """Fix the time at `at` (timezone-aware) for the duration of the block."""
    if at.tzinfo is None:
        raise ValueError("a frozen clock needs a timezone-aware time")
    clock = FrozenClock(at.astimezone(UTC))
    token = _frozen.set(clock)
    try:
        yield clock
    finally:
        _frozen.reset(token)
