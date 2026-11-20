"""Schema Definition (Data Modeling / Storage). Cards that create tables and define their structure."""
from __future__ import annotations

from ..runtime import CardError, card, check_identifier

CATEGORY = "Data Modeling / Storage"
GROUP = "Schema Definition"


@card(
    "Define Data Table",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["table_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "creates an empty table",
            "args": {"table": "products", "description": "Product catalog"},
            "expect": {"table_name": "products"},
        },
        {
            "label": "skip if exists",
            "tables": {"items": []},
            "args": {"table": "items", "if_exists": "skip"},
            "expect": {"table_name": "items"},
        },
    ],
    invalid=[
        {"label": "bad table name", "args": {"table": "123bad"}, "code": "bad_name"},
        {"label": "table exists", "tables": {"items": []}, "args": {"table": "items"}, "code": "table_exists"},
    ],
)
def define_data_table(ctx, *, table: str, description: str = "", if_exists: str = "error") -> dict:
    """Creates a new table with a name and description to hold records in the app."""
    check_identifier(table, "table name")
    if if_exists not in ("error", "skip"):
        raise CardError("invalid_input", "if_exists must be 'error' or 'skip'.")
    ctx.store.define_table(table, [], if_exists=if_exists)
    return {"table_name": table}


@card(
    "Add Field To Table",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "adds text field",
            "tables": {"products": []},
            "args": {"table": "products", "field": "name", "type": "text", "required": True},
            "expect": {"field_name": "name"},
        },
        {
            "label": "adds number field with range",
            "tables": {"products": []},
            "args": {"table": "products", "field": "price", "type": "number", "min": 0, "max": 10000},
            "expect": {"field_name": "price"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x", "type": "text"}, "code": "no_such_table"},
        {"label": "bad field name", "tables": {"products": []}, "args": {"table": "products", "field": "9bad", "type": "text"}, "code": "bad_name"},
    ],
)
def add_field_to_table(ctx, *, table: str, field: str, type: str, required: bool = False,
                       unique: bool = False, default=None, choices: list | None = None,
                       min=None, max=None, min_length: int | None = None, max_length: int | None = None,
                       pattern: str | None = None) -> dict:
    """Adds a named column to a table with a data type, and optional simple rules such as required or a number range."""
    check_identifier(field, "field name")
    spec: dict = {"name": field, "type": type, "required": required, "unique": unique}
    if default is not None:
        spec["default"] = default
    if choices is not None:
        spec["choices"] = choices
    if min is not None:
        spec["min"] = min
    if max is not None:
        spec["max"] = max
    if min_length is not None:
        spec["min_length"] = min_length
    if max_length is not None:
        spec["max_length"] = max_length
    if pattern is not None:
        spec["pattern"] = pattern
    ctx.store.add_field(table, spec)
    return {"field_name": field}


@card(
    "Set Field Default Value",
    category=CATEGORY, group=GROUP,
    inputs=["default_value"],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "sets static default",
            "tables": {"products": [{"name": "status", "type": "text"}]},
            "args": {"table": "products", "field": "status", "default_value": "pending"},
            "expect": {"field_name": "status"},
        },
        {
            "label": "sets dynamic today",
            "tables": {"orders": [{"name": "order_date", "type": "date"}]},
            "args": {"table": "orders", "field": "order_date", "default_value": "{today}"},
            "expect": {"field_name": "order_date"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x", "default_value": "y"}, "code": "no_such_table"},
        {"label": "no such field", "tables": {"products": []}, "args": {"table": "products", "field": "x", "default_value": "y"}, "code": "unknown_field"},
    ],
)
def set_field_default_value(ctx, *, table: str, field: str, default_value) -> dict:
    """Assigns a default value that fills automatically when creating a new record in the table."""
    schema = ctx.store.schema(table)["fields"]
    spec = next((f for f in schema if f["name"] == field), None)
    if spec is None:
        raise CardError("unknown_field", f"Field '{field}' not found in table '{table}'.", {"field": field})
    ctx.store.update_field(table, field, {"default": default_value})
    return {"field_name": field}


@card(
    "Link Tables By Relationship",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "creates foreign key field",
            "tables": {"customers": [], "orders": []},
            "args": {"from_table": "orders", "field": "customer_id", "to_table": "customers"},
            "expect": {"field_name": "customer_id"},
        },
        {
            "label": "with protect delete",
            "tables": {"categories": [], "products": []},
            "args": {"from_table": "products", "field": "category_id", "to_table": "categories", "protect_delete": True},
            "expect": {"field_name": "category_id"},
        },
    ],
    invalid=[
        {"label": "no such from table", "args": {"from_table": "missing", "field": "x", "to_table": "y"}, "code": "no_such_table"},
        {"label": "no such to table", "tables": {"orders": []}, "args": {"from_table": "orders", "field": "x", "to_table": "missing"}, "code": "no_such_table"},
    ],
)
def link_tables_by_relationship(ctx, *, from_table: str, field: str, to_table: str,
                                required: bool = False, protect_delete: bool = False) -> dict:
    """Connects two tables so records in one can reference records in the other."""
    check_identifier(field, "field name")
    if from_table not in ctx.store.tables():
        raise CardError("no_such_table", f"Table '{from_table}' does not exist.")
    if to_table not in ctx.store.tables():
        raise CardError("no_such_table", f"Table '{to_table}' does not exist.")
    spec = {
        "name": field,
        "type": "integer",
        "required": required,
        "references": to_table,
        "protect_delete": protect_delete,
    }
    ctx.store.add_field(from_table, spec)
    return {"field_name": field}


