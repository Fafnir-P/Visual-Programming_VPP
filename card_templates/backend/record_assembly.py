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
