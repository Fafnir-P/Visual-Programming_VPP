"""List Operations (Backend Processing). Cards that filter, sort, group, and transform lists of records."""
from __future__ import annotations

from ..runtime import (
    CardError,
    bounded,
    card,
    compile_condition,
    get_field,
    is_blank,
    matches,
    to_date,
    to_number,
    try_number,
    validate_condition,
)

CATEGORY = "Backend Processing"
GROUP = "List Operations"


@card(
    "Filter Records By Condition",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records"],
    examples=[
        {
            "label": "keeps matching records",
            "args": {
                "records": [{"status": "shipped"}, {"status": "pending"}],
                "condition": {"field": "status", "op": "eq", "value": "shipped"},
            },
            "expect": {"records": [{"status": "shipped"}]},
        },
        {
            "label": "empty list when nothing matches",
            "args": {
                "records": [{"qty": 5}, {"qty": 10}],
                "condition": {"field": "qty", "op": "gt", "value": 20},
            },
            "expect": {"records": []},
        },
    ],
    invalid=[
        {
            "label": "bad condition structure",
            "args": {"records": [], "condition": {"op": "eq"}},
            "code": "invalid_condition",
        },
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "condition": {"field": "status", "op": "eq", "value": "shipped"}},
            "code": "invalid_input",
        },
    ],
)
def filter_records_by_condition(ctx, *, records, condition: dict) -> dict:
    """Keeps only the records in the current list that meet one or more conditions and drops the rest."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    validate_condition(condition)
    records_list = bounded(records, what="records")
    filtered = [rec for rec in records_list if isinstance(rec, dict) and matches(rec, condition)]
    return {"records": filtered}


@card(
    "Sort Records By Field",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records"],
    examples=[
        {
            "label": "sorts ascending by one field",
            "args": {"records": [{"name": "bolt"}, {"name": "axle"}], "fields": ["name"]},
            "expect": {"records": [{"name": "axle"}, {"name": "bolt"}]},
        },
        {
            "label": "sorts descending",
            "args": {
                "records": [{"qty": 5}, {"qty": 10}, {"qty": 2}],
                "fields": ["qty"],
                "descending": True,
            },
            "expect": {"records": [{"qty": 10}, {"qty": 5}, {"qty": 2}]},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "fields": ["name"]},
            "code": "invalid_input",
        },
        {
            "label": "fields must be provided",
            "args": {"records": [], "fields": []},
            "code": "missing_field",
        },
    ],
)
def sort_records_by_field(ctx, *, records, fields: list[str], descending: bool = False) -> dict:
    """Arranges the records in the current list in ascending or descending order of one or more fields."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not fields:
        raise CardError("missing_field", "At least one field is required for sorting.")
    records_list = bounded(records, what="records")

    def sort_key(rec: dict) -> tuple:
        # Each field gives (blank-flag, kind, value): blanks always come last, numbers before text,
        # so numbers and text can sit in the same column without a crash.
        values = []
        for field in fields:
            val = get_field(rec, field)
            blank = val is None or (isinstance(val, str) and not val.strip())
            flag = (0 if blank else 1) if descending else (1 if blank else 0)   # reverse=True flips the order
            if blank:
                values.append((flag, 0, 0))
                continue
            num = try_number(val) if not isinstance(val, bool) else None
            if num is not None:
                values.append((flag, 0, num))
            else:
                values.append((flag, 1, str(val).strip().casefold()))
        return tuple(values)

    sorted_records = sorted(records_list, key=sort_key, reverse=descending)
    return {"records": sorted_records}


