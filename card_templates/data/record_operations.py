"""Record Operations (Data Modeling / Storage). CRUD operations on saved records."""
from __future__ import annotations

from ..runtime import CardError, bounded, card, get_field, MAX_LOOP_ITEMS

CATEGORY = "Data Modeling / Storage"
GROUP = "Record Operations"


@card(
    "Create New Record", category=CATEGORY, group=GROUP,
    inputs=["values"], outputs=["record"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "simple create",
         "tables": {"items": [{"name": "name", "type": "text", "required": True}, {"name": "qty", "type": "integer"}]},
         "args": {"values": {"name": "Bolt", "qty": 10}, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Bolt", "qty": 10}}},
        {"label": "create with defaults",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "active", "type": "bool", "default": True}]},
         "args": {"values": {"name": "Nut"}, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Nut", "active": True}}},
    ],
    invalid=[
        {"label": "missing required field",
         "tables": {"items": [{"name": "name", "type": "text", "required": True}]},
         "args": {"values": {}, "table": "items"}, "code": "required"},
        {"label": "table does not exist",
         "args": {"values": {"name": "Bolt"}, "table": "missing"}, "code": "no_such_table"},
    ],
)
def create_new_record(ctx, *, values, table: str = "records") -> dict:
    """Adds a single record to a table with values the user provides or maps from inputs."""
    if not isinstance(values, dict):
        raise CardError("invalid_input", "Values must be a record.")
    record = ctx.store.insert(table, values)
    return {"record": record}


@card(
    "Read Record By ID", category=CATEGORY, group=GROUP,
    inputs=["id"], outputs=["record"],
    effects=["reads_store"],
    examples=[
        {"label": "record found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}, {"name": "Nut"}]},
         "args": {"id": 2, "table": "items"},
         "expect": {"record": {"id": 2, "name": "Nut"}}},
        {"label": "include archived record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items", "include_archived": True},
         "expect": {"record": {"id": 1, "name": "Bolt"}}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "table": "items"}, "code": "not_found"},
        {"label": "table does not exist",
         "args": {"id": 1, "table": "missing"}, "code": "no_such_table"},
    ],
)
def read_record_by_id(ctx, *, id, table: str = "records", include_archived: bool = False) -> dict:
    """Retrieves one record from a table using its unique identifier."""
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    record = ctx.store.get(table, rec_id)
    if record is None:
        raise CardError("not_found", f"Record {rec_id} not found in {table}.")
    if record.get("_archived") and not include_archived:
        raise CardError("not_found", f"Record {rec_id} not found in {table}.")
    return {"record": record}


@card(
    "Update Existing Record", category=CATEGORY, group=GROUP,
    inputs=["id", "changes"], outputs=["record"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "update one field",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"name": "Bolt", "qty": 10}]},
         "args": {"id": 1, "changes": {"qty": 15}, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Bolt", "qty": 15}}},
        {"label": "update multiple fields",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"name": "Bolt", "qty": 10}]},
         "args": {"id": 1, "changes": {"name": "Screw", "qty": 20}, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Screw", "qty": 20}}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "changes": {"name": "New"}, "table": "items"}, "code": "not_found"},
        {"label": "changes not a record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "changes": "invalid", "table": "items"}, "code": "invalid_input"},
    ],
)
def update_existing_record(ctx, *, id, changes, table: str = "records", expected_version: int | None = None) -> dict:
    """Changes field values in a record the user selects or identifies."""
    if not isinstance(changes, dict):
        raise CardError("invalid_input", "Changes must be a record.")
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    record = ctx.store.update(table, rec_id, changes, expected_version=expected_version)
    return {"record": record}


@card(
    "Delete Record", category=CATEGORY, group=GROUP,
    inputs=["id"], outputs=["record"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "delete record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}, {"name": "Nut"}]},
         "args": {"id": 1, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Bolt"}},
         "expect_rows": {"items": [{"id": 2}]}},
        {"label": "only the chosen record goes",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "A"}, {"name": "B"}, {"name": "C"}]},
         "args": {"id": 2, "table": "items"},
         "expect": {"record": {"id": 2, "name": "B"}},
         "expect_rows": {"items": [{"id": 1}, {"id": 3}]}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "table": "items"}, "code": "not_found"},
        {"label": "table does not exist",
         "args": {"id": 1, "table": "missing"}, "code": "no_such_table"},
    ],
)
def delete_record(ctx, *, id, table: str = "records") -> dict:
    """Removes a record from the table permanently; a record other records still point to is refused."""
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    record = ctx.store.delete(table, rec_id)
    return {"record": record}


