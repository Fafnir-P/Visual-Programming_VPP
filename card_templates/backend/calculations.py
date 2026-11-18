"""Calculations (Backend Processing). Pure numeric operations on field values and lists."""
from __future__ import annotations

from ..runtime import (
    CardError, bounded, card, get_field, is_blank, matches, round_half_up,
    to_number, validate_condition,
)

CATEGORY = "Backend Processing"
GROUP = "Calculations"


@card(
    "Calculate Sum Of Field", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["sum"],
    phase="runtime", role="data",
    examples=[
        {"label": "sum of quantities",
         "args": {"records": [{"qty": 10}, {"qty": 20}, {"qty": 5}], "field": "qty"},
         "expect": {"sum": 35}},
        {"label": "empty list gives zero",
         "args": {"records": [], "field": "amount"},
         "expect": {"sum": 0}},
        {"label": "skip blank values",
         "args": {"records": [{"x": 3}, {"x": None}, {"x": 7}], "field": "x"},
         "expect": {"sum": 10}},
    ],
    invalid=[
        {"label": "not a list", "args": {"records": "text", "field": "x"}, "code": "invalid_input"},
        {"label": "non-numeric value", "args": {"records": [{"x": "abc"}], "field": "x"}, "code": "not_a_number"},
    ],
)
def calculate_sum_of_field(ctx, *, records, field: str = "value") -> dict:
    """Adds up numeric values from a specified field across all records in a list."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Sum needs a list of records.")
    total = 0
    for rec in bounded(records):
        value = get_field(rec, field)
        if not is_blank(value):
            total += to_number(value, field)
    return {"sum": total}


@card(
    "Calculate Average Value", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["average"],
    phase="runtime", role="data",
    examples=[
        {"label": "average of values",
         "args": {"records": [{"score": 80}, {"score": 90}, {"score": 85}], "field": "score"},
         "expect": {"average": 85}},
        {"label": "empty list gives zero",
         "args": {"records": [], "field": "x"},
         "expect": {"average": 0}},
        {"label": "skip blank values in average",
         "args": {"records": [{"x": 10}, {"x": None}, {"x": 20}], "field": "x"},
         "expect": {"average": 15}},
    ],
    invalid=[
        {"label": "not a list", "args": {"records": 5, "field": "x"}, "code": "invalid_input"},
    ],
)
def calculate_average_value(ctx, *, records, field: str = "value", places: int = 2) -> dict:
    """Computes the mean of numeric values from a field across a set of records."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Average needs a list of records.")
    values = []
    for rec in bounded(records):
        value = get_field(rec, field)
        if not is_blank(value):
            values.append(to_number(value, field))
    if not values:
        return {"average": 0}
    avg = sum(values) / len(values)
    return {"average": round_half_up(avg, places)}


@card(
    "Calculate Percentage Of Total", category=CATEGORY, group=GROUP,
    inputs=["value", "total"], outputs=["percentage"],
    phase="runtime", role="data",
    examples=[
        {"label": "part of whole",
         "args": {"value": 25, "total": 100},
         "expect": {"percentage": 25}},
        {"label": "rounded to places",
         "args": {"value": 1, "total": 3, "places": 2},
         "expect": {"percentage": 33.33}},
        {"label": "over hundred percent",
         "args": {"value": 150, "total": 100},
         "expect": {"percentage": 150}},
    ],
    invalid=[
        {"label": "divide by zero", "args": {"value": 10, "total": 0}, "code": "divide_by_zero"},
        {"label": "not a number", "args": {"value": "x", "total": 10}, "code": "not_a_number"},
    ],
)
def calculate_percentage_of_total(ctx, *, value, total, places: int = 2) -> dict:
    """Divides a value by a sum and expresses the result as a percentage."""
    num = to_number(value, "value")
    den = to_number(total, "total")
    if den == 0:
        raise CardError("divide_by_zero", "Cannot calculate percentage: total is zero.")
    pct = (num / den) * 100
    return {"percentage": round_half_up(pct, places)}


