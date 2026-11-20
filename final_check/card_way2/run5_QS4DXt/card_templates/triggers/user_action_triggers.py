"""User Action Triggers (Triggers / Orchestration). Cards that respond to user interactions."""
from __future__ import annotations

from ..runtime import CardError, card

CATEGORY = "Triggers / Orchestration"
GROUP = "User Action Triggers"


@card(
    "Run When Button Pressed",
    category=CATEGORY, group=GROUP,
    inputs=["pressed"], outputs=["fire", "event"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "button pressed fires event",
         "args": {"pressed": True, "button_id": "submit_order"},
         "expect": {"fire": True, "event": {"kind": "button_pressed", "button_id": "submit_order"}},
         "preview": True},
        {"label": "button not pressed does not fire",
         "args": {"pressed": False, "button_id": "submit_order"},
         "expect": {"fire": False},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview",
         "args": {"pressed": True, "button_id": "test"},
         "preview": False, "code": "preview_only"},
    ],
)
def run_when_button_pressed(ctx, *, pressed, button_id: str = "button", label: str = "Run") -> dict:
    """Starts a flow when the user clicks a button in the application interface."""
    ctx.require_preview()
    
    fire = bool(pressed)
    event = {"kind": "button_pressed", "button_id": button_id, "label": label} if fire else {}
    
    return {"fire": fire, "event": event}


@card(
    "Run When Form Submitted",
    category=CATEGORY, group=GROUP,
    inputs=["submitted", "values"], outputs=["fire", "event"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "form submitted fires event",
         "args": {"submitted": True, "values": {"name": "Bolt", "qty": 10}, "form_id": "new_item"},
         "expect": {"fire": True, "event": {"kind": "form_submitted", "form_id": "new_item", "values": {"name": "Bolt", "qty": 10}}},
         "preview": True},
        {"label": "form not submitted does not fire",
         "args": {"submitted": False, "values": {}, "form_id": "new_item"},
         "expect": {"fire": False},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview",
         "args": {"submitted": True, "values": {}},
         "preview": False, "code": "preview_only"},
    ],
)
def run_when_form_submitted(ctx, *, submitted, values, form_id: str = "form") -> dict:
    """Starts a flow when the user submits a form with input values."""
    ctx.require_preview()
    
    if not isinstance(values, dict):
        raise CardError("invalid_input", "Form values must be a record.")
    
    fire = bool(submitted)
    event = {"kind": "form_submitted", "form_id": form_id, "values": values} if fire else {}
    
    return {"fire": fire, "event": event}


@card(
    "Run When Page Opened",
    category=CATEGORY, group=GROUP,
    inputs=["opened"], outputs=["fire", "event"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "page opened fires event",
         "args": {"opened": True, "page_id": "dashboard"},
         "expect": {"fire": True, "event": {"kind": "page_opened", "page_id": "dashboard"}},
         "preview": True},
        {"label": "page not opened does not fire",
         "args": {"opened": False, "page_id": "dashboard"},
         "expect": {"fire": False},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview",
         "args": {"opened": True, "page_id": "test"},
         "preview": False, "code": "preview_only"},
    ],
)
def run_when_page_opened(ctx, *, opened, page_id: str = "page", title: str = "Page") -> dict:
    """Starts a flow when the user navigates to a specific page in the application."""
    ctx.require_preview()
    
    fire = bool(opened)
    event = {"kind": "page_opened", "page_id": page_id, "title": title} if fire else {}
    
    return {"fire": fire, "event": event}


@card(
    "Run When Record Selected",
    category=CATEGORY, group=GROUP,
    inputs=["selected", "record"], outputs=["fire", "event"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "record selected fires event",
         "args": {"selected": True, "record": {"id": 5, "name": "Bolt"}, "table": "items"},
         "expect": {"fire": True, "event": {"kind": "record_selected", "table": "items", "record": {"id": 5, "name": "Bolt"}}},
         "preview": True},
        {"label": "no record selected does not fire",
         "args": {"selected": False, "record": None, "table": "items"},
         "expect": {"fire": False},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview",
         "args": {"selected": True, "record": {"id": 1}},
         "preview": False, "code": "preview_only"},
    ],
)
def run_when_record_selected(ctx, *, selected, record, table: str = "records") -> dict:
    """Starts a flow when the user chooses a record from a list or table."""
    ctx.require_preview()
    
    fire = bool(selected) and record is not None
    event = {"kind": "record_selected", "table": table, "record": record} if fire else {}
    
    return {"fire": fire, "event": event}