@card(
    "Create Multiple Records", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["records", "count"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "insert three records",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"records": [{"name": "Bolt"}, {"name": "Nut"}, {"name": "Screw"}], "table": "items"},
         "expect": {"count": 3, "records": [{"id": 1, "name": "Bolt"}, {"id": 2, "name": "Nut"}, {"id": 3, "name": "Screw"}]}},
        {"label": "empty list does nothing",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"records": [], "table": "items"},
         "expect": {"count": 0, "records": []},
         "expect_rows": {"items": []}},
    ],
    invalid=[
        {"label": "one record fails, none inserted",
         "tables": {"items": [{"name": "name", "type": "text", "required": True}]},
         "args": {"records": [{"name": "Bolt"}, {}], "table": "items"}, "code": "required",
         "expect_rows": {"items": []}},
        {"label": "records not a list",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"records": "invalid", "table": "items"}, "code": "invalid_input"},
    ],
)
def create_multiple_records(ctx, *, records, table: str = "records", limit: int = MAX_LOOP_ITEMS) -> dict:
    """Adds several records to a table at once from a list or imported data."""
    if not isinstance(records, (list, tuple)):
        raise CardError("invalid_input", "Records must be a list.")
    items = bounded(records, limit, "records")
    inserted = ctx.store.insert_many(table, items)
    return {"records": inserted, "count": len(inserted)}


@card(
    "Create Or Update Record", category=CATEGORY, group=GROUP,
    inputs=["values"], outputs=["record", "created"],
    effects=["writes_store"], idempotent=True,
    examples=[
        {"label": "creates new record when key not found",
         "tables": {"items": [{"name": "code", "type": "text", "unique": True}, {"name": "qty", "type": "integer"}]},
         "args": {"values": {"code": "A1", "qty": 10}, "table": "items", "key_field": "code"},
         "expect": {"record": {"id": 1, "code": "A1", "qty": 10}, "created": True}},
        {"label": "updates existing record when key matches",
         "tables": {"items": [{"name": "code", "type": "text", "unique": True}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"code": "A1", "qty": 10}]},
         "args": {"values": {"code": "A1", "qty": 15}, "table": "items", "key_field": "code"},
         "expect": {"record": {"id": 1, "code": "A1", "qty": 15}, "created": False}},
    ],
    invalid=[
        {"label": "key field missing from values",
         "tables": {"items": [{"name": "code", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "args": {"values": {"qty": 10}, "table": "items", "key_field": "code"}, "code": "missing_field"},
        {"label": "values not a record",
         "tables": {"items": [{"name": "code", "type": "text"}]},
         "args": {"values": "invalid", "table": "items", "key_field": "code"}, "code": "invalid_input"},
    ],
)
def create_or_update_record(ctx, *, values, table: str = "records", key_field: str = "id") -> dict:
    """Creates a record if no saved record has the same key value, or updates that record if one does."""
    if not isinstance(values, dict):
        raise CardError("invalid_input", "Values must be a record.")
    if key_field not in values:
        raise CardError("missing_field", f"Key field '{key_field}' not found in values.", {"field": key_field})
    key_value = values[key_field]
    existing = ctx.store.find(table, where={"field": key_field, "op": "eq", "value": key_value}, limit=1)
    if existing:
        record = ctx.store.update(table, existing[0]["id"], values)
        return {"record": record, "created": False}
    record = ctx.store.insert(table, values)
    return {"record": record, "created": True}


@card(
    "Archive Or Restore Record", category=CATEGORY, group=GROUP,
    inputs=["id"], outputs=["record"],
    effects=["writes_store"], idempotent=True,
    examples=[
        {"label": "archive active record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items"},
         "expect": {"record": {"id": 1, "name": "Bolt", "_archived": True}}},
        {"label": "archiving archived record is idempotent",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items"},
         "expect": {"record": {"id": 1, "_archived": True}}},
        {"label": "restore archived record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items", "action": "restore"},
         "expect": {"record": {"id": 1, "name": "Bolt", "_archived": False}}},
        {"label": "restoring active record is idempotent",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items", "action": "restore"},
         "expect": {"record": {"id": 1, "_archived": False}}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "table": "items"}, "code": "not_found"},
        {"label": "table does not exist",
         "args": {"id": 1, "table": "missing"}, "code": "no_such_table"},
        {"label": "unknown action",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 1, "table": "items", "action": "burn"}, "code": "invalid_input"},
    ],
)
def archive_or_restore_record(ctx, *, id, table: str = "records", action: str = "archive") -> dict:
    """Moves a record to inactive status without deleting it, or returns an archived record to active status."""
    if action not in ("archive", "restore"):
        raise CardError("invalid_input", f"Unknown action: {action}. Use archive or restore.")
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    record = ctx.store.set_archived(table, rec_id, action == "archive")
    return {"record": record}


