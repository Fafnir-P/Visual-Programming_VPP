"""Conditional Routing (Backend Processing). Routes records to different outputs based on field values or conditions."""
from __future__ import annotations

from ..runtime import CardError, card, get_field, is_blank, to_date, to_number, try_number

CATEGORY = "Backend Processing"
GROUP = "Conditional Routing"


@card(
    "Route By Status Value", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["pending", "shipped", "delivered", "no_match"],
    role="route",
    examples=[
        {"label": "shipped status routes to shipped port",
         "args": {"record": {"id": 1, "status": "shipped"}, "field": "status",
                  "routes": {"pending": "pending", "shipped": "shipped", "delivered": "delivered"}},
         "expect": {"route": "shipped", "value": {"id": 1, "status": "shipped"}}},
        {"label": "unknown status goes to no_match",
         "args": {"record": {"id": 2, "status": "cancelled"}, "field": "status",
                  "routes": {"pending": "pending", "shipped": "shipped"}},
         "expect": {"route": "no_match", "value": {"id": 2, "status": "cancelled"}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "text", "field": "status", "routes": {}}, "code": "invalid_input"},
        {"label": "routes must be a dict", "args": {"record": {"status": "ok"}, "field": "status", "routes": []}, "code": "invalid_input"},
    ],
)
def route_by_status_value(ctx, *, record, field: str = "status", routes: dict | None = None) -> dict:
    """Sends a record to the output for its status value; records with any other status go to a no-match output."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Status Value needs a record.")
    if routes is None:
        routes = {}
    if not isinstance(routes, dict):
        raise CardError("invalid_input", "Routes must be a mapping of values to port names.")
    
    value = get_field(record, field)
    value_str = str(value).strip() if value is not None else ""
    
    for status_val, port in routes.items():
        if str(status_val).strip().casefold() == value_str.casefold():
            return {"route": port, "value": record}
    
    return {"route": "no_match", "value": record}


@card(
    "Route By Numeric Range", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["low", "medium", "high", "no_match"],
    role="route",
    examples=[
        {"label": "value in first range routes to that port",
         "args": {"record": {"qty": 5}, "field": "qty",
                  "ranges": [{"min": 0, "max": 10, "port": "low"}, {"min": 11, "max": 50, "port": "medium"}]},
         "expect": {"route": "low", "value": {"qty": 5}}},
        {"label": "value outside all ranges goes to no_match",
         "args": {"record": {"qty": 100}, "field": "qty",
                  "ranges": [{"min": 0, "max": 10, "port": "low"}, {"min": 11, "max": 50, "port": "medium"}]},
         "expect": {"route": "no_match", "value": {"qty": 100}}},
        {"label": "boundary value included",
         "args": {"record": {"qty": 10}, "field": "qty", "ranges": [{"min": 0, "max": 10, "port": "low"}]},
         "expect": {"route": "low", "value": {"qty": 10}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": 5, "field": "qty", "ranges": []}, "code": "invalid_input"},
        {"label": "ranges must be a list", "args": {"record": {"qty": 5}, "field": "qty", "ranges": "text"}, "code": "invalid_input"},
    ],
)
def route_by_numeric_range(ctx, *, record, field: str = "value", ranges: list | None = None) -> dict:
    """Sends a record to the output whose number range it falls in; records outside every range go to a no-match output."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Numeric Range needs a record.")
    if ranges is None:
        ranges = []
    if not isinstance(ranges, list):
        raise CardError("invalid_input", "Ranges must be a list of range definitions.")
    
    value = get_field(record, field)
    num = try_number(value)
    
    if num is not None:
        for rng in ranges:
            if not isinstance(rng, dict):
                continue
            min_val = rng.get("min")
            max_val = rng.get("max")
            port = rng.get("port", "no_match")
            
            if min_val is not None:
                min_num = try_number(min_val)
                if min_num is not None and num < min_num:
                    continue
            if max_val is not None:
                max_num = try_number(max_val)
                if max_num is not None and num > max_num:
                    continue
            
            return {"route": port, "value": record}
    
    return {"route": "no_match", "value": record}


