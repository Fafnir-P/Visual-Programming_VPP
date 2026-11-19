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
    "Import Records",
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
        {
            "label": "imports array of records from JSON",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
            "args": {"content": '[{"name":"Bolt","qty":10},{"name":"Nut","qty":20}]', "table": "products", "format": "json"},
            "expect": {"count": 2},
            "expect_rows": {"products": [{"name": "Bolt", "qty": 10}, {"name": "Nut", "qty": 20}]},
        },
        {
            "label": "imports single record from JSON",
            "tables": {"settings": [{"name": "key", "type": "text"}, {"name": "value", "type": "text"}]},
            "args": {"content": '{"key":"theme","value":"dark"}', "table": "settings", "format": "json"},
            "expect": {"count": 1},
            "expect_rows": {"settings": [{"key": "theme", "value": "dark"}]},
        },
    ],
    invalid=[
        {"label": "file too large", "args": {"content": "x" * (MAX_IMPORT_BYTES + 1), "table": "items"}, "code": "file_too_large"},
        {"label": "JSON file too large", "args": {"content": "x" * (MAX_IMPORT_BYTES + 1), "table": "items", "format": "json"}, "code": "file_too_large"},
        {
            "label": "too many rows",
            "tables": {"items": [{"name": "x", "type": "text"}]},
            "args": {"content": "x\n" + "\n".join(["row"] * (MAX_IMPORT_ROWS + 1)), "table": "items"},
            "code": "too_many_rows",
        },
        {"label": "invalid JSON", "tables": {"items": []}, "args": {"content": "{bad json", "table": "items", "format": "json"}, "code": "invalid_input"},
        {"label": "unknown format", "tables": {"items": []}, "args": {"content": "a", "table": "items", "format": "xml"}, "code": "invalid_input"},
    ],
)
def import_records(ctx, *, content: str, table: str, format: str = "csv", has_header: bool = True,
                   delimiter: str = ",") -> dict:
    """Loads records into a table from a CSV or JSON file the user selects; files that are too large are refused."""
    if format not in ("csv", "json"):
        raise CardError("invalid_input", f"Unknown format: {format}. Use csv or json.")
    if not isinstance(content, str):
        raise CardError("invalid_input", "Content must be text.")
    if len(content.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise CardError("file_too_large", f"File is too large (limit {MAX_IMPORT_BYTES} bytes).")

    if format == "json":
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
    else:
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
        records = [{k: v for k, v in row.items() if k in field_specs} for row in rows]

    stored = ctx.store.insert_many(table, bounded(records, MAX_IMPORT_ROWS, "records"))

    return {"count": len(stored), "records": stored}


@card(
    "Export Table",
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
        {
            "label": "exports all records as JSON",
            "tables": {"products": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
            "rows": {"products": [{"name": "Bolt", "qty": 10}, {"name": "Nut", "qty": 20}]},
            "args": {"table": "products", "format": "json"},
            "expect": {"filename": "products.json", "mime": "application/json"},
        },
        {
            "label": "exports with custom filename",
            "tables": {"items": [{"name": "code", "type": "text"}]},
            "rows": {"items": [{"code": "A1"}]},
            "args": {"table": "items", "format": "json", "filename": "export.json"},
            "expect": {"filename": "export.json"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing"}, "code": "no_such_table"},
        {"label": "unknown format", "tables": {"items": []}, "args": {"table": "items", "format": "xml"}, "code": "invalid_input"},
    ],
)
def export_table(ctx, *, table: str, records: list | None = None, filename: str | None = None,
                 format: str = "csv", delimiter: str = ",", pretty: bool = True) -> dict:
    """Saves a whole table, the records matching a filter, or the records on screen to a CSV or JSON file the user picks."""
    if format not in ("csv", "json"):
        raise CardError("invalid_input", f"Unknown format: {format}. Use csv or json.")
    if records is None:
        records = ctx.store.find(table)

    if not records:
        records = []

    if format == "json":
        content = json.dumps(records, indent=2 if pretty else None, ensure_ascii=False)
        return {"filename": filename or f"{table}.json", "mime": "application/json", "content": content}

    # Get field names from schema
    schema = ctx.store.schema(table)["fields"]
    field_names = [f["name"] for f in schema]

    # Build CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=field_names, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow({k: csv_safe_cell(v) for k, v in record.items() if k in field_names})

    return {"filename": filename or f"{table}.csv", "mime": "text/csv", "content": output.getvalue()}


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


_FILE_TYPES = (".csv", ".json", ".txt")


@card(
    "Read Chosen File",
    category=CATEGORY, group=GROUP,
    inputs=["filename", "content"], outputs=["content", "filename", "size"],
    phase="runtime", effects=["file_text_in"], idempotent=True, role="data",
    examples=[
        {"label": "a csv file",
         "args": {"filename": "count.csv", "content": "sku,qty\nA,3\n"},
         "expect": {"content": "sku,qty\nA,3\n", "filename": "count.csv", "size": 12}},
        {"label": "the type is not case sensitive",
         "args": {"filename": "DATA.JSON", "content": "[]"},
         "expect": {"filename": "DATA.JSON", "size": 2}},
        {"label": "size counts bytes, not letters",
         "args": {"filename": "n.txt", "content": "\u00e9"},
         "expect": {"size": 2}},
        {"label": "another allowed type list",
         "args": {"filename": "a.tsv", "content": "x", "allowed_types": [".tsv"]},
         "expect": {"filename": "a.tsv"}},
    ],
    invalid=[
        {"label": "no file chosen", "args": {"filename": None, "content": None}, "code": "no_file"},
        {"label": "file name with a folder in it", "args": {"filename": "../secret.csv", "content": "x"}, "code": "bad_filename"},
        {"label": "type not allowed", "args": {"filename": "run.exe", "content": "x"}, "code": "file_type_not_allowed"},
        {"label": "file too large", "args": {"filename": "big.csv", "content": "x" * (MAX_IMPORT_BYTES + 1)}, "code": "file_too_large"},
        {"label": "content must be text", "args": {"filename": "a.csv", "content": 5}, "code": "invalid_input"},
    ],
)
def read_chosen_file(ctx, *, filename, content, allowed_types: list | None = None) -> dict:
    """Passes on the text of the file the user chose, after checking its name, type and size; the trusted shell reads the file, never the card."""
    if filename is None or content is None:
        raise CardError("no_file", "No file has been chosen yet.")
    if not isinstance(filename, str) or not isinstance(content, str):
        raise CardError("invalid_input", "The file name and the file text must be text.")
    name = filename.strip()
    if not name or any(ch in name for ch in "/\\:\x00") or name in (".", ".."):
        raise CardError("bad_filename", "The file name must be a plain name, with no folder.")
    types = [t.lower() for t in (allowed_types if allowed_types is not None else _FILE_TYPES)]
    if not any(name.lower().endswith(t) for t in types):
        raise CardError("file_type_not_allowed", f"Only these file types are allowed: {', '.join(types)}.", {"allowed": types})
    size = len(content.encode("utf-8"))
    if size > MAX_IMPORT_BYTES:
        raise CardError("file_too_large", f"File is too large (limit {MAX_IMPORT_BYTES} bytes).")
    return {"content": content, "filename": name, "size": size}
