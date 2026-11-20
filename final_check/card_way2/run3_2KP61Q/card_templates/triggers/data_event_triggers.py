"""Data Event Triggers (Triggers / Orchestration). Watches for saved data changes during preview."""
from __future__ import annotations

from ..runtime import CardError, bounded, card

CATEGORY = "Triggers / Orchestration"
GROUP = "Data Event Triggers"


@card(
    "Run When Record Created", category=CATEGORY, group=GROUP,
    inputs=["table"], outputs=["fire", "event", "record", "last_seen_id"],
    role="trigger", effects=["reads_store"],
    examples=[
        {"label": "new record triggers flow",
         "tables": {"orders": [{"name": "status", "type": "text"}]},
         "rows": {"orders": [{"status": "new"}]},
         "args": {"table": "orders", "last_checked_id": None},
         "expect": {"fire": True, "event": {"kind": "record_created", "table": "orders", "id": 1},
                    "record": {"id": 1}, "last_seen_id": 1}},
        {"label": "no new records",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"table": "items", "last_checked_id": 1},
         "expect": {"fire": False, "event": None, "record": None, "last_seen_id": 1}},
        {"label": "several new records come out one at a time, oldest first",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "A"}, {"name": "B"}, {"name": "C"}]},
         "args": {"table": "items", "last_checked_id": 1},
         "expect": {"fire": True, "record": {"id": 2, "name": "B"}, "last_seen_id": 2}},
        {"label": "empty table",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"table": "items"},
         "expect": {"fire": False, "last_seen_id": None}},
    ],
    invalid=[
        {"label": "table does not exist",
         "args": {"table": "missing"}, "code": "no_such_table"},
        {"label": "not in preview",
         "tables": {"orders": [{"name": "status", "type": "text"}]},
         "args": {"table": "orders"}, "preview": False, "code": "preview_only"},
    ],
)
def run_when_record_created(ctx, *, table: str, last_checked_id: int | None = None) -> dict:
    """Starts a flow when a new record is added while the app preview is running."""
    ctx.require_preview()
    ctx.store.schema(table)  # raises no_such_table when the table is missing
    # One event at a time: the oldest record newer than the last one handled. The engine
    # passes ``last_seen_id`` back as ``last_checked_id``, so the next call gives the next record.
    where = None if last_checked_id is None else {"field": "id", "op": "gt", "value": last_checked_id}
    found = ctx.store.find(table, where=where, order_by="id", limit=1, include_archived=True)
    if not found:
        return {"fire": False, "event": None, "record": None, "last_seen_id": last_checked_id}
    record = found[0]
    return {
        "fire": True,
        "event": {"kind": "record_created", "table": table, "id": record["id"]},
        "record": record,
        "last_seen_id": record["id"],
    }


@card(
    "Run When Record Changed", category=CATEGORY, group=GROUP,
    inputs=["table"], outputs=["fire", "event", "record", "before", "after"],
    role="trigger", effects=["reads_store"],
    examples=[
        {"label": "updated record triggers flow",
         "tables": {"items": [{"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"qty": 5}]},
         "args": {"table": "items", "record_id": 1, "last_version": 1},
         "expect": {"fire": False}},
        {"label": "version changed",
         "tables": {"orders": [{"name": "status", "type": "text"}]},
         "rows": {"orders": [{"status": "pending"}]},
         "args": {"table": "orders", "record_id": 1, "last_version": 0},
         "expect": {"fire": True, "record": {"id": 1, "status": "pending", "_version": 1}}},
    ],
    invalid=[
        {"label": "table missing",
         "args": {"table": "none", "record_id": 1}, "code": "no_such_table"},
        {"label": "not preview",
         "tables": {"items": [{"name": "qty", "type": "integer"}]},
         "args": {"table": "items", "record_id": 1}, "preview": False, "code": "preview_only"},
    ],
)
def run_when_record_changed(ctx, *, table: str, record_id: int, last_version: int | None = None,
                           watch_fields: list[str] | None = None) -> dict:
    """Starts a flow when an existing record is updated while the app preview is running."""
    ctx.require_preview()
    if not ctx.store.schema(table):
        raise CardError("no_such_table", f"Table {table} does not exist.")
    
    record = ctx.store.get(table, record_id)
    if not record:
        return {"fire": False, "event": None, "record": None, "before": None, "after": None}
    
    current_version = record["_version"]
    if last_version is not None and current_version <= last_version:
        return {"fire": False, "event": None, "record": None, "before": None, "after": None}
    
    # Get history to find what changed
    history = ctx.store.history(table, record_id)
    before = history[-1]["before"] if history and history[-1].get("before") else {}
    after = record
    
    # If watching specific fields, check if any changed
    if watch_fields and not ctx.store.schema(table).get("history"):
        raise CardError("history_required", "Watching fields needs change history to be enabled for the table.")
    if watch_fields:
        changed = any(before.get(f) != after.get(f) for f in watch_fields)
        if not changed:
            return {"fire": False, "event": None, "record": None, "before": None, "after": None}
    
    return {
        "fire": True,
        "event": {"kind": "record_changed", "table": table, "id": record_id, "version": current_version},
        "record": record,
        "before": before,
        "after": after,
    }


@card(
    "Run When Record Deleted", category=CATEGORY, group=GROUP,
    inputs=["table"], outputs=["fire", "event", "record"],
    role="trigger", effects=["reads_store"],
    examples=[
        {"label": "no deletion detected",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}]},
         "args": {"table": "items", "tracked_ids": [1]},
         "expect": {"fire": False, "event": None, "record": None}},
        {"label": "archived record found",
         "tables": {"orders": [{"name": "ref", "type": "text"}]},
         "rows": {"orders": []},
         "args": {"table": "orders", "tracked_ids": []},
         "expect": {"fire": False}},
    ],
    invalid=[
        {"label": "table not found",
         "args": {"table": "missing", "tracked_ids": []}, "code": "no_such_table"},
        {"label": "requires preview",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"table": "items", "tracked_ids": []}, "preview": False, "code": "preview_only"},
    ],
)
def run_when_record_deleted(ctx, *, table: str, tracked_ids: list[int]) -> dict:
    """Starts a flow when a record is removed while the app preview is running."""
    ctx.require_preview()
    if not ctx.store.schema(table):
        raise CardError("no_such_table", f"Table {table} does not exist.")
    
    # Check if any tracked id no longer exists or is archived
    for rid in bounded(tracked_ids, what="tracked ids"):
        record = ctx.store.get(table, rid)
        if not record or record.get("_archived"):
            # Found a deleted/archived record; get its last known state from history
            history = ctx.store.history(table, rid)
            last_state = history[-1]["before"] if history and history[-1].get("before") else {"id": rid}
            return {
                "fire": True,
                "event": {"kind": "record_deleted", "table": table, "id": rid},
                "record": last_state,
            }
    
    return {"fire": False, "event": None, "record": None}