@card(
    "Group Records By Value",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["groups"],
    examples=[
        {
            "label": "groups by a field",
            "args": {
                "records": [{"status": "shipped", "id": 1}, {"status": "pending", "id": 2}, {"status": "shipped", "id": 3}],
                "field": "status",
            },
            "expect": {
                "groups": [
                    {"key": "shipped", "records": [{"status": "shipped", "id": 1}, {"status": "shipped", "id": 3}]},
                    {"key": "pending", "records": [{"status": "pending", "id": 2}]},
                ]
            },
        },
        {
            "label": "empty list produces empty groups",
            "args": {"records": [], "field": "status"},
            "expect": {"groups": []},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "field": "status"},
            "code": "invalid_input",
        },
        {
            "label": "field must be provided",
            "args": {"records": [], "field": ""},
            "code": "missing_field",
        },
    ],
)
def group_records_by_value(ctx, *, records, field: str) -> dict:
    """Organizes records into named groups based on a shared field value or category."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not field:
        raise CardError("missing_field", "A field name is required for grouping.")
    records_list = bounded(records, what="records")

    groups_dict: dict = {}
    for rec in records_list:
        if not isinstance(rec, dict):
            continue
        value = get_field(rec, field)
        key = str(value) if value is not None else ""
        if key not in groups_dict:
            groups_dict[key] = []
        groups_dict[key].append(rec)

    groups = [{"key": key, "records": recs} for key, recs in groups_dict.items()]
    return {"groups": groups}


@card(
    "Remove Duplicate Records",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records"],
    examples=[
        {
            "label": "removes duplicates based on fields",
            "args": {
                "records": [{"name": "bolt", "qty": 5}, {"name": "bolt", "qty": 10}, {"name": "axle", "qty": 5}],
                "fields": ["name"],
            },
            "expect": {"records": [{"name": "bolt", "qty": 5}, {"name": "axle", "qty": 5}]},
        },
        {
            "label": "no duplicates returns same list",
            "args": {"records": [{"id": 1}, {"id": 2}], "fields": ["id"]},
            "expect": {"records": [{"id": 1}, {"id": 2}]},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "fields": ["name"]},
            "code": "invalid_input",
        },
        {
            "label": "fields must be provided",
            "args": {"records": [], "fields": []},
            "code": "missing_field",
        },
    ],
)
def remove_duplicate_records(ctx, *, records, fields: list[str]) -> dict:
    """Identifies and removes records with matching values in specified fields from the list."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not fields:
        raise CardError("missing_field", "At least one field is required to detect duplicates.")
    records_list = bounded(records, what="records")

    seen = set()
    unique = []
    for rec in records_list:
        if not isinstance(rec, dict):
            continue
        key = tuple(get_field(rec, field) for field in fields)
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return {"records": unique}


@card(
    "Paginate Record List",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records", "total", "page", "page_size", "total_pages"],
    examples=[
        {
            "label": "returns first page",
            "args": {"records": [{"id": i} for i in range(1, 11)], "page": 1, "page_size": 3},
            "expect": {"records": [{"id": 1}, {"id": 2}, {"id": 3}], "total": 10, "page": 1, "page_size": 3, "total_pages": 4},
        },
        {
            "label": "returns last page with fewer items",
            "args": {"records": [{"id": i} for i in range(1, 6)], "page": 2, "page_size": 3},
            "expect": {"records": [{"id": 4}, {"id": 5}], "total": 5, "page": 2, "page_size": 3, "total_pages": 2},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "page": 1, "page_size": 10},
            "code": "invalid_input",
        },
        {
            "label": "page must be positive",
            "args": {"records": [], "page": 0, "page_size": 10},
            "code": "invalid_input",
        },
    ],
)
def paginate_record_list(ctx, *, records, page: int = 1, page_size: int = 10) -> dict:
    """Splits a list into fixed-size pages and returns one page at a time."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if page < 1:
        raise CardError("invalid_input", "Page number must be at least 1.")
    if page_size < 1:
        raise CardError("invalid_input", "Page size must be at least 1.")
    records_list = bounded(records, what="records")

    total = len(records_list)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    page_records = records_list[start:end]

    return {
        "records": page_records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@card(
    "Take Record Range",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records"],
    examples=[
        {
            "label": "takes a range from the list",
            "args": {"records": [{"id": i} for i in range(1, 11)], "start": 2, "end": 5},
            "expect": {"records": [{"id": 3}, {"id": 4}, {"id": 5}]},
        },
        {
            "label": "end beyond list returns remaining items",
            "args": {"records": [{"id": 1}, {"id": 2}], "start": 1, "end": 10},
            "expect": {"records": [{"id": 2}]},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "start": 0, "end": 5},
            "code": "invalid_input",
        },
        {
            "label": "start must be non-negative",
            "args": {"records": [], "start": -1, "end": 5},
            "code": "invalid_input",
        },
    ],
)
def take_record_range(ctx, *, records, start: int = 0, end: int = 10) -> dict:
    """Returns part of a list of records, from the start position up to (not including) the end position."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if start < 0:
        raise CardError("invalid_input", "Start position must be at least 0.")
    if end < start:
        raise CardError("invalid_input", "End position must be at least the start position.")
    records_list = bounded(records, what="records")
    return {"records": records_list[start:end]}