@card(
    "Find Minimum Value", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["minimum"],
    phase="runtime", role="data",
    examples=[
        {"label": "smallest value",
         "args": {"records": [{"price": 5}, {"price": 2}, {"price": 8}], "field": "price"},
         "expect": {"minimum": 2}},
        {"label": "single record",
         "args": {"records": [{"x": 10}], "field": "x"},
         "expect": {"minimum": 10}},
        {"label": "skip blank values",
         "args": {"records": [{"x": 5}, {"x": None}, {"x": 3}], "field": "x"},
         "expect": {"minimum": 3}},
    ],
    invalid=[
        {"label": "empty list", "args": {"records": [], "field": "x"}, "code": "invalid_input"},
        {"label": "not a list", "args": {"records": "text", "field": "x"}, "code": "invalid_input"},
    ],
)
def find_minimum_value(ctx, *, records, field: str = "value") -> dict:
    """Identifies the smallest numeric value in a field across a list of records."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Minimum needs a list of records.")
    values = []
    for rec in bounded(records):
        value = get_field(rec, field)
        if not is_blank(value):
            values.append(to_number(value, field))
    if not values:
        raise CardError("invalid_input", "Cannot find minimum: no numeric values found.")
    return {"minimum": min(values)}


@card(
    "Find Maximum Value", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["maximum"],
    phase="runtime", role="data",
    examples=[
        {"label": "largest value",
         "args": {"records": [{"temp": 22}, {"temp": 18}, {"temp": 25}], "field": "temp"},
         "expect": {"maximum": 25}},
        {"label": "single record",
         "args": {"records": [{"x": 7}], "field": "x"},
         "expect": {"maximum": 7}},
        {"label": "skip blank values",
         "args": {"records": [{"x": 10}, {"x": None}, {"x": 20}], "field": "x"},
         "expect": {"maximum": 20}},
    ],
    invalid=[
        {"label": "empty list", "args": {"records": [], "field": "x"}, "code": "invalid_input"},
        {"label": "not a list", "args": {"records": 5, "field": "x"}, "code": "invalid_input"},
    ],
)
def find_maximum_value(ctx, *, records, field: str = "value") -> dict:
    """Identifies the largest numeric value in a field across a list of records."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Maximum needs a list of records.")
    values = []
    for rec in bounded(records):
        value = get_field(rec, field)
        if not is_blank(value):
            values.append(to_number(value, field))
    if not values:
        raise CardError("invalid_input", "Cannot find maximum: no numeric values found.")
    return {"maximum": max(values)}


