"""Import and Export (Data Modeling / Storage). Cards that move data in and out of tables."""
from __future__ import annotations

import csv
import io
import json

from ..runtime import (
    csv_safe_cell,
    MAX_IMPORT_BYTES,
    MAX_IMPORT_ROWS,
    CardError,
    bounded,
    card,
    validate_against,
)

CATEGORY = "Data Modeling / Storage"
GROUP = "Import and Export"


@card(
    "Import Records From CSV",
    category=CATEGORY, group=GROUP,
    inputs=["content"],
    outputs=["count", "records"],
    phase="runtime",
    effects=["writes_store", "file_text_in"],
    idempotent=False,
    role="data",
    examples=[
        {
            "label": "imports rows from CSV",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "price", "type": "number"}]},
            "args": {"content": "name,price\nBolt,1.5\nNut,0.75\n", "table": "products"},
            "expect": {"count": 2},
            "expect_rows": {"products": [{"name": "Bolt", "price": 1.5}, {"name": "Nut", "price": 0.75}]},
        },
        {
            "label": "skips header row",
            "tables": {"items": [{"name": "code", "type": "text"}]},
            "args": {"content": "code\nA1\nA2\n", "table": "items", "has_header": True},
            "expect": {"count": 2},
            "expect_rows": {"items": [{"code": "A1"}, {"code": "A2"}]},
        },
    ],
    invalid=[
        {"label": "file too large", "args": {"content": "x" * (MAX_IMPORT_BYTES + 1), "table": "items"}, "code": "file_too_large"},
        {
            "label": "too many rows",
            "tables": {"items": [{"name": "x", "type": "text"}]},
            "args": {"content": "x\n" + "\n".join(["row"] * (MAX_IMPORT_ROWS + 1)), "table": "items"},
            "code": "too_many_rows",
        },
    ],
)
def import_records_from_csv(ctx, *, content: str, table: str, has_header: bool = True,
                           delimiter: str = ",") -> dict:
    """Loads records into a table from a CSV file the user selects; files that are too large are refused."""
    if not isinstance(content, str):
        raise CardError("invalid_input", "Content must be text.")
    if len(content.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise CardError("file_too_large", f"File is too large (limit {MAX_IMPORT_BYTES} bytes).")
    
    schema = ctx.store.schema(table)["fields"]
    field_specs = {f["name"]: f for f in schema}
    
    content = content.lstrip("\ufeff")   # a spreadsheet may put a byte-order mark first
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise CardError("invalid_input", "Delimiter must be one character.")
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not has_header:
        # If no header, use field names from schema in order
        field_names = [f["name"] for f in schema]
        reader = csv.DictReader(io.StringIO(content), fieldnames=field_names, delimiter=delimiter)
    elif not any(name in field_specs for name in (reader.fieldnames or [])):
        raise CardError("no_matching_columns", "No column in the file matches a field of the table.",
                        {"columns": list(reader.fieldnames or [])})

    rows = list(reader)
    if len(rows) > MAX_IMPORT_ROWS:
        raise CardError("too_many_rows", f"Too many rows: {len(rows)} (limit {MAX_IMPORT_ROWS}).")
    
    records = []
    for row in rows:
        # Clean the row data
        clean = {}
        for key, value in row.items():
            if key in field_specs:
                clean[key] = value
        records.append(clean)
    
    stored = ctx.store.insert_many(table, bounded(records, MAX_IMPORT_ROWS, "records"))

    return {"count": len(stored), "records": stored}


@card(
    "Import Records From JSON",
    category=CATEGORY, group=GROUP,
    inputs=["content"],
    outputs=["count", "records"],
    phase="runtime",
    effects=["writes_store", "file_text_in"],
    idempotent=False,
    role="data",
    examples=[
        {
            "label": "imports array of records",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
            "args": {"content": '[{"name":"Bolt","qty":10},{"name":"Nut","qty":20}]', "table": "products"},
            "expect": {"count": 2},
            "expect_rows": {"products": [{"name": "Bolt", "qty": 10}, {"name": "Nut", "qty": 20}]},
        },
        {
            "label": "imports single record",
            "tables": {"settings": [{"name": "key", "type": "text"}, {"name": "value", "type": "text"}]},
            "args": {"content": '{"key":"theme","value":"dark"}', "table": "settings"},
            "expect": {"count": 1},
            "expect_rows": {"settings": [{"key": "theme", "value": "dark"}]},
        },
    ],
    invalid=[
        {"label": "file too large", "args": {"content": "x" * (MAX_IMPORT_BYTES + 1), "table": "items"}, "code": "file_too_large"},
        {"label": "invalid JSON", "tables": {"items": []}, "args": {"content": "{bad json", "table": "items"}, "code": "invalid_input"},
    ],
)
def import_records_from_json(ctx, *, content: str, table: str) -> dict:
    """Reads records from a JSON file the user picks and adds them to the table; files that are too large are refused."""
    if not isinstance(content, str):
        raise CardError("invalid_input", "Content must be text.")
    if len(content.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise CardError("file_too_large", f"File is too large (limit {MAX_IMPORT_BYTES} bytes).")
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise CardError("invalid_input", f"Invalid JSON: {e}") from None
    
    # Handle single record or array
    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise CardError("invalid_input", "JSON must be a record or array of records.")
    
    if len(records) > MAX_IMPORT_ROWS:
        raise CardError("too_many_rows", f"Too many rows: {len(records)} (limit {MAX_IMPORT_ROWS}).")
    
    stored = ctx.store.insert_many(table, bounded(records, MAX_IMPORT_ROWS, "records"))

    return {"count": len(stored), "records": stored}


@card(
    "Export Table To CSV",
    category=CATEGORY, group=GROUP,
    inputs=["records"],
    outputs=["filename", "mime", "content"],
    phase="runtime",
    effects=["reads_store", "file_text_out"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "exports all records",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "price", "type": "number"}]},
            "rows": {"products": [{"name": "Bolt", "price": 1.5}, {"name": "Nut", "price": 0.75}]},
            "args": {"table": "products"},
            "expect": {"filename": "products.csv", "mime": "text/csv"},
        },
        {
            "label": "exports filtered records",
            "tables": {"items": [{"name": "status", "type": "text"}]},
            "rows": {"items": [{"status": "active"}, {"status": "inactive"}]},
            "args": {"table": "items", "records": [{"status": "active"}]},
            "expect": {"filename": "items.csv"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing"}, "code": "no_such_table"},
    ],
)
def export_table_to_csv(ctx, *, table: str, records: list | None = None, filename: str | None = None,
                        delimiter: str = ",") -> dict:
    """Saves a whole table, the records matching a filter, or the records on screen to a CSV file the user picks."""
    if records is None:
        records = ctx.store.find(table)
    
    if not records:
        records = []
    
    # Get field names from schema
    schema = ctx.store.schema(table)["fields"]
    field_names = [f["name"] for f in schema]
    
    # Build CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=field_names, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow({k: csv_safe_cell(v) for k, v in record.items() if k in field_names})

    content = output.getvalue()
    fname = filename or f"{table}.csv"
    
    return {"filename": fname, "mime": "text/csv", "content": content}