@card(
    "Define Choice List",
    category=CATEGORY, group=GROUP,
    inputs=["choices"],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "creates choice field",
            "tables": {"products": []},
            "args": {"table": "products", "field": "color", "choices": ["red", "green", "blue"]},
            "expect": {"field_name": "color"},
        },
        {
            "label": "creates multichoice field",
            "tables": {"products": []},
            "args": {"table": "products", "field": "tags", "type": "multichoice", "choices": ["new", "sale", "featured"]},
            "expect": {"field_name": "tags"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x", "choices": ["a"]}, "code": "no_such_table"},
        {"label": "empty choices", "tables": {"products": []}, "args": {"table": "products", "field": "x", "choices": []}, "code": "invalid_input"},
    ],
)
def define_choice_list(ctx, *, table: str, field: str, choices: list, type: str = "choice",
                       required: bool = False) -> dict:
    """Creates a dropdown list of allowed values that a field can use across the app."""
    check_identifier(field, "field name")
    if not choices:
        raise CardError("invalid_input", "Choices list cannot be empty.")
    if type not in ("choice", "multichoice"):
        raise CardError("invalid_input", "Type must be 'choice' or 'multichoice'.")
    spec = {"name": field, "type": type, "choices": choices, "required": required}
    ctx.store.add_field(table, spec)
    return {"field_name": field}


@card(
    "Add Calculated Field",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "creates calculated field",
            "tables": {"line_items": [{"name": "qty", "type": "integer"}, {"name": "price", "type": "number"}]},
            "args": {"table": "line_items", "field": "total", "expression": "qty * price"},
            "expect": {"field_name": "total"},
        },
        {
            "label": "with type specified",
            "tables": {"products": [{"name": "cost", "type": "number"}, {"name": "margin", "type": "number"}]},
            "args": {"table": "products", "field": "sell_price", "expression": "cost * (1 + margin)", "type": "currency"},
            "expect": {"field_name": "sell_price"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x", "expression": "1+1"}, "code": "no_such_table"},
        {"label": "bad field name", "tables": {"items": []}, "args": {"table": "items", "field": "9bad", "expression": "1+1"}, "code": "bad_name"},
    ],
)
def add_calculated_field(ctx, *, table: str, field: str, expression: str, type: str = "number") -> dict:
    """Defines a field whose value is worked out from other fields in the same record, using a formula the builder sets."""
    check_identifier(field, "field name")
    spec = {"name": field, "type": type, "computed": {"expr": expression}}
    ctx.store.add_field(table, spec)
    return {"field_name": field}


@card(
    "Enable Change History Tracking",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["table_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "enables tracking with default limit",
            "tables": {"products": []},
            "args": {"table": "products"},
            "expect": {"table_name": "products"},
        },
        {
            "label": "enables tracking with custom limit",
            "tables": {"orders": []},
            "args": {"table": "orders", "keep_versions": 5},
            "expect": {"table_name": "orders"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing"}, "code": "no_such_table"},
        {"label": "negative limit", "tables": {"products": []}, "args": {"table": "products", "keep_versions": -1}, "code": "invalid_input"},
    ],
)
def enable_change_history_tracking(ctx, *, table: str, keep_versions: int = 10) -> dict:
    """Makes a table keep the last few versions of each record, with when each change was made."""
    if keep_versions < 1:
        raise CardError("invalid_input", "keep_versions must be at least 1.")
    ctx.store.enable_history(table, keep=keep_versions)
    return {"table_name": table}


@card(
    "Define App Settings",
    category=CATEGORY, group=GROUP,
    inputs=["settings"],
    outputs=["record"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "creates settings table and record",
            "args": {"settings": {"currency": "USD", "tax_rate": 0.08}},
            "expect": {"record": {"id": 1, "currency": "USD", "tax_rate": 0.08}},
            "expect_rows": {"app_settings": [{"currency": "USD", "tax_rate": 0.08}]},
        },
        {
            "label": "updates if exists",
            "tables": {"app_settings": [{"name": "currency", "type": "text"}]},
            "rows": {"app_settings": [{"currency": "EUR"}]},
            "args": {"settings": {"currency": "GBP"}, "table": "app_settings"},
            "expect": {"record": {"id": 1, "currency": "GBP"}},
            "expect_rows": {"app_settings": [{"currency": "GBP"}]},
        },
    ],
    invalid=[
        {"label": "not a record", "args": {"settings": "bad"}, "code": "invalid_input"},
        {"label": "empty settings", "args": {"settings": {}}, "code": "invalid_input"},
    ],
)
def define_app_settings(ctx, *, settings: dict, table: str = "app_settings") -> dict:
    """Keeps the owner's app-wide options, such as default currency or reorder level, in one saved settings record."""
    if not isinstance(settings, dict) or not settings:
        raise CardError("invalid_input", "Settings must be a non-empty record.")
    
    with ctx.store.transaction():   # table and settings record are saved together or not at all
        return _save_settings(ctx, settings, table)


def _save_settings(ctx, settings: dict, table: str) -> dict:
    """Creates the settings table if needed and saves the one settings record."""
    if table not in ctx.store.tables():
        fields = []
        for key, value in settings.items():
            check_identifier(key, "setting name")
            if isinstance(value, bool):
                field_type = "bool"
            elif isinstance(value, int):
                field_type = "integer"
            elif isinstance(value, float):
                field_type = "number"
            else:
                field_type = "text"
            fields.append({"name": key, "type": field_type})
        ctx.store.define_table(table, fields, if_exists="skip")
    
    # Create or update the settings record
    existing = ctx.store.find(table, limit=1)
    if existing:
        record = ctx.store.update(table, existing[0]["id"], settings)
    else:
        record = ctx.store.insert(table, settings)
    
    return {"record": record}
