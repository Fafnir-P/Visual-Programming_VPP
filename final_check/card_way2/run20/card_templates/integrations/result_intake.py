"""Result Intake (Integrations / Connectors). Cards that accept and validate results from outside actions."""
from __future__ import annotations

from ..runtime import CardError, card, coerce_value, validate_against, view

CATEGORY = "Integrations / Connectors"
GROUP = "Result Intake"


@card(
    "Enter Outside Result", category=CATEGORY, group=GROUP,
    inputs=["item"], outputs=["view", "value"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "text result field",
         "args": {"item": {"key": "order-1"}, "field_type": "text", "field_label": "Reference number", "required": False},
         "expect": {"view": {"kind": "input.text", "props": {"label": "Reference number"}}, "value": None}},
        {"label": "number result with value",
         "args": {"item": {"key": "count-1"}, "field_type": "number", "value": 42.5},
         "expect": {"view": {"kind": "input.number"}, "value": 42.5}},
    ],
    invalid=[
        {"label": "invalid field type", "args": {"item": {"key": "x"}, "field_type": "unknown"}, "code": "bad_type"},
        {"label": "item is not a dict", "args": {"item": "something"}, "code": "invalid_input"},
    ],
)
def enter_outside_result(ctx, *, item, value=None, field_type: str = "text",
                         field_label: str = "Result", required: bool = True) -> dict:
    """Shows a form where a person types the result of an outside action, such as a reference number or confirmed quantity."""
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item:
        raise CardError("missing_field", "Item must have a 'key' field.", {"fields": ["key"]})
    spec = {"type": field_type, "required": required}
    clean = coerce_value(spec, value, field_label)
    kind_map = {"text": "input.text", "number": "input.number", "integer": "input.number",
                "date": "input.date", "datetime": "input.datetime", "email": "input.text",
                "phone": "input.text"}
    kind = kind_map.get(field_type, "input.text")
    props = {"label": field_label, "required": required, "value": clean, "item_key": str(item["key"])}
    if field_type == "integer":
        props["integer_only"] = True
    node = view(kind, props=props)
    return {"view": node, "value": clean}


@card(
    "Import Result File", category=CATEGORY, group=GROUP,
    inputs=["item"], outputs=["view", "content", "filename"],
    phase="human", role="view", effects=["view", "file_text_in"],
    examples=[
        {"label": "file picker for csv",
         "args": {"item": {"key": "import-1"}, "accepted_types": ["csv"]},
         "expect": {"view": {"kind": "input.file", "props": {"item_key": "import-1"}},
                    "content": None, "filename": None}},
        {"label": "file picker with content",
         "args": {"item": {"key": "import-2"}, "filename": "data.json", "content": '{"a":1}'},
         "expect": {"view": {"kind": "input.file"}, "content": '{"a":1}', "filename": "data.json"}},
    ],
    invalid=[
        {"label": "item missing key", "args": {"item": {}}, "code": "missing_field"},
        {"label": "accepted_types not a list", "args": {"item": {"key": "x"}, "accepted_types": "csv"},
         "code": "invalid_input"},
    ],
)
def import_result_file(ctx, *, item, filename=None, content=None,
                       accepted_types: list = None, label: str = "Upload result file") -> dict:
    """Lets a person pick and import a result file from an outside action."""
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item:
        raise CardError("missing_field", "Item must have a 'key' field.", {"fields": ["key"]})
    types = accepted_types or ["csv", "json", "txt"]
    if not isinstance(types, (list, tuple)):
        raise CardError("invalid_input", "Accepted types must be a list.")
    props = {"label": label, "accepted_types": list(types), "item_key": str(item["key"])}
    if filename is not None:
        props["filename"] = str(filename)
    node = view("input.file", props=props)
    return {"view": node, "content": content, "filename": filename}


@card(
    "Match Result To Item", category=CATEGORY, group=GROUP,
    inputs=["result", "items"], outputs=["matched_item", "result"],
    phase="human", role="data", effects=[],
    examples=[
        {"label": "result matches first item",
         "args": {"result": {"item_key": "order-1", "value": "REF123"},
                  "items": [{"key": "order-1", "kind": "order"}, {"key": "order-2", "kind": "order"}]},
         "expect": {"matched_item": {"key": "order-1", "kind": "order"}, "result": {"item_key": "order-1", "value": "REF123"}}},
        {"label": "result matches second item by key",
         "args": {"result": {"item_key": "task-2", "status": "done"},
                  "items": [{"key": "task-1"}, {"key": "task-2"}]},
         "expect": {"matched_item": {"key": "task-2"}, "result": {"item_key": "task-2", "status": "done"}}},
    ],
    invalid=[
        {"label": "no matching item", "args": {"result": {"item_key": "x"}, "items": [{"key": "y"}]},
         "code": "not_found"},
        {"label": "result missing item_key", "args": {"result": {"value": "x"}, "items": [{"key": "a"}]},
         "code": "missing_field"},
    ],
)
def match_result_to_item(ctx, *, result, items, key_field: str = "item_key") -> dict:
    """Matches a result entered by a person to the waiting item that triggered it."""
    if not isinstance(result, dict):
        raise CardError("invalid_input", "Result must be a record.")
    if key_field not in result:
        raise CardError("missing_field", f"Result must have a '{key_field}' field.", {"fields": [key_field]})
    if not isinstance(items, (list, tuple)):
        raise CardError("invalid_input", "Items must be a list.")
    target_key = str(result[key_field])
    matched = None
    for item in items:
        if isinstance(item, dict) and str(item.get("key")) == target_key:
            matched = item
            break
    if matched is None:
        raise CardError("not_found", f"No item found with key '{target_key}'.", {"key": target_key})
    return {"matched_item": matched, "result": result}


