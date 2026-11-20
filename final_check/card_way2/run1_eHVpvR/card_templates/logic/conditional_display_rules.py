"""Conditional Display Rules (Logic / Validation). Cards that control what appears on screen."""
from __future__ import annotations

from ..runtime import CardError, card, get_field, is_blank

CATEGORY = "Logic / Validation"
GROUP = "Conditional Display Rules"


@card(
    "Show Or Hide Field",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record", "visible"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "field value matches shows field",
         "args": {"record": {"status": "shipped", "tracking": "123"}, 
                  "depends_on_field": "status", "depends_on_value": "shipped"},
         "expect": {"record": {"status": "shipped", "tracking": "123"}, "visible": True}},
        {"label": "field value does not match hides field",
         "args": {"record": {"status": "pending", "tracking": ""}, 
                  "depends_on_field": "status", "depends_on_value": "shipped"},
         "expect": {"visible": False}},
        {"label": "field not empty shows field",
         "args": {"record": {"has_notes": True, "notes": "Call back"}, 
                  "depends_on_field": "has_notes", "show_when": "not_empty"},
         "expect": {"visible": True}},
        {"label": "field empty hides field",
         "args": {"record": {"notes": ""}, 
                  "depends_on_field": "notes", "show_when": "not_empty"},
         "expect": {"visible": False}},
    ],
    invalid=[
        {"label": "missing record",
         "args": {"record": None, "depends_on_field": "status"},
         "code": "invalid_input"},
    ],
)
def show_or_hide_field(ctx, *, record, depends_on_field: str, depends_on_value: str = None, 
                      show_when: str = "equals") -> dict:
    """Decides whether a field appears on screen based on another field or record state."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Show Or Hide Field needs a record.")
    
    value = get_field(record, depends_on_field)
    
    if show_when == "equals":
        visible = str(value).strip().lower() == str(depends_on_value).strip().lower() if depends_on_value else False
    elif show_when == "not_empty":
        visible = not is_blank(value)
    elif show_when == "empty":
        visible = is_blank(value)
    else:
        raise CardError("invalid_input", f"Unknown show_when value: {show_when}. Use 'equals', 'not_empty', or 'empty'.")
    
    return {"record": record, "visible": visible}


@card(
    "Enable Or Disable Field",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record", "enabled"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "editable status enables field",
         "args": {"record": {"status": "draft", "notes": "test"}, 
                  "depends_on_field": "status", "enable_when_value": "draft"},
         "expect": {"record": {"status": "draft", "notes": "test"}, "enabled": True}},
        {"label": "locked status disables field",
         "args": {"record": {"status": "approved", "notes": "test"}, 
                  "depends_on_field": "status", "enable_when_value": "draft"},
         "expect": {"enabled": False}},
        {"label": "multiple allowed values",
         "args": {"record": {"status": "pending"}, 
                  "depends_on_field": "status", "enable_when_value": ["draft", "pending"]},
         "expect": {"enabled": True}},
        {"label": "not in allowed values",
         "args": {"record": {"status": "shipped"}, 
                  "depends_on_field": "status", "enable_when_value": ["draft", "pending"]},
         "expect": {"enabled": False}},
    ],
    invalid=[
        {"label": "missing record",
         "args": {"record": None, "depends_on_field": "status"},
         "code": "invalid_input"},
    ],
)
def enable_or_disable_field(ctx, *, record, depends_on_field: str, 
                           enable_when_value: str | list = None) -> dict:
    """Controls whether a field can be edited depending on conditions like record status."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Enable Or Disable Field needs a record.")
    
    value = str(get_field(record, depends_on_field, "")).strip().lower()
    
    if enable_when_value is None:
        enabled = True
    elif isinstance(enable_when_value, list):
        enabled = any(value == str(v).strip().lower() for v in enable_when_value)
    else:
        enabled = value == str(enable_when_value).strip().lower()
    
    return {"record": record, "enabled": enabled}