@card(
    "Find First Matching Record",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["record", "found"],
    examples=[
        {
            "label": "finds first matching record",
            "args": {
                "records": [{"status": "pending"}, {"status": "shipped"}, {"status": "shipped"}],
                "condition": {"field": "status", "op": "eq", "value": "shipped"},
            },
            "expect": {"record": {"status": "shipped"}, "found": True},
        },
        {
            "label": "returns not found when no match",
            "args": {
                "records": [{"status": "pending"}],
                "condition": {"field": "status", "op": "eq", "value": "shipped"},
            },
            "expect": {"record": None, "found": False},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "condition": {"field": "status", "op": "eq", "value": "shipped"}},
            "code": "invalid_input",
        },
        {
            "label": "condition must be valid",
            "args": {"records": [], "condition": {"field": ""}},
            "code": "invalid_condition",
        },
    ],
)
def find_first_matching_record(ctx, *, records, condition: dict) -> dict:
    """Searches a list and returns the first record that meets the specified condition."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    validate_condition(condition)
    records_list = bounded(records, what="records")

    for rec in records_list:
        if isinstance(rec, dict) and matches(rec, condition):
            return {"record": rec, "found": True}
    return {"record": None, "found": False}


@card(
    "Flag Unusual Records",
    category=CATEGORY,
    group=GROUP,
    inputs=["records"],
    outputs=["records"],
    examples=[
        {
            "label": "flags records outside range",
            "args": {
                "records": [{"qty": 5}, {"qty": 50}, {"qty": 10}],
                "field": "qty",
                "min": 4,
                "max": 20,
                "flag_field": "unusual",
            },
            "expect": {
                "records": [
                    {"qty": 5, "unusual": False},
                    {"qty": 50, "unusual": True},
                    {"qty": 10, "unusual": False},
                ]
            },
        },
        {
            "label": "all normal when in range",
            "args": {"records": [{"qty": 5}, {"qty": 10}], "field": "qty", "min": 0, "max": 100},
            "expect": {"records": [{"qty": 5, "unusual": False}, {"qty": 10, "unusual": False}]},
        },
    ],
    invalid=[
        {
            "label": "records must be a list",
            "args": {"records": "not a list", "field": "qty"},
            "code": "invalid_input",
        },
        {
            "label": "field must be provided",
            "args": {"records": [], "field": ""},
            "code": "missing_field",
        },
    ],
)
def flag_unusual_records(ctx, *, records, field: str, min: float | None = None, max: float | None = None, flag_field: str = "unusual") -> dict:
    """Marks records whose value falls outside a normal range the builder sets, such as far above the average."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not field:
        raise CardError("missing_field", "A field name is required for checking unusual values.")
    records_list = bounded(records, what="records")

    flagged = []
    for rec in records_list:
        if not isinstance(rec, dict):
            flagged.append(rec)
            continue
        new_rec = rec.copy()
        value = get_field(rec, field)
        unusual = False
        try:
            num = to_number(value, field)
            if min is not None and num < min:
                unusual = True
            if max is not None and num > max:
                unusual = True
        except CardError:
            unusual = True
        new_rec[flag_field] = unusual
        flagged.append(new_rec)
    return {"records": flagged}


@card(
    "Merge Two Lists",
    category=CATEGORY,
    group=GROUP,
    inputs=["list_a", "list_b"],
    outputs=["records"],
    examples=[
        {
            "label": "combines two lists",
            "args": {"list_a": [{"id": 1}], "list_b": [{"id": 2}]},
            "expect": {"records": [{"id": 1}, {"id": 2}]},
        },
        {
            "label": "removes duplicates when requested",
            "args": {
                "list_a": [{"name": "bolt"}, {"name": "axle"}],
                "list_b": [{"name": "bolt"}, {"name": "nut"}],
                "remove_duplicates": True,
                "unique_fields": ["name"],
            },
            "expect": {"records": [{"name": "bolt"}, {"name": "axle"}, {"name": "nut"}]},
        },
    ],
    invalid=[
        {
            "label": "list_a must be a list",
            "args": {"list_a": "not a list", "list_b": []},
            "code": "invalid_input",
        },
        {
            "label": "list_b must be a list",
            "args": {"list_a": [], "list_b": "not a list"},
            "code": "invalid_input",
        },
    ],
)
def merge_two_lists(ctx, *, list_a, list_b, remove_duplicates: bool = False, unique_fields: list[str] | None = None) -> dict:
    """Combines two lists of records into one list, optionally dropping repeated records."""
    if not isinstance(list_a, list):
        raise CardError("invalid_input", "First list must be a list.")
    if not isinstance(list_b, list):
        raise CardError("invalid_input", "Second list must be a list.")

    combined = bounded(list_a + list_b, what="records")

    if not remove_duplicates:
        return {"records": combined}

    if not unique_fields:
        unique_fields = []

    seen = set()
    unique = []
    for rec in combined:
        if not isinstance(rec, dict):
            unique.append(rec)
            continue
        if unique_fields:
            key = tuple(get_field(rec, field) for field in unique_fields)
        else:
            key = tuple(sorted(rec.items()))
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return {"records": unique}