@card(
    "Route By Text Match", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["match", "no_match"],
    role="route",
    examples=[
        {"label": "matching text routes to match port",
         "args": {"record": {"name": "Bolt"}, "field": "name", "match_value": "bolt", "match_port": "match"},
         "expect": {"route": "match", "value": {"name": "Bolt"}}},
        {"label": "non-matching text goes to no_match",
         "args": {"record": {"name": "Screw"}, "field": "name", "match_value": "bolt", "match_port": "match"},
         "expect": {"route": "no_match", "value": {"name": "Screw"}}},
        {"label": "blank field goes to no_match",
         "args": {"record": {"name": ""}, "field": "name", "match_value": "bolt", "match_port": "match"},
         "expect": {"route": "no_match", "value": {"name": ""}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "text", "field": "name", "match_value": "x", "match_port": "m"}, "code": "invalid_input"},
        {"label": "match_port required", "args": {"record": {"name": "x"}, "field": "name", "match_value": "x", "match_port": ""}, "code": "invalid_input"},
    ],
)
def route_by_text_match(ctx, *, record, field: str = "value", match_value: str = "", match_port: str = "match") -> dict:
    """Sends a record to an output when a text field matches a chosen value; other records go to a no-match output."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Text Match needs a record.")
    if not match_port or not isinstance(match_port, str):
        raise CardError("invalid_input", "Match port name is required.")
    
    value = get_field(record, field)
    value_str = str(value).strip().casefold() if value is not None else ""
    match_str = str(match_value).strip().casefold()
    
    if value_str == match_str:
        return {"route": match_port, "value": record}
    
    return {"route": "no_match", "value": record}


@card(
    "Route By Field Presence", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["has_value", "is_empty"],
    role="route",
    examples=[
        {"label": "field with value routes to has_value",
         "args": {"record": {"note": "Called supplier"}, "field": "note"},
         "expect": {"route": "has_value", "value": {"note": "Called supplier"}}},
        {"label": "empty field routes to is_empty",
         "args": {"record": {"note": "  "}, "field": "note"},
         "expect": {"route": "is_empty", "value": {"note": "  "}}},
        {"label": "missing field routes to is_empty",
         "args": {"record": {}, "field": "note"},
         "expect": {"route": "is_empty", "value": {}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": [], "field": "note"}, "code": "invalid_input"},
        {"label": "field name required", "args": {"record": {"note": "x"}, "field": ""}, "code": "invalid_input"},
    ],
)
def route_by_field_presence(ctx, *, record, field: str = "value") -> dict:
    """Sends a record one way if a field has a value and another way if it is empty."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Field Presence needs a record.")
    if not field:
        raise CardError("invalid_input", "Field name is required.")
    
    value = get_field(record, field)
    
    if is_blank(value):
        return {"route": "is_empty", "value": record}
    
    return {"route": "has_value", "value": record}


@card(
    "Route By Date Comparison", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["past", "today", "future"],
    role="route",
    examples=[
        {"label": "past date routes to past",
         "args": {"record": {"due": "2026-01-10"}, "field": "due"},
         "expect": {"route": "past", "value": {"due": "2026-01-10"}}},
        {"label": "today routes to today",
         "args": {"record": {"due": "2026-01-15"}, "field": "due"},
         "expect": {"route": "today", "value": {"due": "2026-01-15"}}},
        {"label": "future date routes to future",
         "args": {"record": {"due": "2026-01-20"}, "field": "due"},
         "expect": {"route": "future", "value": {"due": "2026-01-20"}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "2026-01-15", "field": "due"}, "code": "invalid_input"},
        {"label": "not a date", "args": {"record": {"due": "not-a-date"}, "field": "due"}, "code": "not_a_date"},
    ],
)
def route_by_date_comparison(ctx, *, record, field: str = "date") -> dict:
    """Sends a record to an output depending on whether a date is in the past, today or in the future."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Date Comparison needs a record.")
    
    value = get_field(record, field)
    record_date = to_date(value, field)
    today = ctx.today()
    
    if record_date < today:
        return {"route": "past", "value": record}
    elif record_date > today:
        return {"route": "future", "value": record}
    else:
        return {"route": "today", "value": record}


@card(
    "Route By Category", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["hardware", "tools", "supplies", "no_match"],
    role="route",
    examples=[
        {"label": "known category routes to its port",
         "args": {"record": {"category": "hardware"}, "field": "category",
                  "categories": {"hardware": "hardware", "tools": "tools"}},
         "expect": {"route": "hardware", "value": {"category": "hardware"}}},
        {"label": "unknown category goes to no_match",
         "args": {"record": {"category": "furniture"}, "field": "category",
                  "categories": {"hardware": "hardware", "tools": "tools"}},
         "expect": {"route": "no_match", "value": {"category": "furniture"}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "hardware", "field": "category", "categories": {}}, "code": "invalid_input"},
        {"label": "categories must be a dict", "args": {"record": {"category": "x"}, "field": "category", "categories": []}, "code": "invalid_input"},
    ],
)
def route_by_category(ctx, *, record, field: str = "category", categories: dict | None = None) -> dict:
    """Sends a record to the output for its category or type; records with an unlisted category go to a no-match output."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By Category needs a record.")
    if categories is None:
        categories = {}
    if not isinstance(categories, dict):
        raise CardError("invalid_input", "Categories must be a mapping of values to port names.")
    
    value = get_field(record, field)
    value_str = str(value).strip().casefold() if value is not None else ""
    
    for cat_val, port in categories.items():
        if str(cat_val).strip().casefold() == value_str:
            return {"route": port, "value": record}
    
    return {"route": "no_match", "value": record}


