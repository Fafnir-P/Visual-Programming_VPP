"""Cross-Field Rules (Logic / Validation). Cards that check relationships between multiple fields."""
from __future__ import annotations

from ..runtime import CardError, card, get_field, is_blank, to_date, to_number

CATEGORY = "Logic / Validation"
GROUP = "Cross-Field Rules"


@card(
    "Compare Two Fields", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "greater than passes", "args": {"value": {"a": 10, "b": 5}, "field_a": "a", "field_b": "b", "operator": "gt"}, "expect": {"value": {"a": 10, "b": 5}}},
        {"label": "equal passes", "args": {"value": {"x": 5, "y": 5}, "field_a": "x", "field_b": "y", "operator": "eq"}, "expect": {"value": {"x": 5, "y": 5}}},
        {"label": "not equal passes", "args": {"value": {"x": 3, "y": 5}, "field_a": "x", "field_b": "y", "operator": "ne"}, "expect": {"value": {"x": 3, "y": 5}}},
        {"label": "less than or equal passes", "args": {"value": {"a": 5, "b": 5}, "field_a": "a", "field_b": "b", "operator": "lte"}, "expect": {"value": {"a": 5, "b": 5}}},
    ],
    invalid=[
        {"label": "greater than fails", "args": {"value": {"a": 3, "b": 5}, "field_a": "a", "field_b": "b", "operator": "gt"}, "code": "comparison_failed"},
        {"label": "equal fails", "args": {"value": {"x": 3, "y": 5}, "field_a": "x", "field_b": "y", "operator": "eq"}, "code": "comparison_failed"},
    ],
)
def compare_two_fields(ctx, *, value, field_a: str = "field_a", field_b: str = "field_b", operator: str = "gt") -> dict:
    """Checks whether two fields meet a condition like greater than, equal to, or not matching."""
    val_a = get_field(value, field_a)
    val_b = get_field(value, field_b)
    
    if operator in ("gt", "gte", "lt", "lte"):
        num_a = to_number(val_a, field_a)
        num_b = to_number(val_b, field_b)
        passes = (
            num_a > num_b if operator == "gt"
            else num_a >= num_b if operator == "gte"
            else num_a < num_b if operator == "lt"
            else num_a <= num_b
        )
    elif operator == "eq":
        passes = val_a == val_b
    elif operator == "ne":
        passes = val_a != val_b
    else:
        raise CardError("invalid_input", f"Unknown operator: {operator}.")
    
    if not passes:
        raise CardError("comparison_failed", f"{field_a} must be {operator} {field_b}.", {"field_a": field_a, "field_b": field_b})
    
    return {"value": value}


@card(
    "Verify Sum Equals Total", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "sum matches", "args": {"value": {"items": [{"amt": 10}, {"amt": 20}], "total": 30}, "items_field": "items", "amount_field": "amt", "total_field": "total"}, "expect": {"value": {"items": [{"amt": 10}, {"amt": 20}], "total": 30}}},
        {"label": "single item matches", "args": {"value": {"items": [{"amt": 50}], "total": 50}, "items_field": "items", "amount_field": "amt", "total_field": "total"}, "expect": {"value": {"items": [{"amt": 50}], "total": 50}}},
        {"label": "empty items zero total", "args": {"value": {"items": [], "total": 0}, "items_field": "items", "amount_field": "amt", "total_field": "total"}, "expect": {"value": {"items": [], "total": 0}}},
    ],
    invalid=[
        {"label": "sum mismatch", "args": {"value": {"items": [{"amt": 10}, {"amt": 20}], "total": 25}, "items_field": "items", "amount_field": "amt", "total_field": "total"}, "code": "sum_mismatch"},
        {"label": "total too high", "args": {"value": {"items": [{"amt": 10}], "total": 15}, "items_field": "items", "amount_field": "amt", "total_field": "total"}, "code": "sum_mismatch"},
    ],
)
def verify_sum_equals_total(ctx, *, value, items_field: str = "items", amount_field: str = "amount", total_field: str = "total") -> dict:
    """Confirms that line item amounts add up to a specified total field."""
    items = get_field(value, items_field) or []
    total = to_number(get_field(value, total_field), total_field)
    
    computed_sum = sum(to_number(get_field(item, amount_field), amount_field) for item in items)
    
    if abs(computed_sum - total) > 1e-9:
        raise CardError("sum_mismatch", f"Sum of {items_field}.{amount_field} ({computed_sum}) does not match {total_field} ({total}).")
    
    return {"value": value}


