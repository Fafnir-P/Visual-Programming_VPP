"""Keys and Constraints (Data Modeling / Storage). Cards that enforce data integrity rules."""
from __future__ import annotations

from ..runtime import CardError, card, check_identifier

CATEGORY = "Data Modeling / Storage"
GROUP = "Keys and Constraints"


@card(
    "Set Primary Key Field",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "sets primary key",
            "tables": {"products": [{"name": "sku", "type": "text", "unique": True}]},
            "args": {"table": "products", "field": "sku"},
            "expect": {"field_name": "sku"},
        },
        {
            "label": "default to id field",
            "tables": {"orders": []},
            "args": {"table": "orders"},
            "expect": {"field_name": "id"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x"}, "code": "no_such_table"},
        {"label": "field not unique", "tables": {"products": [{"name": "name", "type": "text"}]}, "args": {"table": "products", "field": "name"}, "code": "invalid_input"},
    ],
)
def set_primary_key_field(ctx, *, table: str, field: str = "id") -> dict:
    """Designates a field as the unique identifier that every record must have."""
    schema = ctx.store.schema(table)["fields"]
    if field != "id":
        spec = next((f for f in schema if f["name"] == field), None)
        if spec is None:
            raise CardError("unknown_field", f"Field '{field}' not found in table '{table}'.", {"field": field})
        if not spec.get("unique"):
            raise CardError("invalid_input", f"Field '{field}' must be unique to be a primary key.", {"field": field})
    return {"field_name": field}


@card(
    "Enforce Unique Field Value",
    category=CATEGORY, group=GROUP,
    inputs=[],
    outputs=["field_name"],
    phase="generation",
    effects=["writes_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "marks field unique",
            "tables": {"products": [{"name": "sku", "type": "text"}]},
            "args": {"table": "products", "field": "sku"},
            "expect": {"field_name": "sku"},
        },
        {
            "label": "marks email unique",
            "tables": {"users": [{"name": "email", "type": "email"}]},
            "args": {"table": "users", "field": "email"},
            "expect": {"field_name": "email"},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "field": "x"}, "code": "no_such_table"},
        {"label": "no such field", "tables": {"products": []}, "args": {"table": "products", "field": "x"}, "code": "unknown_field"},
    ],
)
def enforce_unique_field_value(ctx, *, table: str, field: str) -> dict:
    """Makes the saved table itself refuse two records with the same value in the specified field."""
    schema = ctx.store.schema(table)["fields"]
    spec = next((f for f in schema if f["name"] == field), None)
    if spec is None:
        raise CardError("unknown_field", f"Field '{field}' not found in table '{table}'.", {"field": field})
    ctx.store.update_field(table, field, {"unique": True})
    return {"field_name": field}


@card(
    "Reference Linked Record",
    category=CATEGORY, group=GROUP,
    inputs=["record"],
    outputs=["record"],
    phase="runtime",
    effects=["reads_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "validates reference exists",
            "tables": {"customers": [], "orders": [{"name": "customer_id", "type": "integer", "references": "customers"}]},
            "rows": {"customers": [{}]},
            "args": {"record": {"customer_id": 1}, "field": "customer_id", "table": "orders"},
            "expect": {"record": {"customer_id": 1}},
        },
        {
            "label": "null reference allowed if not required",
            "tables": {"customers": [], "orders": [{"name": "customer_id", "type": "integer", "references": "customers"}]},
            "args": {"record": {"customer_id": None}, "field": "customer_id", "table": "orders"},
            "expect": {"record": {"customer_id": None}},
        },
    ],
    invalid=[
        {
            "label": "reference not found",
            "tables": {"customers": [], "orders": [{"name": "customer_id", "type": "integer", "references": "customers"}]},
            "args": {"record": {"customer_id": 999}, "field": "customer_id", "table": "orders"},
            "code": "missing_reference",
        },
        {
            "label": "required reference is null",
            "tables": {"customers": [], "orders": [{"name": "customer_id", "type": "integer", "references": "customers", "required": True}]},
            "args": {"record": {"customer_id": None}, "field": "customer_id", "table": "orders"},
            "code": "required",
        },
    ],
)
def reference_linked_record(ctx, *, record: dict, field: str, table: str = "records",
                           referenced_table: str | None = None) -> dict:
    """Makes sure a field value points to a record that exists in the linked table."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a dict.")
    
    value = record.get(field)
    
    # Determine the referenced table from schema if not provided
    if referenced_table is None:
        schema = ctx.store.schema(table)["fields"]
        spec = next((f for f in schema if f["name"] == field), None)
        if spec and "references" in spec:
            referenced_table = spec["references"]
        else:
            raise CardError("invalid_input", f"Field '{field}' is not a reference field.", {"field": field})
    
    # Check if required
    schema = ctx.store.schema(table)["fields"]
    spec = next((f for f in schema if f["name"] == field), None)
    is_required = spec.get("required", False) if spec else False
    
    if value is None:
        if is_required:
            raise CardError("required", f"{field} is required.", {"field": field})
        return {"record": record}
    
    # Validate the reference exists
    referenced = ctx.store.get(referenced_table, value)
    if referenced is None:
        raise CardError("missing_reference", f"Referenced record not found in {referenced_table}.", {"field": field})
    
    return {"record": record}


@card(
    "Prevent Accidental Delete",
    category=CATEGORY, group=GROUP,
    inputs=["record_id"],
    outputs=["can_delete"],
    phase="runtime",
    effects=["reads_store"],
    idempotent=True,
    role="data",
    examples=[
        {
            "label": "allows delete when no references",
            "tables": {"categories": [], "products": [{"name": "category_id", "type": "integer", "references": "categories"}]},
            "rows": {"categories": [{}]},
            "args": {"table": "categories", "record_id": 1},
            "expect": {"can_delete": True},
        },
        {
            "label": "blocks delete when references exist",
            "tables": {"categories": [], "products": [{"name": "category_id", "type": "integer", "references": "categories", "protect_delete": True}]},
            "rows": {"categories": [{}], "products": [{"category_id": 1}]},
            "args": {"table": "categories", "record_id": 1},
            "expect": {"can_delete": False},
        },
    ],
    invalid=[
        {"label": "no such table", "args": {"table": "missing", "record_id": 1}, "code": "no_such_table"},
        {"label": "record not found", "tables": {"categories": []}, "args": {"table": "categories", "record_id": 999}, "code": "not_found"},
    ],
)
def prevent_accidental_delete(ctx, *, table: str, record_id: int) -> dict:
    """Blocks deletion of a record if other records reference it or a condition is met."""
    record = ctx.store.get(table, record_id)
    if record is None:
        raise CardError("not_found", f"Record {record_id} not found in {table}.")
    
    # Check all tables for references to this record
    for other_table in ctx.store.tables():
        if other_table == table:
            continue
        schema = ctx.store.schema(other_table)["fields"]
        for field_spec in schema:
            if field_spec.get("references") == table and field_spec.get("protect_delete"):
                # Check if any records reference this one
                referencing = ctx.store.find(
                    other_table,
                    where={"field": field_spec["name"], "op": "eq", "value": record_id},
                    limit=1
                )
                if referencing:
                    return {"can_delete": False}
    
    return {"can_delete": True}
