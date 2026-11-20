"""Local Continuation (Integrations / Connectors). Cards that continue flows after outside actions complete."""
from __future__ import annotations

import json

from ..runtime import CardError, card

CATEGORY = "Integrations / Connectors"
GROUP = "Local Continuation"


@card(
    "Resume After Result", category=CATEGORY, group=GROUP,
    inputs=["result", "item"], outputs=["resumed", "data"],
    phase="human", role="flow", effects=["reads_store"],
    examples=[
        {"label": "resume with result data",
         "args": {"result": {"value": "REF123"}, "item": {"key": "order-1", "payload": {"product": "bolt"}}},
         "expect": {"resumed": True, "data": {"result": {"value": "REF123"}, "payload": {"product": "bolt"}}}},
        {"label": "resume with merged data",
         "args": {"result": {"status": "confirmed"}, "item": {"key": "task-1", "payload": {"user": "alice"}}},
         "expect": {"resumed": True, "data": {"result": {"status": "confirmed"}, "payload": {"user": "alice"}}}},
    ],
    invalid=[
        {"label": "result is not a dict", "args": {"result": "text", "item": {"key": "x"}},
         "code": "invalid_input"},
        {"label": "item missing key", "args": {"result": {}, "item": {}}, "code": "missing_field"},
    ],
)
def resume_after_result(ctx, *, result, item, merge_payload: bool = True) -> dict:
    """Continues the flow after a person enters a result from an outside action."""
    if not isinstance(result, dict):
        raise CardError("invalid_input", "Result must be a record.")
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item:
        raise CardError("missing_field", "Item must have a 'key' field.", {"fields": ["key"]})
    data = {"result": result}
    if merge_payload and "payload" in item:
        data["payload"] = item["payload"]
    return {"resumed": True, "data": data}


@card(
    "Mark Item Outcome", category=CATEGORY, group=GROUP,
    inputs=["item", "result"], outputs=["item"],
    phase="human", role="data", effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "mark item as done",
         "tables": {"outbox": [{"name": "key", "type": "text", "required": True},
                               {"name": "status", "type": "text", "required": True},
                               {"name": "result", "type": "text"}]},
         "rows": {"outbox": [{"key": "order-1", "status": "pending", "result": None}]},
         "args": {"item": {"key": "order-1"}, "result": {"value": "REF123"}, "outcome": "done",
                  "table": "outbox"},
         "expect": {"item": {"key": "order-1", "status": "done"}},
         "expect_rows": {"outbox": [{"key": "order-1", "status": "done"}]}},
        {"label": "mark item as failed",
         "tables": {"outbox": [{"name": "key", "type": "text"}, {"name": "status", "type": "text"}]},
         "rows": {"outbox": [{"key": "task-1", "status": "pending"}]},
         "args": {"item": {"key": "task-1"}, "result": {}, "outcome": "failed", "table": "outbox"},
         "expect": {"item": {"key": "task-1", "status": "failed"}},
         "expect_rows": {"outbox": [{"key": "task-1", "status": "failed"}]}},
    ],
    invalid=[
        {"label": "item missing key", "args": {"item": {}, "result": {}}, "code": "missing_field"},
        {"label": "invalid outcome", "args": {"item": {"key": "x"}, "result": {}, "outcome": "unknown"},
         "code": "not_allowed"},
    ],
)
def mark_item_outcome(ctx, *, item, result, outcome: str = "done",
                      table: str = "_vp_outbox", result_field: str = "result") -> dict:
    """Marks an item as done or failed based on the result a person entered."""
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item:
        raise CardError("missing_field", "Item must have a 'key' field.", {"fields": ["key"]})
    if outcome not in ("done", "failed"):
        raise CardError("not_allowed", "Outcome must be 'done' or 'failed'.", {"allowed": ["done", "failed"]})
    key = str(item["key"])
    # use outbox methods if using the built-in outbox table
    if table == "_vp_outbox":
        ctx.store.outbox_set(key, outcome, result)
        return {"item": ctx.store.outbox_get(key)}
    # otherwise update the custom table
    records = ctx.store.find(table, where={"field": "key", "op": "eq", "value": key}, limit=1)
    if not records:
        raise CardError("not_found", f"No item found with key '{key}'.", {"key": key})
    changes = {"status": outcome}
    if result_field in ctx.store.field_names(table):   # keep the result only if the table has a place for it
        changes[result_field] = result if isinstance(result, str) else json.dumps(result)
    updated = ctx.store.update(table, records[0]["id"], changes)
    return {"item": updated}


@card(
    "Log Outside Action", category=CATEGORY, group=GROUP,
    inputs=["item", "result"], outputs=["logged"],
    phase="human", role="data", effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "log completed action",
         "args": {"item": {"key": "order-1", "kind": "supplier_order"}, "result": {"ref": "REF123"}},
         "expect": {"logged": True}},
        {"label": "log failed action",
         "args": {"item": {"key": "task-1", "kind": "manual_task"}, "result": {}, "action": "failed"},
         "expect": {"logged": True}},
    ],
    invalid=[
        {"label": "item missing key", "args": {"item": {}, "result": {}}, "code": "missing_field"},
        {"label": "result not a dict", "args": {"item": {"key": "x"}, "result": "text"},
         "code": "invalid_input"},
    ],
)
def log_outside_action(ctx, *, item, result, action: str = "completed", details: dict = None) -> dict:
    """Records a history entry when a person completes an outside action."""
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item:
        raise CardError("missing_field", "Item must have a 'key' field.", {"fields": ["key"]})
    if not isinstance(result, dict):
        raise CardError("invalid_input", "Result must be a record.")
    import json
    kind = item.get("kind", "outside_action")
    message = f"{action.capitalize()} outside action for {item['key']}"
    log_details = details or {}
    log_details.update({"item_key": item["key"], "kind": kind, "result": result})
    ctx.store.log_event(kind, message, log_details)
    return {"logged": True}


@card(
    "Show Still Pending", category=CATEGORY, group=GROUP,
    inputs=["items"], outputs=["pending_items", "count"],
    phase="human", role="data", effects=["reads_store"],
    examples=[
        {"label": "filter pending from list",
         "args": {"items": [{"key": "o1", "status": "pending"}, {"key": "o2", "status": "done"},
                            {"key": "o3", "status": "pending"}]},
         "expect": {"pending_items": [{"key": "o1", "status": "pending"},
                                      {"key": "o3", "status": "pending"}], "count": 2}},
        {"label": "all items done",
         "args": {"items": [{"key": "t1", "status": "done"}]},
         "expect": {"pending_items": [], "count": 0}},
    ],
    invalid=[
        {"label": "items not a list", "args": {"items": "something"}, "code": "invalid_input"},
        {"label": "item missing status", "args": {"items": [{"key": "x"}], "require_status": True},
         "code": "missing_field"},
    ],
)
def show_still_pending(ctx, *, items, status_field: str = "status",
                       pending_value: str = "pending", require_status: bool = False) -> dict:
    """Displays items still waiting for a person to complete outside actions."""
    if not isinstance(items, (list, tuple)):
        raise CardError("invalid_input", "Items must be a list.")
    pending = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise CardError("invalid_input", f"Item {i + 1} must be a record.")
        if require_status and status_field not in item:
            raise CardError("missing_field", f"Item {i + 1} must have '{status_field}' field.",
                            {"fields": [status_field]})
        status = str(item.get(status_field, "")).strip().lower()
        if status == pending_value.lower():
            pending.append(item)
    return {"pending_items": pending, "count": len(pending)}
