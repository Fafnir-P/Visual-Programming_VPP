"""Human Instructions (Integrations / Connectors). Cards that show instructions and items for people to act on outside the app."""
from __future__ import annotations

from ..runtime import CardError, card, view

CATEGORY = "Integrations / Connectors"
GROUP = "Human Instructions"


@card(
    "Show Manual Steps", category=CATEGORY, group=GROUP,
    inputs=["steps"], outputs=["view"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "list of three steps",
         "args": {"steps": ["Open supplier portal", "Enter order", "Copy reference number"],
                  "title": "Submit order to supplier"},
         "expect": {"view": {"kind": "display.instructions",
                             "props": {"title": "Submit order to supplier", "step_count": 3}}}},
        {"label": "single step with long title",
         "args": {"steps": ["Confirm receipt"], "title": "Receiving confirmation needed"},
         "expect": {"view": {"kind": "display.instructions",
                             "props": {"title": "Receiving confirmation needed", "step_count": 1}}}},
    ],
    invalid=[
        {"label": "empty steps list", "args": {"steps": []}, "code": "required"},
        {"label": "steps is not a list", "args": {"steps": "do something"}, "code": "invalid_input"},
    ],
)
def show_manual_steps(ctx, *, steps, title: str = "Follow these steps", icon: str = "info") -> dict:
    """Displays step-by-step instructions for a person to follow outside the app."""
    if not isinstance(steps, (list, tuple)):
        raise CardError("invalid_input", "Steps must be a list.")
    if not steps:
        raise CardError("required", "At least one step is required.")
    step_nodes = []
    for i, step in enumerate(steps, start=1):
        text = str(step).strip()
        if not text:
            raise CardError("invalid_input", f"Step {i} is empty.")
        step_nodes.append(view("display.text", props={"text": f"{i}. {text}"}))
    node = view("display.instructions", props={"title": title, "icon": icon, "step_count": len(step_nodes)},
                children=step_nodes)
    return {"view": node}


@card(
    "Show Copyable Text", category=CATEGORY, group=GROUP,
    inputs=["text"], outputs=["view"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "plain text value",
         "args": {"text": "REF-2026-00123", "label": "Reference number"},
         "expect": {"view": {"kind": "display.copyable",
                             "props": {"label": "Reference number", "char_count": 14}}}},
        {"label": "multi-line text",
         "args": {"text": "Line one\nLine two\nLine three"},
         "expect": {"view": {"kind": "display.copyable", "props": {"char_count": 28}}}},
    ],
    invalid=[
        {"label": "empty text", "args": {"text": ""}, "code": "required"},
        {"label": "text is None", "args": {"text": None}, "code": "required"},
    ],
)
def show_copyable_text(ctx, *, text, label: str = "Copy this text", monospace: bool = False) -> dict:
    """Displays text in a copyable block for a person to paste elsewhere."""
    if text is None or (isinstance(text, str) and not text.strip()):
        raise CardError("required", "Text is required.")
    content = str(text)
    node = view("display.copyable", props={"label": label, "text": content, "monospace": monospace,
                                           "char_count": len(content)})
    return {"view": node}


@card(
    "Show Action Checklist", category=CATEGORY, group=GROUP,
    inputs=["items"], outputs=["view"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "list of two items",
         "args": {"items": ["Email supplier", "Update tracking"],
                  "title": "Complete these actions"},
         "expect": {"view": {"kind": "display.checklist",
                             "props": {"title": "Complete these actions", "item_count": 2}}}},
        {"label": "single action with custom title",
         "args": {"items": ["Approve shipment"], "title": "Approval needed"},
         "expect": {"view": {"kind": "display.checklist",
                             "props": {"title": "Approval needed", "item_count": 1}}}},
    ],
    invalid=[
        {"label": "empty items list", "args": {"items": []}, "code": "required"},
        {"label": "items is not a list", "args": {"items": "something"}, "code": "invalid_input"},
    ],
)
def show_action_checklist(ctx, *, items, title: str = "Actions to complete", icon: str = "checkbox") -> dict:
    """Displays a checklist of tasks for a person to complete outside the app."""
    if not isinstance(items, (list, tuple)):
        raise CardError("invalid_input", "Items must be a list.")
    if not items:
        raise CardError("required", "At least one item is required.")
    item_nodes = []
    for i, item in enumerate(items, start=1):
        text = str(item).strip()
        if not text:
            raise CardError("invalid_input", f"Item {i} is empty.")
        item_nodes.append(view("display.text", props={"text": text}))
    node = view("display.checklist", props={"title": title, "icon": icon, "item_count": len(item_nodes)},
                children=item_nodes)
    return {"view": node}