@card(
    "Route By List Membership", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["in_list", "not_in_list"],
    role="route",
    examples=[
        {"label": "value in list routes to in_list",
         "args": {"record": {"code": "A12"}, "field": "code", "reference_list": ["A12", "B34", "C56"]},
         "expect": {"route": "in_list", "value": {"code": "A12"}}},
        {"label": "value not in list routes to not_in_list",
         "args": {"record": {"code": "Z99"}, "field": "code", "reference_list": ["A12", "B34"]},
         "expect": {"route": "not_in_list", "value": {"code": "Z99"}}},
        {"label": "empty list means nothing matches",
         "args": {"record": {"code": "A12"}, "field": "code", "reference_list": []},
         "expect": {"route": "not_in_list", "value": {"code": "A12"}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "A12", "field": "code", "reference_list": []}, "code": "invalid_input"},
        {"label": "reference_list must be a list", "args": {"record": {"code": "x"}, "field": "code", "reference_list": "x"}, "code": "invalid_input"},
    ],
)
def route_by_list_membership(ctx, *, record, field: str = "value", reference_list: list | None = None) -> dict:
    """Sends a record one way if a field value appears in a reference list and another way if it does not."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Route By List Membership needs a record.")
    if reference_list is None:
        reference_list = []
    if not isinstance(reference_list, list):
        raise CardError("invalid_input", "Reference list must be a list.")
    
    value = get_field(record, field)
    value_str = str(value).strip().casefold() if value is not None else ""
    
    for item in reference_list:
        if str(item).strip().casefold() == value_str:
            return {"route": "in_list", "value": record}
    
    return {"route": "not_in_list", "value": record}


@card(
    "Branch On Yes/No", category=CATEGORY, group=GROUP,
    inputs=["condition", "value"], outputs=["yes", "no"],
    role="route",
    examples=[
        {"label": "yes sends the value out of the yes port",
         "args": {"condition": True, "value": {"id": 1}},
         "expect": {"route": "yes", "value": {"id": 1}}},
        {"label": "no sends it out of the no port",
         "args": {"condition": False, "value": 7},
         "expect": {"route": "no", "value": 7}},
        {"label": "nothing to pass on: the branch is still chosen",
         "args": {"condition": True},
         "expect": {"route": "yes", "value": None}},
    ],
    invalid=[
        {"label": "a text is not a yes or no", "args": {"condition": "yes"}, "code": "invalid_input"},
        {"label": "a number is not a yes or no", "args": {"condition": 1}, "code": "invalid_input"},
    ],
)
def branch_on_yes_no(ctx, *, condition, value=None) -> dict:
    """Sends the value out of the yes port when the answer is yes and out of the no port when it is no."""
    if not isinstance(condition, bool):
        raise CardError("invalid_input", "Branch On Yes/No needs a yes or no answer.")
    return {"route": "yes" if condition else "no", "value": value}
