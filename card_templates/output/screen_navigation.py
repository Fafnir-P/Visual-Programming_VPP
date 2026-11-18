"""Screen Navigation (Navigation / Output). Navigation between views and screens."""
from __future__ import annotations

from ..runtime import CardError, card, view

CATEGORY = "Navigation / Output"
GROUP = "Screen Navigation"


@card(
    "Open Detail Screen", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "open detail for record",
         "args": {"record": {"id": 1, "name": "Item A"}, "screen": "item_detail"},
         "expect": {"view": {"kind": "nav.detail", "props": {"screen": "item_detail"}}}},
        {"label": "detail with title",
         "args": {"record": {"id": 2, "name": "Order 1002"}, "screen": "order_detail", "title": "Order Details"},
         "expect": {"view": {"props": {"title": "Order Details"}}}},
    ],
    invalid=[
        {"label": "missing record", "args": {"screen": "detail"}, "code": "required"},
        {"label": "record not a dict", "args": {"record": "text", "screen": "detail"}, "code": "invalid_input"},
    ],
)
def open_detail_screen(ctx, *, record=None, screen: str = "detail", title: str = "") -> dict:
    """Displays the full record view when the user selects an item from a list."""
    if record is None:
        raise CardError("required", "Detail screen needs a record.")
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a record.")
    node = view("nav.detail", screen=screen, record=record, title=title)
    return {"view": node}


@card(
    "Go Back To List", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "back to default list",
         "args": {},
         "expect": {"view": {"kind": "nav.back", "props": {"screen": "list"}}}},
        {"label": "back to specific screen",
         "args": {"screen": "inventory_list", "label": "Back to Inventory"},
         "expect": {"view": {"props": {"screen": "inventory_list", "label": "Back to Inventory"}}}},
    ],
    invalid=[
        {"label": "empty screen name", "args": {"screen": ""}, "code": "invalid_input"},
    ],
)
def go_back_to_list(ctx, *, screen: str = "list", label: str = "Back") -> dict:
    """Returns the user to the previous list or overview screen."""
    if not screen.strip():
        raise CardError("invalid_input", "Screen name cannot be empty.")
    node = view("nav.back", screen=screen, label=label)
    return {"view": node}


@card(
    "Open Pop-Up Panel", category=CATEGORY, group=GROUP,
    inputs=["content"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "popup with title",
         "args": {"content": {"kind": "display.text", "props": {}, "children": []}, "title": "Quick Edit"},
         "expect": {"view": {"kind": "dialog.panel", "props": {"title": "Quick Edit"}}}},
        {"label": "popup with size",
         "args": {"content": {"kind": "layout.stack", "props": {}, "children": []}, "size": "large"},
         "expect": {"view": {"props": {"size": "large"}}}},
    ],
    invalid=[
        {"label": "missing content", "args": {"title": "Panel"}, "code": "required"},
        {"label": "content not a view", "args": {"content": "text"}, "code": "invalid_input"},
    ],
)
def open_pop_up_panel(ctx, *, content=None, title: str = "", size: str = "medium", 
                      dismissible: bool = True) -> dict:
    """Shows a temporary overlay window for quick edits or details without leaving the current screen."""
    if content is None:
        raise CardError("required", "Pop-up panel needs content.")
    if not isinstance(content, dict) or "kind" not in content:
        raise CardError("invalid_input", "Content must be a view node.")
    node = view("dialog.panel", title=title, size=size, dismissible=dismissible, children=[content])
    return {"view": node}
