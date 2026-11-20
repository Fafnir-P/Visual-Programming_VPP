"""Field Validation (Logic / Validation). Cards that check individual field values against basic rules."""
from __future__ import annotations

import re

from ..runtime import CardError, card, coerce_value, get_field, is_blank, to_date

CATEGORY = "Logic / Validation"
GROUP = "Field Validation"


@card(
    "Check Field Is Required", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "field has value", "args": {"value": "bolt", "field": "item"}, "expect": {"value": "bolt"}},
        {"label": "numeric zero is allowed", "args": {"value": 0, "field": "qty"}, "expect": {"value": 0}},
        {"label": "false is allowed", "args": {"value": False, "field": "flag"}, "expect": {"value": False}},
    ],
    invalid=[
        {"label": "empty text fails", "args": {"value": "", "field": "name"}, "code": "required"},
        {"label": "whitespace fails", "args": {"value": "  ", "field": "name"}, "code": "required"},
        {"label": "none fails", "args": {"value": None, "field": "name"}, "code": "required"},
    ],
)
def check_field_is_required(ctx, *, value, field: str = "value") -> dict:
    """Stops the user if a mandatory field is left empty before saving or submitting."""
    if is_blank(value):
        raise CardError("required", f"{field} is required.", {"field": field})
    return {"value": value}


@card(
    "Validate Field Type", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "text is accepted", "args": {"value": "hello", "field_type": "text"}, "expect": {"value": "hello"}},
        {"label": "number is accepted", "args": {"value": 42, "field_type": "number"}, "expect": {"value": 42}},
        {"label": "date string is accepted", "args": {"value": "2026-01-31", "field_type": "date"}, "expect": {"value": "2026-01-31"}},
        {"label": "integer is accepted", "args": {"value": 5, "field_type": "integer"}, "expect": {"value": 5}},
    ],
    invalid=[
        {"label": "text when number expected", "args": {"value": "hello", "field_type": "number"}, "code": "not_a_number"},
        {"label": "text when date expected", "args": {"value": "not-a-date", "field_type": "date"}, "code": "not_a_date"},
    ],
)
def validate_field_type(ctx, *, value, field: str = "value", field_type: str = "text") -> dict:
    """Confirms a field contains the correct data type such as number, text, or date."""
    spec = {"type": field_type, "required": False}
    clean = coerce_value(spec, value, field)
    return {"value": clean}


@card(
    "Match Format Pattern", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "email matches", "args": {"value": "user@example.com", "format_type": "email"}, "expect": {"value": "user@example.com"}},
        {"label": "phone matches", "args": {"value": "+1-555-1234", "format_type": "phone"}, "expect": {"value": "+1-555-1234"}},
        {"label": "custom pattern matches", "args": {"value": "ABC-123", "format_type": "custom", "pattern": r"^[A-Z]{3}-\d{3}$"}, "expect": {"value": "ABC-123"}},
    ],
    invalid=[
        {"label": "bad email format", "args": {"value": "not-email", "format_type": "email"}, "code": "bad_format"},
        {"label": "bad phone format", "args": {"value": "abc", "format_type": "phone"}, "code": "bad_format"},
        {"label": "custom pattern fails", "args": {"value": "ABC-12", "format_type": "custom", "pattern": r"^[A-Z]{3}-\d{3}$"}, "code": "bad_format"},
    ],
)
def match_format_pattern(ctx, *, value, field: str = "value", format_type: str = "email", pattern: str = "") -> dict:
    """Checks a field against a pattern like email address, phone number, or code format."""
    if format_type == "email":
        spec = {"type": "email", "required": True}
    elif format_type == "phone":
        spec = {"type": "phone", "required": True}
    elif format_type == "custom":
        spec = {"type": "text", "required": True, "pattern": pattern}
    else:
        raise CardError("invalid_input", f"Unknown format type: {format_type}.")
    
    clean = coerce_value(spec, value, field)
    return {"value": clean}


