"""Date and Time Operations (Backend Processing). Calculations and comparisons on dates and times."""
from __future__ import annotations

import datetime as dt

from ..runtime import CardError, card, iso, to_date, to_datetime, to_number

CATEGORY = "Backend Processing"
GROUP = "Date and Time Operations"


def _same_shape(original, result: dt.datetime) -> str:
    """A date in gives a date out; a date and time in gives a date and time out."""
    date_only = (isinstance(original, dt.date) and not isinstance(original, dt.datetime)) or (
        isinstance(original, str) and len(original.strip()) <= 10)
    if date_only and result.time() == dt.time(0, 0):
        return result.date().isoformat()
    return iso(result)


@card(
    "Calculate Date Difference", category=CATEGORY, group=GROUP,
    inputs=["start_date", "end_date"], outputs=["difference"],
    phase="runtime", role="data",
    examples=[
        {"label": "days between dates",
         "args": {"start_date": "2026-01-01", "end_date": "2026-01-10", "unit": "days"},
         "expect": {"difference": 9}},
        {"label": "hours between datetimes",
         "args": {"start_date": "2026-01-01T10:00:00", "end_date": "2026-01-01T14:30:00", "unit": "hours"},
         "expect": {"difference": 4.5}},
        {"label": "minutes between times",
         "args": {"start_date": "2026-01-01T09:00:00", "end_date": "2026-01-01T09:45:00", "unit": "minutes"},
         "expect": {"difference": 45}},
    ],
    invalid=[
        {"label": "not a date", "args": {"start_date": "not-a-date", "end_date": "2026-01-10"}, "code": "not_a_date"},
        {"label": "unknown unit", "args": {"start_date": "2026-01-01", "end_date": "2026-01-10", "unit": "years"}, "code": "invalid_input"},
    ],
)
def calculate_date_difference(ctx, *, start_date, end_date, unit: str = "days") -> dict:
    """Computes the number of days, hours, or minutes between two dates or timestamps."""
    start = to_datetime(start_date, "start_date")
    end = to_datetime(end_date, "end_date")
    delta = end - start
    if unit == "days":
        diff = delta.days + delta.seconds / 86400
    elif unit == "hours":
        diff = delta.total_seconds() / 3600
    elif unit == "minutes":
        diff = delta.total_seconds() / 60
    elif unit == "seconds":
        diff = delta.total_seconds()
    else:
        raise CardError("invalid_input", f"Unknown unit: {unit}. Use days, hours, minutes or seconds.")
    return {"difference": round(diff, 2)}


@card(
    "Add Time To Date", category=CATEGORY, group=GROUP,
    inputs=["date"], outputs=["result"],
    phase="runtime", role="data",
    examples=[
        {"label": "add days",
         "args": {"date": "2026-01-15", "amount": 7, "unit": "days"},
         "expect": {"result": "2026-01-22"}},
        {"label": "add hours",
         "args": {"date": "2026-01-15T09:00:00", "amount": 3, "unit": "hours"},
         "expect": {"result": "2026-01-15T12:00:00"}},
        {"label": "add minutes",
         "args": {"date": "2026-01-15T09:30:00", "amount": 45, "unit": "minutes"},
         "expect": {"result": "2026-01-15T10:15:00"}},
    ],
    invalid=[
        {"label": "not a date", "args": {"date": "invalid", "amount": 5}, "code": "not_a_date"},
        {"label": "not a number", "args": {"date": "2026-01-15", "amount": "x"}, "code": "not_a_number"},
    ],
)
def add_time_to_date(ctx, *, date, amount, unit: str = "days") -> dict:
    """Advances a date forward by a specified number of days, hours, or minutes."""
    d = to_datetime(date, "date")
    amt = to_number(amount, "amount")
    if unit == "days":
        result = d + dt.timedelta(days=amt)
    elif unit == "hours":
        result = d + dt.timedelta(hours=amt)
    elif unit == "minutes":
        result = d + dt.timedelta(minutes=amt)
    elif unit == "seconds":
        result = d + dt.timedelta(seconds=amt)
    else:
        raise CardError("invalid_input", f"Unknown unit: {unit}. Use days, hours, minutes or seconds.")
    return {"result": _same_shape(date, result)}