@card(
    "Export Table To JSON",
    category=CATEGORY, group=GROUP,
    inputs=["records"],
    outputs=["filename", "mime", "content"],
    phase="runtime",
    effects=["reads_store", "file_text_out"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "exports all records",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
            "rows": {"products": [{"name": "Bolt", "qty": 10}, {"name": "Nut", "qty": 20}]},
            "args": {"table": "products"},
            "expect": {"filename": "products.json", "mime": "application/json"},
        },
        {
            "label": "exports with custom filename",
            "tables": {"items": [{"name": "code", "type": "text"}]},
            "rows": {"items": [{"code": "A1"}]},
            "args": {"table": "items", "filename": "export.json"},
            "expect": {"filename": "export.json"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing"}, "code": "no_such_table"},
    ],
)
def export_table_to_json(ctx, *, table: str, records: list | None = None, filename: str | None = None,
                        pretty: bool = True) -> dict:
    """Saves a whole table, the records matching a filter, or the records on screen to a JSON file the user picks."""
    if records is None:
        records = ctx.store.find(table)
    
    if not records:
        records = []
    
    indent = 2 if pretty else None
    content = json.dumps(records, indent=indent, ensure_ascii=False)
    fname = filename or f"{table}.json"
    
    return {"filename": fname, "mime": "application/json", "content": content}


@card(
    "Load Sample Data Set",
    category=CATEGORY, group=GROUP,
    inputs=["sample_data"],
    outputs=["count", "records"],
    phase="generation",
    effects=["writes_store"],
    idempotent=False,
    role="data",
    examples=[
        {
            "label": "loads sample records",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "price", "type": "number"}]},
            "args": {"table": "products", "sample_data": [{"name": "Bolt", "price": 1.5}, {"name": "Nut", "price": 0.75}]},
            "expect": {"count": 2},
            "expect_rows": {"products": [{"name": "Bolt", "price": 1.5}, {"name": "Nut", "price": 0.75}]},
        },
        {
            "label": "loads with default samples",
            "tables": {"items": [{"name": "code", "type": "text"}, {"name": "qty", "type": "integer"}]},
            "args": {"table": "items"},
            "expect": {"count": 3},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "sample_data": []}, "code": "no_such_table"},
        {"label": "not a list", "tables": {"items": []}, "args": {"table": "items", "sample_data": "bad"}, "code": "invalid_input"},
    ],
)
def load_sample_data_set(ctx, *, table: str, sample_data: list | None = None) -> dict:
    """Fills a table with example records so the user can test the app immediately."""
    ctx.store.schema(table)  # raises no_such_table when the table is missing
    if sample_data is not None:
        if not isinstance(sample_data, list):
            raise CardError("invalid_input", "sample_data must be a list of records.")
        records = sample_data
    else:
        # Generate default sample data based on schema
        schema = ctx.store.schema(table)["fields"]
        records = []
        for i in range(3):
            record = {}
            for field in schema:
                fname = field["name"]
                ftype = field["type"]
                if ftype == "text":
                    record[fname] = f"Sample {i + 1}"
                elif ftype in ("number", "currency"):
                    record[fname] = (i + 1) * 10.0
                elif ftype == "integer":
                    record[fname] = (i + 1) * 10
                elif ftype == "bool":
                    record[fname] = i % 2 == 0
                elif ftype == "date":
                    record[fname] = f"2026-01-{(i + 1):02d}"
                elif ftype == "email":
                    record[fname] = f"user{i + 1}@example.com"
            records.append(record)
    
    stored = ctx.store.insert_many(table, bounded(records, MAX_IMPORT_ROWS, "records"))

    return {"count": len(stored), "records": stored}