@card(
    "Copy Record", category=CATEGORY, group=GROUP,
    inputs=["id"], outputs=["record"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "copy record",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"name": "Bolt", "qty": 10}]},
         "args": {"id": 1, "table": "items"},
         "expect": {"record": {"id": 2, "name": "Bolt", "qty": 10}}},
        {"label": "copy with field changes",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"name": "Bolt", "qty": 10}]},
         "args": {"id": 1, "changes": {"name": "Screw"}, "table": "items"},
         "expect": {"record": {"id": 2, "name": "Screw", "qty": 10}}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "table": "items"}, "code": "not_found"},
        {"label": "changes not a record",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "changes": "invalid", "table": "items"}, "code": "invalid_input"},
    ],
)
def copy_record(ctx, *, id, table: str = "records", changes: dict | None = None) -> dict:
    """Creates a new record by copying an existing one, so the user can change a few fields."""
    if changes is not None and not isinstance(changes, dict):
        raise CardError("invalid_input", "Changes must be a record.")
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    source = ctx.store.get(table, rec_id)
    if source is None:
        raise CardError("not_found", f"Record {rec_id} not found in {table}.")
    new_values = {k: v for k, v in source.items() if k not in ("id", "_version", "_created_at", "_updated_at", "_archived")}
    if changes:
        new_values.update(changes)
    record = ctx.store.insert(table, new_values)
    return {"record": record}


@card(
    "Update Field Across Records", category=CATEGORY, group=GROUP,
    inputs=["ids", "field", "value"], outputs=["count"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "update one field in three records",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "status", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt", "status": "pending"}, {"name": "Nut", "status": "pending"}, {"name": "Screw", "status": "shipped"}]},
         "args": {"ids": [1, 2], "field": "status", "value": "approved", "table": "items"},
         "expect": {"count": 2},
         "expect_rows": {"items": [{"id": 1, "status": "approved"}, {"id": 2, "status": "approved"}, {"id": 3, "status": "shipped"}]}},
        {"label": "empty list does nothing",
         "tables": {"items": [{"name": "status", "type": "text"}]},
         "args": {"ids": [], "field": "status", "value": "done", "table": "items"},
         "expect": {"count": 0}},
    ],
    invalid=[
        {"label": "ids not a list",
         "tables": {"items": [{"name": "status", "type": "text"}]},
         "args": {"ids": 1, "field": "status", "value": "done", "table": "items"}, "code": "invalid_input"},
        {"label": "field name empty",
         "tables": {"items": [{"name": "status", "type": "text"}]},
         "rows": {"items": [{"status": "pending"}]},
         "args": {"ids": [1], "field": "", "value": "done", "table": "items"}, "code": "invalid_input"},
    ],
)
def update_field_across_records(ctx, *, ids, field, value, table: str = "records", limit: int = MAX_LOOP_ITEMS) -> dict:
    """Changes one field to a new value in several selected or filtered records at once."""
    if not isinstance(ids, (list, tuple)):
        raise CardError("invalid_input", "IDs must be a list.")
    if not isinstance(field, str) or not field.strip():
        raise CardError("invalid_input", "Field must be a non-empty text.")
    id_list = bounded(ids, limit, "records")
    count = 0
    with ctx.store.transaction():   # all or nothing: one bad id or value stops the whole change
        for rec_id in id_list:
            try:
                rid = int(rec_id)
            except (TypeError, ValueError):
                raise CardError("invalid_input", f"{rec_id!r} is not a record id.") from None
            ctx.store.update(table, rid, {field: value})
            count += 1
    return {"count": count}


