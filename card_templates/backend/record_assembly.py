"""Record Assembly (Backend Processing). Cards that merge, build, rename, and select fields in records."""
from __future__ import annotations

from ..runtime import CardError, card, get_field

CATEGORY = "Backend Processing"
GROUP = "Record Assembly"


@card(
    "Merge Two Records",
    category=CATEGORY,
    group=GROUP,
    inputs=["record_a", "record_b"],
    outputs=["record"],
    examples=[
        {
            "label": "combines fields from both records",
            "args": {"record_a": {"name": "bolt"}, "record_b": {"qty": 5}},
            "expect": {"record": {"name": "bolt", "qty": 5}},
        },
        {
            "label": "second record overrides first when strategy is overwrite",
            "args": {
                "record_a": {"name": "bolt", "qty": 10},
                "record_b": {"qty": 5},
                "strategy": "overwrite",
            },
            "expect": {"record": {"name": "bolt", "qty": 5}},
        },
    ],
    invalid=[
        {
            "label": "record_a must be a record",
            "args": {"record_a": "not a record", "record_b": {}},
            "code": "invalid_input",
        },
        {
            "label": "record_b must be a record",
            "args": {"record_a": {}, "record_b": "not a record"},
            "code": "invalid_input",
        },
    ],
)
def merge_two_records(ctx, *, record_a, record_b, strategy: str = "overwrite") -> dict:
    """Combines fields from two records into one, with options for handling duplicate field names."""
    if not isinstance(record_a, dict):
        raise CardError("invalid_input", "First input must be a record.")
    if not isinstance(record_b, dict):
        raise CardError("invalid_input", "Second input must be a record.")

    merged = record_a.copy()
    if strategy == "overwrite":
        merged.update(record_b)
    elif strategy == "keep_first":
        for key, value in record_b.items():
            if key not in merged:
                merged[key] = value
    else:
        merged.update(record_b)
    return {"record": merged}


@card(
    "Build Record From Fields",
    category=CATEGORY,
    group=GROUP,
    inputs=[],
    outputs=["record"],
    examples=[
        {
            "label": "builds a record from individual values",
            "args": {"fields": {"name": "bolt", "qty": 5, "price": 0.25}},
            "expect": {"record": {"name": "bolt", "qty": 5, "price": 0.25}},
        },
        {
            "label": "empty fields creates empty record",
            "args": {"fields": {}},
            "expect": {"record": {}},
        },
    ],
    invalid=[
        {
            "label": "fields must be a record",
            "args": {"fields": "not a record"},
            "code": "invalid_input",
        },
        {
            "label": "fields cannot be a list",
            "args": {"fields": []},
            "code": "invalid_input",
        },
    ],
)
def build_record_from_fields(ctx, *, fields: dict) -> dict:
    """Creates a new record by selecting and assembling individual field values."""
    if not isinstance(fields, dict):
        raise CardError("invalid_input", "Fields must be a record.")
    return {"record": fields.copy()}


@card(
    "Rename Record Fields",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["record"],
    examples=[
        {
            "label": "renames fields according to mapping",
            "args": {"record": {"old_name": "bolt", "qty": 5}, "mapping": {"old_name": "name"}},
            "expect": {"record": {"name": "bolt", "qty": 5}},
        },
        {
            "label": "keeps unmapped fields unchanged",
            "args": {"record": {"a": 1, "b": 2}, "mapping": {"a": "x"}},
            "expect": {"record": {"x": 1, "b": 2}},
        },
    ],
    invalid=[
        {
            "label": "record must be a record",
            "args": {"record": "not a record", "mapping": {}},
            "code": "invalid_input",
        },
        {
            "label": "mapping must be a record",
            "args": {"record": {}, "mapping": []},
            "code": "invalid_input",
        },
    ],
)
def rename_record_fields(ctx, *, record, mapping: dict) -> dict:
    """Changes field names in a record to new names while keeping values unchanged."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Input must be a record.")
    if not isinstance(mapping, dict):
        raise CardError("invalid_input", "Mapping must be a record.")

    renamed = {}
    for old_name, value in record.items():
        new_name = mapping.get(old_name, old_name)
        renamed[new_name] = value
    return {"record": renamed}


@card(
    "Keep Only Selected Fields",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["record"],
    examples=[
        {
            "label": "keeps only specified fields",
            "args": {"record": {"name": "bolt", "qty": 5, "price": 0.25}, "fields": ["name", "qty"]},
            "expect": {"record": {"name": "bolt", "qty": 5}},
        },
        {
            "label": "missing fields are omitted",
            "args": {"record": {"name": "bolt"}, "fields": ["name", "qty"]},
            "expect": {"record": {"name": "bolt"}},
        },
    ],
    invalid=[
        {
            "label": "record must be a record",
            "args": {"record": "not a record", "fields": []},
            "code": "invalid_input",
        },
        {
            "label": "fields must be a list",
            "args": {"record": {}, "fields": "not a list"},
            "code": "invalid_input",
        },
    ],
)
def keep_only_selected_fields(ctx, *, record, fields: list[str]) -> dict:
    """Keeps only the named fields of a record and drops all the others."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Input must be a record.")
    if not isinstance(fields, list):
        raise CardError("invalid_input", "Fields must be a list.")

    selected = {}
    for field in fields:
        if field in record:
            selected[field] = record[field]
    return {"record": selected}