@card(
    "Require Either Or Field", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "first filled", "args": {"value": {"email": "a@b.com", "phone": ""}, "field_a": "email", "field_b": "phone"}, "expect": {"value": {"email": "a@b.com", "phone": ""}}},
        {"label": "second filled", "args": {"value": {"email": "", "phone": "555-1234"}, "field_a": "email", "field_b": "phone"}, "expect": {"value": {"email": "", "phone": "555-1234"}}},
        {"label": "both filled", "args": {"value": {"email": "a@b.com", "phone": "555-1234"}, "field_a": "email", "field_b": "phone"}, "expect": {"value": {"email": "a@b.com", "phone": "555-1234"}}},
    ],
    invalid=[
        {"label": "both empty", "args": {"value": {"email": "", "phone": ""}, "field_a": "email", "field_b": "phone"}, "code": "required"},
        {"label": "both none", "args": {"value": {"email": None, "phone": None}, "field_a": "email", "field_b": "phone"}, "code": "required"},
    ],
)
def require_either_or_field(ctx, *, value, field_a: str = "field_a", field_b: str = "field_b") -> dict:
    """Ensures at least one of two fields is filled, but not necessarily both."""
    val_a = get_field(value, field_a)
    val_b = get_field(value, field_b)
    
    if is_blank(val_a) and is_blank(val_b):
        raise CardError("required", f"At least one of {field_a} or {field_b} is required.", {"field_a": field_a, "field_b": field_b})
    
    return {"value": value}


@card(
    "Require Dependent Field", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value", "field_required"],
    examples=[
        {"label": "trigger value present and dependent filled", "args": {"value": {"type": "express", "tracking": "123"}, "trigger_field": "type", "trigger_value": "express", "dependent_field": "tracking"}, "expect": {"value": {"type": "express", "tracking": "123"}, "field_required": True}},
        {"label": "trigger value not present", "args": {"value": {"type": "standard", "tracking": ""}, "trigger_field": "type", "trigger_value": "express", "dependent_field": "tracking"}, "expect": {"value": {"type": "standard", "tracking": ""}, "field_required": False}},
        {"label": "trigger value present dependent optional", "args": {"value": {"type": "express", "tracking": ""}, "trigger_field": "type", "trigger_value": "standard", "dependent_field": "tracking"}, "expect": {"value": {"type": "express", "tracking": ""}, "field_required": False}},
    ],
    invalid=[
        {"label": "trigger value present but dependent empty", "args": {"value": {"type": "express", "tracking": ""}, "trigger_field": "type", "trigger_value": "express", "dependent_field": "tracking"}, "code": "required"},
        {"label": "trigger value present dependent none", "args": {"value": {"type": "express", "tracking": None}, "trigger_field": "type", "trigger_value": "express", "dependent_field": "tracking"}, "code": "required"},
    ],
)
def require_dependent_field(ctx, *, value, trigger_field: str = "trigger", trigger_value: str = "yes", dependent_field: str = "dependent") -> dict:
    """Makes a second field mandatory, and marks it required on screen, only when a first field has a certain value."""
    trigger = get_field(value, trigger_field)
    dependent = get_field(value, dependent_field)
    
    field_required = str(trigger).strip().casefold() == str(trigger_value).strip().casefold()
    
    if field_required and is_blank(dependent):
        raise CardError("required", f"{dependent_field} is required when {trigger_field} is {trigger_value}.", {"field": dependent_field})
    
    return {"value": value, "field_required": field_required}


@card(
    "Validate Date Order", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "start before end", "args": {"value": {"start": "2026-01-01", "end": "2026-01-10"}, "start_field": "start", "end_field": "end"}, "expect": {"value": {"start": "2026-01-01", "end": "2026-01-10"}}},
        {"label": "same date allowed", "args": {"value": {"start": "2026-01-05", "end": "2026-01-05"}, "start_field": "start", "end_field": "end", "allow_equal": True}, "expect": {"value": {"start": "2026-01-05", "end": "2026-01-05"}}},
        {"label": "order before ship", "args": {"value": {"order": "2026-01-01", "ship": "2026-01-02"}, "start_field": "order", "end_field": "ship"}, "expect": {"value": {"order": "2026-01-01", "ship": "2026-01-02"}}},
    ],
    invalid=[
        {"label": "end before start", "args": {"value": {"start": "2026-01-10", "end": "2026-01-01"}, "start_field": "start", "end_field": "end"}, "code": "date_order_invalid"},
        {"label": "same date not allowed", "args": {"value": {"start": "2026-01-05", "end": "2026-01-05"}, "start_field": "start", "end_field": "end", "allow_equal": False}, "code": "date_order_invalid"},
    ],
)
def validate_date_order(ctx, *, value, start_field: str = "start_date", end_field: str = "end_date", allow_equal: bool = True) -> dict:
    """Confirms a start date comes before an end date or ship date follows order date."""
    start = to_date(get_field(value, start_field), start_field)
    end = to_date(get_field(value, end_field), end_field)
    
    if allow_equal:
        if start > end:
            raise CardError("date_order_invalid", f"{start_field} must be on or before {end_field}.", {"start_field": start_field, "end_field": end_field})
    else:
        if start >= end:
            raise CardError("date_order_invalid", f"{start_field} must be before {end_field}.", {"start_field": start_field, "end_field": end_field})
    
    return {"value": value}
