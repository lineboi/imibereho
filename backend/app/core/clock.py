"""Time for the tracker (contract §11.10): one injectable clock and Kigali calendar months.

Rwanda keeps UTC+2 all year (no daylight saving), so a fixed offset is exact; SQL uses the IANA
name `Africa/Kigali` (`KIGALI_TZ_NAME`), which is the same offset. Every service takes "now" from
`get_clock`, so tests replace one dependency instead of patching `datetime`.
"""

import calendar
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Final

KIGALI: Final = timezone(timedelta(hours=2), "CAT")
KIGALI_TZ_NAME: Final = "Africa/Kigali"

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_clock() -> Clock:
    """FastAPI dependency: the clock. Tests override it with a fixed time."""
    return utc_now


@dataclass(frozen=True, slots=True)
class Month:
    """A calendar month in Kigali time."""

    year: int
    month: int

    @classmethod
    def parse(cls, value: str) -> "Month":
        """`YYYY-MM`, already format-checked by the schema."""
        year, month = value.split("-")
        return cls(int(year), int(month))

    @classmethod
    def of(cls, moment: datetime) -> "Month":
        local = moment.astimezone(KIGALI)
        return cls(local.year, local.month)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def days(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def start(self) -> datetime:
        """The first instant of the month, in Kigali time (comparable with any aware time)."""
        return datetime(self.year, self.month, 1, tzinfo=KIGALI)

    @property
    def end(self) -> datetime:
        """The first instant after the month (exclusive bound)."""
        if self.month == 12:
            return datetime(self.year + 1, 1, 1, tzinfo=KIGALI)
        return datetime(self.year, self.month + 1, 1, tzinfo=KIGALI)

    def contains(self, day: date) -> bool:
        return (day.year, day.month) == (self.year, self.month)

    def elapsed_days(self, now: datetime) -> int:
        """Days of the month that have started by `now`: all of a past month, 0 for a future one."""
        current = Month.of(now)
        if (self.year, self.month) < (current.year, current.month):
            return self.days
        if (self.year, self.month) > (current.year, current.month):
            return 0
        return now.astimezone(KIGALI).day


def day_window(day: date) -> tuple[datetime, datetime]:
    """A Kigali calendar day as [start, end)."""
    start = datetime(day.year, day.month, day.day, tzinfo=KIGALI)
    return start, start + timedelta(days=1)