@card(
    "Pick Field From Records",
    category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["values"],
    examples=[
        {"label": "ids of a list of records",
         "args": {"records": [{"id": 3, "n": "a"}, {"id": 5, "n": "b"}], "field": "id"},
         "expect": {"values": [3, 5]}},
        {"label": "blank values are left out",
         "args": {"records": [{"sku": "A"}, {"sku": ""}, {"sku": None}, {}, {"sku": "B"}], "field": "sku"},
         "expect": {"values": ["A", "B"]}},
        {"label": "blank values kept on request",
         "args": {"records": [{"sku": "A"}, {}], "field": "sku", "skip_blank": False},
         "expect": {"values": ["A", None]}},
        {"label": "repeats removed on request, first one kept",
         "args": {"records": [{"c": "x"}, {"c": "y"}, {"c": "x"}], "field": "c", "unique": True},
         "expect": {"values": ["x", "y"]}},
        {"label": "empty list",
         "args": {"records": [], "field": "id"},
         "expect": {"values": []}},
    ],
    invalid=[
        {"label": "records must be a list", "args": {"records": {"id": 1}, "field": "id"}, "code": "invalid_input"},
        {"label": "a field name is needed", "args": {"records": [], "field": ""}, "code": "invalid_input"},
    ],
)
def pick_field_from_records(ctx, *, records, field: str, skip_blank: bool = True, unique: bool = False) -> dict:
    """Takes one named field out of every record and gives the values as a list, for example the ids of a list of records."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not isinstance(field, str) or not field.strip():
        raise CardError("invalid_input", "Say which field to take.")
    out = []
    for rec in bounded(records, what="records"):
        value = get_field(rec, field) if isinstance(rec, dict) else None
        if skip_blank and is_blank(value):
            continue
        if unique and value in out:
            continue
        out.append(value)
    return {"values": out}


_DATE_OPERATORS = ("before", "after", "on", "on_or_before", "on_or_after")


@card(
    "Filter Records By Date",
    category=CATEGORY, group=GROUP,
    inputs=["records", "compare_date"], outputs=["records"],
    examples=[
        {"label": "records due before today (overdue)",
         "args": {"records": [{"id": 1, "due": "2026-01-10"}, {"id": 2, "due": "2026-01-20"}, {"id": 3, "due": "2026-01-15"}],
                  "compare_date": "2026-01-15", "field": "due", "operator": "before"},
         "expect": {"records": [{"id": 1}]}},
        {"label": "on or after",
         "args": {"records": [{"id": 1, "due": "2026-01-10"}, {"id": 3, "due": "2026-01-15"}, {"id": 2, "due": "2026-01-20"}],
                  "compare_date": "2026-01-15", "field": "due", "operator": "on_or_after"},
         "expect": {"records": [{"id": 3}, {"id": 2}]}},
        {"label": "a date and time is compared by its day",
         "args": {"records": [{"id": 1, "at": "2026-01-15T23:59:00"}], "compare_date": "2026-01-15T00:00:00", "field": "at", "operator": "on"},
         "expect": {"records": [{"id": 1}]}},
        {"label": "records with no date are dropped by default",
         "args": {"records": [{"id": 1}, {"id": 2, "due": None}], "compare_date": "2026-01-15", "field": "due", "operator": "before"},
         "expect": {"records": []}},
        {"label": "records with no date kept on request",
         "args": {"records": [{"id": 1}], "compare_date": "2026-01-15", "field": "due", "operator": "before", "keep_blank": True},
         "expect": {"records": [{"id": 1}]}},
    ],
    invalid=[
        {"label": "a record date that is not a date", "args": {"records": [{"due": "soon"}], "compare_date": "2026-01-15", "field": "due"}, "code": "not_a_date"},
        {"label": "the compare date is not a date", "args": {"records": [], "compare_date": "x", "field": "due"}, "code": "not_a_date"},
        {"label": "unknown operator", "args": {"records": [], "compare_date": "2026-01-15", "field": "due", "operator": "near"}, "code": "invalid_input"},
        {"label": "records must be a list", "args": {"records": "no", "compare_date": "2026-01-15", "field": "due"}, "code": "invalid_input"},
    ],
)
def filter_records_by_date(ctx, *, records, compare_date, field: str, operator: str = "before", keep_blank: bool = False) -> dict:
    """Keeps the records whose date field is before, after or on a date that arrives while the app runs, such as today."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if operator not in _DATE_OPERATORS:
        raise CardError("invalid_input", f"Operator must be one of: {', '.join(_DATE_OPERATORS)}.")
    if not isinstance(field, str) or not field.strip():
        raise CardError("invalid_input", "Say which date field to compare.")
    limit = to_date(compare_date, "compare_date")
    keep = {
        "before": lambda d: d < limit, "after": lambda d: d > limit, "on": lambda d: d == limit,
        "on_or_before": lambda d: d <= limit, "on_or_after": lambda d: d >= limit,
    }[operator]
    out = []
    for rec in bounded(records, what="records"):
        raw = get_field(rec, field) if isinstance(rec, dict) else None
        if is_blank(raw):
            if keep_blank:
                out.append(rec)
            continue
        if keep(to_date(raw, field)):
            out.append(rec)
    return {"records": out}