@card(
    "Subtract Time From Date", category=CATEGORY, group=GROUP,
    inputs=["date"], outputs=["result"],
    phase="runtime", role="data",
    examples=[
        {"label": "subtract days",
         "args": {"date": "2026-01-15", "amount": 5, "unit": "days"},
         "expect": {"result": "2026-01-10"}},
        {"label": "subtract hours",
         "args": {"date": "2026-01-15T14:00:00", "amount": 2, "unit": "hours"},
         "expect": {"result": "2026-01-15T12:00:00"}},
        {"label": "subtract minutes",
         "args": {"date": "2026-01-15T10:30:00", "amount": 45, "unit": "minutes"},
         "expect": {"result": "2026-01-15T09:45:00"}},
    ],
    invalid=[
        {"label": "not a date", "args": {"date": "bad", "amount": 3}, "code": "not_a_date"},
        {"label": "not a number", "args": {"date": "2026-01-15", "amount": "text"}, "code": "not_a_number"},
    ],
)
def subtract_time_from_date(ctx, *, date, amount, unit: str = "days") -> dict:
    """Moves a date backward by a specified number of days, hours, or minutes."""
    d = to_datetime(date, "date")
    amt = to_number(amount, "amount")
    if unit == "days":
        result = d - dt.timedelta(days=amt)
    elif unit == "hours":
        result = d - dt.timedelta(hours=amt)
    elif unit == "minutes":
        result = d - dt.timedelta(minutes=amt)
    elif unit == "seconds":
        result = d - dt.timedelta(seconds=amt)
    else:
        raise CardError("invalid_input", f"Unknown unit: {unit}. Use days, hours, minutes or seconds.")
    return {"result": _same_shape(date, result)}


@card(
    "Compare Two Dates", category=CATEGORY, group=GROUP,
    inputs=["first_date", "second_date"], outputs=["comparison"],
    phase="runtime", role="data",
    examples=[
        {"label": "first is before second",
         "args": {"first_date": "2026-01-10", "second_date": "2026-01-20"},
         "expect": {"comparison": "before"}},
        {"label": "first is after second",
         "args": {"first_date": "2026-02-01", "second_date": "2026-01-15"},
         "expect": {"comparison": "after"}},
        {"label": "dates are equal",
         "args": {"first_date": "2026-01-15", "second_date": "2026-01-15"},
         "expect": {"comparison": "equal"}},
    ],
    invalid=[
        {"label": "not a date", "args": {"first_date": "bad", "second_date": "2026-01-15"}, "code": "not_a_date"},
    ],
)
def compare_two_dates(ctx, *, first_date, second_date) -> dict:
    """Determines whether one date is before, after, or equal to another date."""
    first = to_datetime(first_date, "first_date")
    second = to_datetime(second_date, "second_date")
    if first < second:
        comparison = "before"
    elif first > second:
        comparison = "after"
    else:
        comparison = "equal"
    return {"comparison": comparison}


@card(
    "Calculate Working Days", category=CATEGORY, group=GROUP,
    inputs=["start_date", "end_date"], outputs=["working_days"],
    phase="runtime", role="data",
    examples=[
        {"label": "weekdays only",
         "args": {"start_date": "2026-01-05", "end_date": "2026-01-09"},
         "expect": {"working_days": 5}},
        {"label": "span including weekend",
         "args": {"start_date": "2026-01-09", "end_date": "2026-01-12"},
         "expect": {"working_days": 2}},
        {"label": "exclude holidays",
         "args": {"start_date": "2026-01-01", "end_date": "2026-01-05", "holidays": ["2026-01-01"]},
         "expect": {"working_days": 2}},
    ],
    invalid=[
        {"label": "not a date", "args": {"start_date": "bad", "end_date": "2026-01-15"}, "code": "not_a_date"},
    ],
)
def calculate_working_days(ctx, *, start_date, end_date, holidays: list[str] | None = None) -> dict:
    """Counts weekdays between two dates, excluding weekends and optionally holidays."""
    start = to_date(start_date, "start_date")
    end = to_date(end_date, "end_date")
    if end < start:
        raise CardError("invalid_input", "end_date must be on or after start_date.")
    holiday_set = set()
    if holidays:
        for h in holidays:
            holiday_set.add(to_date(h, "holiday").isoformat())
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current.isoformat() not in holiday_set:
            count += 1
        current += dt.timedelta(days=1)
    return {"working_days": count}


@card(
    "Get Current Date And Time", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["date", "time", "datetime"],
    phase="runtime", role="data",
    examples=[
        {"label": "returns fixed time in examples",
         "args": {},
         "expect": {"date": "2026-01-15", "time": "09:30:00", "datetime": "2026-01-15T09:30:00"},
         "now": "2026-01-15T09:30:00"},
        {"label": "custom now time",
         "args": {},
         "expect": {"date": "2026-02-20", "datetime": "2026-02-20T14:45:00"},
         "now": "2026-02-20T14:45:00"},
    ],
    invalid=[],
)
def get_current_date_and_time(ctx) -> dict:
    """Returns the date and time as the app clock says it is now."""
    now = ctx.now()
    return {
        "date": now.date().isoformat(),
        "time": now.time().replace(microsecond=0).isoformat(),
        "datetime": iso(now),
    }