@card(
    "Reject Invalid Result", category=CATEGORY, group=GROUP,
    inputs=["result", "item"], outputs=["valid", "reason"],
    phase="human", role="data", effects=[],
    examples=[
        {"label": "result is fresh and valid",
         "args": {"result": {"item_key": "order-1", "value": "REF123", "entered_at": "2026-01-15T10:00:00"},
                  "item": {"key": "order-1", "created_at": "2026-01-15T09:00:00", "_version": 1}},
         "expect": {"valid": True, "reason": ""}},
        {"label": "result is stale",
         "args": {"result": {"item_key": "order-1", "value": "REF123", "item_version": 1},
                  "item": {"key": "order-1", "created_at": "2026-01-15T09:00:00", "_version": 2}},
         "expect": {"valid": False, "reason": "stale"}},
        {"label": "an unrelated later change does not make it stale",
         "args": {"result": {"item_key": "order-1", "value": "REF123", "item_version": 2},
                  "item": {"key": "order-1", "_version": 2}},
         "expect": {"valid": True, "reason": ""}},
        {"label": "result for another item",
         "args": {"result": {"item_key": "order-9", "value": "REF123"}, "item": {"key": "order-1"}},
         "expect": {"valid": False, "reason": "key_mismatch"}},
    ],
    invalid=[
        {"label": "result missing item_key", "args": {"result": {}, "item": {"key": "x"}},
         "code": "missing_field"},
        {"label": "item missing key", "args": {"result": {"item_key": "x"}, "item": {}},
         "code": "missing_field"},
    ],
)
def reject_invalid_result(ctx, *, result, item, max_age_hours: int = 24) -> dict:
    """Rejects a result entered by a person if it is for another item, built on an older version of the item, or too old."""
    if not isinstance(result, dict):
        raise CardError("invalid_input", "Result must be a record.")
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "item_key" not in result:
        raise CardError("missing_field", "Result must have 'item_key'.", {"fields": ["item_key"]})
    if "key" not in item:
        raise CardError("missing_field", "Item must have 'key'.", {"fields": ["key"]})
    if str(result["item_key"]) != str(item["key"]):
        return {"valid": False, "reason": "key_mismatch"}
    # stale = the item changed after the outside action began (the result says which version it was built on)
    built_on = result.get("item_version")
    if built_on is not None and item.get("_version") != built_on:
        return {"valid": False, "reason": "stale"}
    # check age if entered_at is present
    if "entered_at" in result and max_age_hours > 0:
        from ..runtime import to_datetime
        import datetime as dt
        entered = to_datetime(result["entered_at"])
        age = (ctx.now() - entered).total_seconds() / 3600
        if age > max_age_hours:
            return {"valid": False, "reason": "too_old"}
    return {"valid": True, "reason": ""}


@card(
    "Reconcile Stale Result", category=CATEGORY, group=GROUP,
    inputs=["result", "old_item", "current_item"], outputs=["view", "action"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "show differences",
         "args": {"result": {"value": "REF123"},
                  "old_item": {"key": "o1", "status": "pending", "_version": 1},
                  "current_item": {"key": "o1", "status": "cancelled", "_version": 2}},
         "expect": {"view": {"kind": "display.reconciliation",
                             "props": {"has_changes": True}}, "action": None}},
        {"label": "no changes, accept by default",
         "args": {"result": {"value": "REF123"},
                  "old_item": {"key": "o1", "status": "pending"},
                  "current_item": {"key": "o1", "status": "pending"}},
         "expect": {"view": {"kind": "display.reconciliation",
                             "props": {"has_changes": False}}, "action": None}},
    ],
    invalid=[
        {"label": "old_item missing key", "args": {"result": {}, "old_item": {}, "current_item": {"key": "x"}},
         "code": "missing_field"},
        {"label": "current_item not a dict", "args": {"result": {}, "old_item": {"key": "x"}, "current_item": "x"},
         "code": "invalid_input"},
    ],
)
def reconcile_stale_result(ctx, *, result, old_item, current_item, action=None) -> dict:
    """Shows what changed in a record since an outside action began, and lets the user accept or discard the result."""
    if not isinstance(result, dict):
        raise CardError("invalid_input", "Result must be a record.")
    if not isinstance(old_item, dict) or not isinstance(current_item, dict):
        raise CardError("invalid_input", "Both items must be records.")
    if "key" not in old_item or "key" not in current_item:
        raise CardError("missing_field", "Both items must have a 'key' field.", {"fields": ["key"]})
    # compare old and current
    changed_fields = []
    all_fields = set(old_item.keys()) | set(current_item.keys())
    for field in all_fields:
        if field.startswith("_"):
            continue
        if old_item.get(field) != current_item.get(field):
            changed_fields.append({"field": field, "old": old_item.get(field), "new": current_item.get(field)})
    has_changes = len(changed_fields) > 0
    props = {"has_changes": has_changes, "change_count": len(changed_fields),
             "old_version": old_item.get("_version", 1), "current_version": current_item.get("_version", 1)}
    node = view("display.reconciliation", props=props)
    return {"view": node, "action": action}