@card(
    "Calculate Running Total", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["records"],
    phase="runtime", role="data",
    examples=[
        {"label": "accumulate values",
         "args": {"records": [{"amount": 10}, {"amount": 5}, {"amount": 3}], "field": "amount", "output_field": "running"},
         "expect": {"records": [{"amount": 10, "running": 10}, {"amount": 5, "running": 15}, {"amount": 3, "running": 18}]}},
        {"label": "start from initial balance",
         "args": {"records": [{"delta": 2}, {"delta": -1}], "field": "delta", "output_field": "total", "initial": 10},
         "expect": {"records": [{"delta": 2, "total": 12}, {"delta": -1, "total": 11}]}},
    ],
    invalid=[
        {"label": "not a list", "args": {"records": "text", "field": "x"}, "code": "invalid_input"},
        {"label": "non-numeric value", "args": {"records": [{"x": "abc"}], "field": "x"}, "code": "not_a_number"},
    ],
)
def calculate_running_total(ctx, *, records, field: str = "value", output_field: str = "running_total", initial: float = 0) -> dict:
    """Adds each value to the sum of all previous values in sequence."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Running total needs a list of records.")
    results = []
    total = to_number(initial, "initial")
    for rec in bounded(records):
        value = get_field(rec, field)
        if not is_blank(value):
            total += to_number(value, field)
        new_rec = {**rec, output_field: total}
        results.append(new_rec)
    return {"records": results}


@card(
    "Calculate Stock Level", category=CATEGORY, group=GROUP,
    inputs=["starting", "incoming", "outgoing"], outputs=["stock"],
    phase="runtime", role="data",
    examples=[
        {"label": "positive stock",
         "args": {"starting": 100, "incoming": 50, "outgoing": 30},
         "expect": {"stock": 120}},
        {"label": "zero starting",
         "args": {"starting": 0, "incoming": 20, "outgoing": 5},
         "expect": {"stock": 15}},
        {"label": "negative result",
         "args": {"starting": 10, "incoming": 0, "outgoing": 15},
         "expect": {"stock": -5}},
    ],
    invalid=[
        {"label": "not a number", "args": {"starting": "x", "incoming": 10, "outgoing": 5}, "code": "not_a_number"},
    ],
)
def calculate_stock_level(ctx, *, starting, incoming, outgoing) -> dict:
    """Computes current inventory by subtracting outgoing quantity from incoming quantity and starting balance."""
    start = to_number(starting, "starting")
    inc = to_number(incoming, "incoming")
    out = to_number(outgoing, "outgoing")
    stock = start + inc - out
    return {"stock": stock}


@card(
    "Count Records Matching Condition", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["count"],
    phase="runtime", role="data",
    examples=[
        {"label": "count all records",
         "args": {"records": [{"x": 1}, {"x": 2}, {"x": 3}]},
         "expect": {"count": 3}},
        {"label": "count matching only",
         "args": {"records": [{"status": "ok"}, {"status": "fail"}, {"status": "ok"}],
                  "condition": {"field": "status", "op": "eq", "value": "ok"}},
         "expect": {"count": 2}},
        {"label": "empty list",
         "args": {"records": []},
         "expect": {"count": 0}},
    ],
    invalid=[
        {"label": "not a list", "args": {"records": 5}, "code": "invalid_input"},
        {"label": "bad condition", "args": {"records": [], "condition": {"op": "unknown", "value": 1}}, "code": "invalid_condition"},
    ],
)
def count_records_matching_condition(ctx, *, records, condition: dict | None = None) -> dict:
    """Counts the records in the current list, or only those that meet a condition."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Count needs a list of records.")
    if condition is None:
        return {"count": len(bounded(records))}
    validate_condition(condition)
    count = sum(1 for rec in bounded(records) if matches(rec, condition))
    return {"count": count}


@card(
    "Calculate Reorder Quantity", category=CATEGORY, group=GROUP,
    inputs=["average_use", "lead_time"], outputs=["quantity"],
    phase="runtime", role="data",
    examples=[
        {"label": "simple formula",
         "args": {"average_use": 10, "lead_time": 5, "safety_factor": 1.5},
         "expect": {"quantity": 75}},
        {"label": "no safety factor",
         "args": {"average_use": 8, "lead_time": 3, "safety_factor": 1.0},
         "expect": {"quantity": 24}},
    ],
    invalid=[
        {"label": "not a number", "args": {"average_use": "x", "lead_time": 5}, "code": "not_a_number"},
        {"label": "negative use", "args": {"average_use": -5, "lead_time": 2}, "code": "too_small"},
    ],
)
def calculate_reorder_quantity(ctx, *, average_use, lead_time, safety_factor: float = 1.2) -> dict:
    """Works out the next order amount from past usage with a plain formula, such as average use times lead time."""
    use = to_number(average_use, "average_use")
    lead = to_number(lead_time, "lead_time")
    factor = to_number(safety_factor, "safety_factor")
    if use < 0:
        raise CardError("too_small", "Average use cannot be negative.")
    if lead < 0:
        raise CardError("too_small", "Lead time cannot be negative.")
    if factor < 0:
        raise CardError("too_small", "Safety factor cannot be negative.")
    quantity = use * lead * factor
    return {"quantity": round_half_up(quantity, 0)}