@card(
    "Validate Number Range", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "number in range", "args": {"value": 5, "min": 1, "max": 10}, "expect": {"value": 5}},
        {"label": "at minimum", "args": {"value": 1, "min": 1, "max": 10}, "expect": {"value": 1}},
        {"label": "at maximum", "args": {"value": 10, "min": 1, "max": 10}, "expect": {"value": 10}},
        {"label": "no max set", "args": {"value": 100, "min": 1}, "expect": {"value": 100}},
    ],
    invalid=[
        {"label": "below minimum", "args": {"value": 0, "min": 1, "max": 10}, "code": "too_small"},
        {"label": "above maximum", "args": {"value": 11, "min": 1, "max": 10}, "code": "too_large"},
    ],
)
def validate_number_range(ctx, *, value, field: str = "value", min: float | None = None, max: float | None = None) -> dict:
    """Ensures a numeric field falls between a minimum and maximum value."""
    spec = {"type": "number", "required": True, "min": min, "max": max}
    clean = coerce_value(spec, value, field)
    return {"value": clean}


@card(
    "Check Text Length", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "length in range", "args": {"value": "hello", "min_length": 3, "max_length": 10}, "expect": {"value": "hello"}},
        {"label": "at minimum length", "args": {"value": "hi", "min_length": 2}, "expect": {"value": "hi"}},
        {"label": "at maximum length", "args": {"value": "hello", "max_length": 5}, "expect": {"value": "hello"}},
    ],
    invalid=[
        {"label": "too short", "args": {"value": "a", "min_length": 3}, "code": "too_short"},
        {"label": "too long", "args": {"value": "too long text", "max_length": 5}, "code": "too_long"},
    ],
)
def check_text_length(ctx, *, value, field: str = "value", min_length: int | None = None, max_length: int | None = None) -> dict:
    """Verifies a text field meets minimum or maximum character count limits."""
    spec = {"type": "text", "required": True, "min_length": min_length, "max_length": max_length}
    clean = coerce_value(spec, value, field)
    return {"value": clean}


@card(
    "Validate Against Allowed List", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "value in list", "args": {"value": "shipped", "allowed": ["pending", "shipped", "delivered"]}, "expect": {"value": "shipped"}},
        {"label": "case insensitive match", "args": {"value": "SHIPPED", "allowed": ["pending", "shipped", "delivered"]}, "expect": {"value": "shipped"}},
        {"label": "numeric value in list", "args": {"value": 2, "allowed": [1, 2, 3]}, "expect": {"value": 2}},
    ],
    invalid=[
        {"label": "value not in list", "args": {"value": "cancelled", "allowed": ["pending", "shipped", "delivered"]}, "code": "not_allowed"},
        {"label": "empty list rejects", "args": {"value": "anything", "allowed": []}, "code": "not_allowed"},
    ],
)
def validate_against_allowed_list(ctx, *, value, field: str = "value", allowed: list = None) -> dict:
    """Confirms a field value exists in a predefined list of acceptable options."""
    if allowed is None:
        allowed = []
    spec = {"type": "choice", "required": True, "choices": allowed}
    clean = coerce_value(spec, value, field)
    return {"value": clean}


@card(
    "Reject Future Date", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "past date is allowed", "args": {"value": "2026-01-01", "field": "date"}, "expect": {"value": "2026-01-01"}},
        {"label": "today is allowed", "args": {"value": "2026-01-15", "field": "date"}, "expect": {"value": "2026-01-15"}},
    ],
    invalid=[
        {"label": "future date is rejected", "args": {"value": "2026-01-20", "field": "date"}, "code": "too_large"},
        {"label": "far future date is rejected", "args": {"value": "2027-01-01", "field": "date"}, "code": "too_large"},
    ],
)
def reject_future_date(ctx, *, value, field: str = "date") -> dict:
    """Prevents a date field from being set to a date beyond today."""
    date_value = to_date(value, field)
    today = ctx.today()
    if date_value > today:
        raise CardError("too_large", f"{field} cannot be in the future.", {"field": field})
    return {"value": date_value.isoformat()}