@card(
    "Show Waiting Item", category=CATEGORY, group=GROUP,
    inputs=["item"], outputs=["view"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "item with all fields",
         "args": {"item": {"key": "order-123", "kind": "supplier_order", "created_at": "2026-01-15T09:00:00",
                           "instructions": "Submit via portal"}},
         "expect": {"view": {"kind": "display.waiting_item",
                             "props": {"key": "order-123", "kind": "supplier_order"}}}},
        {"label": "minimal item",
         "args": {"item": {"key": "task-1", "kind": "manual_task", "created_at": "2026-01-14T10:00:00"}},
         "expect": {"view": {"kind": "display.waiting_item",
                             "props": {"key": "task-1", "kind": "manual_task"}}}},
    ],
    invalid=[
        {"label": "missing key field", "args": {"item": {"kind": "order"}}, "code": "missing_field"},
        {"label": "item is not a dict", "args": {"item": "something"}, "code": "invalid_input"},
    ],
)
def show_waiting_item(ctx, *, item, show_instructions: bool = True) -> dict:
    """Displays an item paused until a person completes an outside action."""
    if not isinstance(item, dict):
        raise CardError("invalid_input", "Item must be a record.")
    if "key" not in item or "kind" not in item:
        raise CardError("missing_field", "Item must have 'key' and 'kind' fields.",
                        {"fields": ["key", "kind"]})
    props = {"key": str(item["key"]), "kind": str(item["kind"]),
             "created_at": item.get("created_at"), "show_instructions": show_instructions}
    if show_instructions and "instructions" in item:
        props["instructions"] = str(item["instructions"])
    node = view("display.waiting_item", props=props)
    return {"view": node}


@card(
    "Show Pending Reminder", category=CATEGORY, group=GROUP,
    inputs=["items"], outputs=["view"],
    phase="human", role="view", effects=["view"],
    examples=[
        {"label": "two pending items",
         "args": {"items": [{"key": "ord-1", "kind": "order"}, {"key": "ord-2", "kind": "order"}],
                  "message": "Orders waiting"},
         "expect": {"view": {"kind": "display.reminder",
                             "props": {"message": "Orders waiting", "pending_count": 2}}}},
        {"label": "single pending item",
         "args": {"items": [{"key": "task-1", "kind": "task"}]},
         "expect": {"view": {"kind": "display.reminder", "props": {"pending_count": 1}}}},
    ],
    invalid=[
        {"label": "empty items list", "args": {"items": []}, "code": "required"},
        {"label": "items is not a list", "args": {"items": {"key": "x"}}, "code": "invalid_input"},
    ],
)
def show_pending_reminder(ctx, *, items, message: str = "Actions pending", urgency: str = "normal") -> dict:
    """Displays a reminder of actions still waiting for a person to complete outside."""
    if not isinstance(items, (list, tuple)):
        raise CardError("invalid_input", "Items must be a list.")
    if not items:
        raise CardError("required", "At least one pending item is required.")
    for i, item in enumerate(items):
        if not isinstance(item, dict) or "key" not in item:
            raise CardError("invalid_input", f"Item {i + 1} must be a record with a 'key' field.")
    node = view("display.reminder", props={"message": message, "urgency": urgency,
                                           "pending_count": len(items)})
    return {"view": node}