@card(
    "Run When Value Crosses Threshold", category=CATEGORY, group=GROUP,
    inputs=["table", "record_id"], outputs=["fire", "event", "value", "crossed"],
    role="trigger", effects=["reads_store"],
    examples=[
        {"label": "value above threshold",
         "tables": {"stock": [{"name": "qty", "type": "integer"}]},
         "rows": {"stock": [{"qty": 15}]},
         "args": {"table": "stock", "record_id": 1, "field": "qty", "threshold": 10, "direction": "above"},
         "expect": {"fire": True, "value": 15, "crossed": "above"}},
        {"label": "no crossing",
         "tables": {"stock": [{"name": "qty", "type": "integer"}]},
         "rows": {"stock": [{"qty": 8}]},
         "args": {"table": "stock", "record_id": 1, "field": "qty", "threshold": 10, "direction": "above",
                  "last_value": 7},
         "expect": {"fire": False, "value": 8}},
    ],
    invalid=[
        {"label": "table missing",
         "args": {"table": "none", "record_id": 1, "field": "qty", "threshold": 10}, "code": "no_such_table"},
        {"label": "not preview",
         "tables": {"stock": [{"name": "qty", "type": "integer"}]},
         "args": {"table": "stock", "record_id": 1, "field": "qty", "threshold": 10},
         "preview": False, "code": "preview_only"},
    ],
)
def run_when_value_crosses_threshold(ctx, *, table: str, record_id: int, field: str, threshold: float,
                                    direction: str = "below", last_value: float | None = None) -> dict:
    """Starts a flow when a numeric field goes above or below a limit while the app preview is running."""
    ctx.require_preview()
    if not ctx.store.schema(table):
        raise CardError("no_such_table", f"Table {table} does not exist.")
    if direction not in ("above", "below"):
        raise CardError("invalid_input", "Direction must be 'above' or 'below'.")
    
    record = ctx.store.get(table, record_id)
    if not record:
        return {"fire": False, "event": None, "value": None, "crossed": None}
    
    from ..runtime import get_field, try_number
    current = try_number(get_field(record, field))
    if current is None:
        return {"fire": False, "event": None, "value": None, "crossed": None}
    
    # Determine if crossing happened
    crossed = False
    if direction == "below":
        if current < threshold:
            if last_value is None or last_value >= threshold:
                crossed = True
    else:  # above
        if current > threshold:
            if last_value is None or last_value <= threshold:
                crossed = True
    
    if crossed:
        return {
            "fire": True,
            "event": {"kind": "threshold_crossed", "table": table, "id": record_id,
                     "field": field, "threshold": threshold, "direction": direction},
            "value": current,
            "crossed": direction,
        }
    
    return {"fire": False, "event": None, "value": current, "crossed": None}