@card(
    "Join Records Into List",
    category=CATEGORY,
    group=GROUP,
    inputs=["record_1", "record_2"],
    outputs=["records"],
    examples=[
        {
            "label": "combines individual records into a list",
            "args": {"record_1": {"id": 1}, "record_2": {"id": 2}},
            "expect": {"records": [{"id": 1}, {"id": 2}]},
        },
        {
            "label": "includes additional records if provided",
            "args": {
                "record_1": {"id": 1},
                "record_2": {"id": 2},
                "additional": [{"id": 3}, {"id": 4}],
            },
            "expect": {"records": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]},
        },
    ],
    invalid=[
        {
            "label": "record_1 must be a record",
            "args": {"record_1": "not a record", "record_2": {}},
            "code": "invalid_input",
        },
        {
            "label": "record_2 must be a record",
            "args": {"record_1": {}, "record_2": []},
            "code": "invalid_input",
        },
    ],
)
def join_records_into_list(ctx, *, record_1, record_2, additional: list | None = None) -> dict:
    """Collects multiple individual records into a single list for batch processing."""
    if not isinstance(record_1, dict):
        raise CardError("invalid_input", "First record must be a record.")
    if not isinstance(record_2, dict):
        raise CardError("invalid_input", "Second record must be a record.")

    records = [record_1, record_2]
    if additional:
        if not isinstance(additional, list):
            raise CardError("invalid_input", "Additional records must be a list.")
        records.extend(additional)
    return {"records": records}


@card(
    "Build Summary Record",
    category=CATEGORY, group=GROUP,
    inputs=["value_1", "value_2", "value_3", "value_4"], outputs=["record", "rows"],
    examples=[
        {"label": "three numbers get labels",
         "args": {"value_1": 42, "value_2": 12500, "value_3": 3.5, "labels": ["Orders", "Revenue", "Average"]},
         "expect": {"record": {"Orders": 42, "Revenue": 12500, "Average": 3.5},
                    "rows": [{"label": "Orders", "value": 42}, {"label": "Revenue", "value": 12500}, {"label": "Average", "value": 3.5}]}},
        {"label": "a value that is not linked is left out",
         "args": {"value_1": 7, "value_3": 9, "labels": ["A", "B", "C"]},
         "expect": {"record": {"A": 7, "C": 9}, "rows": [{"label": "A", "value": 7}, {"label": "C", "value": 9}]}},
        {"label": "without labels the names are Value 1, Value 2 ...",
         "args": {"value_2": "late"},
         "expect": {"record": {"Value 2": "late"}}},
        {"label": "zero and false are real values",
         "args": {"value_1": 0, "value_2": False, "labels": ["Zero", "Off"]},
         "expect": {"record": {"Zero": 0, "Off": False}}},
    ],
    invalid=[
        {"label": "nothing to summarise", "args": {}, "code": "required"},
        {"label": "two labels the same", "args": {"value_1": 1, "value_2": 2, "labels": ["X", "x"]}, "code": "duplicate_value"},
        {"label": "labels must be a list of text", "args": {"value_1": 1, "labels": "A"}, "code": "invalid_input"},
    ],
)
def build_summary_record(ctx, *, value_1=None, value_2=None, value_3=None, value_4=None, labels: list | None = None) -> dict:
    """Puts up to four values under labels in one record and in a list of label and value rows, ready for a summary table."""
    if labels is not None and (not isinstance(labels, list) or not all(isinstance(x, str) and x.strip() for x in labels)):
        raise CardError("invalid_input", "Labels must be a list of texts.")
    names = [(labels[i].strip() if labels and i < len(labels) else f"Value {i + 1}") for i in range(4)]
    values = [value_1, value_2, value_3, value_4]
    used = [(n, v) for n, v in zip(names, values) if v is not None]
    if not used:
        raise CardError("required", "Link at least one value.")
    seen = set()
    for n, _ in used:
        if n.casefold() in seen:
            raise CardError("duplicate_value", f"The label {n} is used twice.", {"label": n})
        seen.add(n.casefold())
    return {"record": {n: v for n, v in used}, "rows": [{"label": n, "value": v} for n, v in used]}


@card(
    "Set Field Of Record",
    category=CATEGORY, group=GROUP,
    inputs=["value", "record"], outputs=["record"],
    examples=[
        {"label": "a new record with one field, for Update Existing Record",
         "args": {"value": 120, "field": "stock"},
         "expect": {"record": {"stock": 120}}},
        {"label": "one field of an existing record is replaced",
         "args": {"value": "late", "field": "status", "record": {"id": 4, "status": "new"}},
         "expect": {"record": {"id": 4, "status": "late"}}},
        {"label": "a field is added",
         "args": {"value": 1, "field": "flag", "record": {"id": 1}},
         "expect": {"record": {"id": 1, "flag": 1}}},
        {"label": "a blank value is kept as a value",
         "args": {"value": None, "field": "note"},
         "expect": {"record": {"note": None}}},
    ],
    invalid=[
        {"label": "a field name is needed", "args": {"value": 1, "field": " "}, "code": "invalid_input"},
        {"label": "the record must be a record", "args": {"value": 1, "field": "a", "record": [1]}, "code": "invalid_input"},
    ],
)
def set_field_of_record(ctx, *, value, field: str, record=None) -> dict:
    """Gives a record one field with the value that arrives; without a record it makes a new one, ready for Update Existing Record."""
    if not isinstance(field, str) or not field.strip():
        raise CardError("invalid_input", "Say which field to set.")
    if record is not None and not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a record.")
    out = dict(record or {})
    out[field.strip()] = value
    return {"record": out}
