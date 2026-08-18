"""Age arithmetic, anchored to Sri Lanka's local date.

Everything here uses Asia/Colombo rather than date.today(). The server runs UTC, which is 5h30m
behind Colombo, so for five and a half hours of every day "today" in UTC is yesterday locally:
a date of birth a user legitimately enters as today would look like a future date, and someone's
age would tick over a day late. Both matter here, because age decides whether a guardian's
consent is required and whether a talent may be offered paid work.

`years_ago` and `calculate_age` are two views of the same question and live together on purpose:
the search filters compare against the raw date_of_birth column (so Postgres can use an index),
while the gates need an integer. Keeping them side by side keeps their leap-year handling
consistent -- see test_age.py, which pins them together at the boundaries.
"""
from datetime import date
from zoneinfo import ZoneInfo

COLOMBO = ZoneInfo("Asia/Colombo")


def today_lk() -> date:
    """Today's date in Sri Lanka."""
    from datetime import datetime

    return datetime.now(COLOMBO).date()


def calculate_age(date_of_birth: date, *, on: date | None = None) -> int:
    """Completed years since date_of_birth. Negative for a future date."""
    reference = on or today_lk()
    years = reference.year - date_of_birth.year
    # Subtract one if this year's birthday hasn't happened yet.
    if (reference.month, reference.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


def years_ago(n: int, *, on: date | None = None) -> date:
    """The date exactly n years before today, for comparing against date_of_birth in SQL.

    Someone is at least n years old iff date_of_birth <= years_ago(n).
    """
    reference = on or today_lk()
    try:
        return reference.replace(year=reference.year - n)
    except ValueError:
        # Feb 29 targeting a non-leap year -- fall back to Feb 28.
        return reference.replace(year=reference.year - n, day=28)