@card(
    "Delete Multiple Records", category=CATEGORY, group=GROUP,
    inputs=["ids"], outputs=["count"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "delete three records",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}, {"name": "Nut"}, {"name": "Screw"}]},
         "args": {"ids": [1, 3], "table": "items"},
         "expect": {"count": 2},
         "expect_rows": {"items": [{"id": 2}]}},
        {"label": "empty list does nothing",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"ids": [], "table": "items"},
         "expect": {"count": 0}},
    ],
    invalid=[
        {"label": "ids not a list",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"ids": 1, "table": "items"}, "code": "invalid_input"},
        {"label": "table does not exist",
         "args": {"ids": [1], "table": "missing"}, "code": "no_such_table"},
    ],
)
def delete_multiple_records(ctx, *, ids, table: str = "records", limit: int = MAX_LOOP_ITEMS) -> dict:
    """Removes several selected or filtered records at once after a confirmation."""
    if not isinstance(ids, (list, tuple)):
        raise CardError("invalid_input", "IDs must be a list.")
    id_list = bounded(ids, limit, "records")
    ctx.store.schema(table)  # raises no_such_table when the table is missing
    count = 0
    with ctx.store.transaction():   # all or nothing: a protected record stops the whole delete
        for rec_id in id_list:
            try:
                ctx.store.delete(table, int(rec_id))
                count += 1
            except CardError as err:
                if err.code != "not_found":   # an id that is already gone is not an error
                    raise
    return {"count": count}


@card(
    "Restore Previous Record Version", category=CATEGORY, group=GROUP,
    inputs=["id"], outputs=["record"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "restore to previous version",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "qty", "type": "integer"}]}, "history": {"items": 5},
         "rows": {"items": [{"name": "Bolt", "qty": 10}]},
         "args": {"id": 1, "table": "items", "version": 1},
         "expect": {"record": {"id": 1, "name": "Bolt", "qty": 10}}},
        {"label": "restoring the first version keeps its values",
         "tables": {"items": [{"name": "name", "type": "text"}]}, "history": {"items": 5},
         "rows": {"items": [{"name": "Original"}]},
         "args": {"id": 1, "table": "items", "version": 1},
         "expect": {"record": {"id": 1, "name": "Original"}}},
    ],
    invalid=[
        {"label": "record not found",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"id": 99, "table": "items", "version": 1}, "code": "not_found"},
        {"label": "nothing to go back to",
         "tables": {"items": [{"name": "name", "type": "text"}]}, "history": {"items": 5},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items"}, "code": "not_found"},
        {"label": "version not found",
         "tables": {"items": [{"name": "name", "type": "text"}]}, "history": {"items": 5},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"id": 1, "table": "items", "version": 999}, "code": "not_found"},
    ],
)
def restore_previous_record_version(ctx, *, id, table: str = "records", version: int | None = None) -> dict:
    """Puts a record back to an earlier kept version, such as how it was before its last saved change."""
    try:
        rec_id = int(id)
    except (TypeError, ValueError):
        raise CardError("invalid_input", "ID must be a number.") from None
    history = ctx.store.history(table, rec_id)
    if not history:
        raise CardError("not_found", f"No history found for record {rec_id} in {table}.")
    if version is None:
        # go back one step: the state before the latest change
        old_data = history[-1].get("before")
        if old_data is None:
            raise CardError("not_found", "There is no earlier version to go back to.")
    else:
        matches = [h for h in history if h["version"] == version]
        if not matches or matches[0].get("after") is None:
            raise CardError("not_found", f"Version {version} not found for record {rec_id}.")
        old_data = matches[0]["after"]
    restore_values = {k: v for k, v in old_data.items() if k not in ("id", "_version", "_created_at", "_updated_at", "_archived")}
    record = ctx.store.update(table, rec_id, restore_values)
    return {"record": record}