@card(
    "Calculate From Two Values", category=CATEGORY, group=GROUP,
    inputs=["first", "second"], outputs=["result"],
    phase="runtime", role="data",
    examples=[
        {"label": "add two numbers",
         "args": {"first": 10, "second": 5, "operation": "add"},
         "expect": {"result": 15}},
        {"label": "subtract",
         "args": {"first": 20, "second": 8, "operation": "subtract"},
         "expect": {"result": 12}},
        {"label": "multiply",
         "args": {"first": 6, "second": 7, "operation": "multiply"},
         "expect": {"result": 42}},
        {"label": "divide",
         "args": {"first": 100, "second": 4, "operation": "divide"},
         "expect": {"result": 25}},
    ],
    invalid=[
        {"label": "divide by zero", "args": {"first": 10, "second": 0, "operation": "divide"}, "code": "divide_by_zero"},
        {"label": "unknown operation", "args": {"first": 5, "second": 3, "operation": "power"}, "code": "invalid_input"},
    ],
)
def calculate_from_two_values(ctx, *, first, second, operation: str = "add", places: int = 2) -> dict:
    """Adds, subtracts, multiplies or divides two numbers, such as stock counted minus stock on record."""
    a = to_number(first, "first")
    b = to_number(second, "second")
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise CardError("divide_by_zero", "Cannot divide by zero.")
        result = a / b
    else:
        raise CardError("invalid_input", f"Unknown operation: {operation}. Use add, subtract, multiply or divide.")
    return {"result": round_half_up(result, places)}


@card(
    "Change Value By Percent", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["result"],
    phase="runtime", role="data",
    examples=[
        {"label": "increase by percentage",
         "args": {"value": 100, "percent": 10, "direction": "increase"},
         "expect": {"result": 110}},
        {"label": "decrease by percentage",
         "args": {"value": 50, "percent": 20, "direction": "decrease"},
         "expect": {"result": 40}},
        {"label": "add tax",
         "args": {"value": 100, "percent": 7.5, "direction": "increase"},
         "expect": {"result": 107.5}},
    ],
    invalid=[
        {"label": "not a number", "args": {"value": "x", "percent": 10}, "code": "not_a_number"},
        {"label": "negative percent", "args": {"value": 100, "percent": -5}, "code": "too_small"},
    ],
)
def change_value_by_percent(ctx, *, value, percent, direction: str = "increase", places: int = 2) -> dict:
    """Raises or lowers an amount by a percentage, for example to add tax or take off a discount."""
    val = to_number(value, "value")
    pct = to_number(percent, "percent")
    if pct < 0:
        raise CardError("too_small", "Percent cannot be negative.")
    if direction not in ("increase", "decrease"):
        raise CardError("invalid_input", f"Direction must be increase or decrease, not {direction}.")
    change = val * (pct / 100)
    result = val + change if direction == "increase" else val - change
    return {"result": round_half_up(result, places)}


@card(
    "Calculate Percentage Change", category=CATEGORY, group=GROUP,
    inputs=["old_value", "new_value"], outputs=["change"],
    phase="runtime", role="data",
    examples=[
        {"label": "increase",
         "args": {"old_value": 50, "new_value": 75},
         "expect": {"change": 50}},
        {"label": "decrease",
         "args": {"old_value": 100, "new_value": 80},
         "expect": {"change": -20}},
        {"label": "no change",
         "args": {"old_value": 10, "new_value": 10},
         "expect": {"change": 0}},
    ],
    invalid=[
        {"label": "old value is zero", "args": {"old_value": 0, "new_value": 10}, "code": "divide_by_zero"},
        {"label": "not a number", "args": {"old_value": "x", "new_value": 10}, "code": "not_a_number"},
    ],
)
def calculate_percentage_change(ctx, *, old_value, new_value, places: int = 2) -> dict:
    """Shows how much a value rose or fell compared with an earlier value, as a percentage."""
    old = to_number(old_value, "old_value")
    new = to_number(new_value, "new_value")
    if old == 0:
        raise CardError("divide_by_zero", "Cannot calculate percentage change: old value is zero.")
    change = ((new - old) / old) * 100
    return {"change": round_half_up(change, places)}
