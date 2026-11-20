"""Interactive Controls (UI / Interface). User-triggered actions and feedback components."""
from __future__ import annotations

from ..runtime import CardError, card, coerce_value, view

CATEGORY = "UI / Interface"
GROUP = "Interactive Controls"


@card(
    "Click Button", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "primary action button",
         "args": {"label": "Save Order", "variant": "primary"},
         "expect": {"view": {"kind": "action.button", "props": {"label": "Save Order", "variant": "primary"}}}},
        {"label": "secondary button with icon",
         "args": {"label": "Cancel", "variant": "secondary", "icon": "x"},
         "expect": {"view": {"kind": "action.button", "props": {"icon": "x"}}}},
    ],
    invalid=[
        {"label": "empty label", "args": {"label": ""}, "code": "required"},
    ],
)
def click_button(ctx, *, label: str = "", variant: str = "primary", icon: str = "", 
                 disabled: bool = False, name: str = "action") -> dict:
    """Triggers an action when the user clicks the labeled button."""
    if not label.strip():
        raise CardError("required", "Button needs a label.")
    node = view("action.button", id=name, label=label, variant=variant, icon=icon, disabled=disabled)
    return {"view": node}


@card(
    "Switch Toggle", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    role="view", effects=["view"],
    examples=[
        {"label": "toggle off initially",
         "args": {"value": False, "label": "Enable notifications"},
         "expect": {"view": {"kind": "input.toggle", "props": {"label": "Enable notifications"}}, "value": False}},
        {"label": "toggle on",
         "args": {"value": True, "name": "active"},
         "expect": {"view": {"id": "active"}, "value": True}},
        {"label": "text converted to bool",
         "args": {"value": "yes", "label": "Active"},
         "expect": {"value": True}},
    ],
    invalid=[
        {"label": "invalid bool text", "args": {"value": "maybe"}, "code": "not_a_bool"},
    ],
)
def switch_toggle(ctx, *, value=None, label: str = "Toggle", name: str = "toggle",
                  disabled: bool = False) -> dict:
    """Lets the user turn a setting on or off with a sliding switch."""
    spec = {"type": "bool"}
    clean = coerce_value(spec, value, label)
    node = view("input.toggle", id=name, label=label, value=clean, disabled=disabled)
    return {"view": node, "value": clean}


@card(
    "Adjust Slider", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    role="view", effects=["view"],
    examples=[
        {"label": "slider with range",
         "args": {"value": 50, "min_value": 0, "max_value": 100, "label": "Volume"},
         "expect": {"view": {"kind": "input.slider", "props": {"min": 0, "max": 100}}, "value": 50}},
        {"label": "slider with step",
         "args": {"value": 2.5, "min_value": 0, "max_value": 5, "step": 0.5},
         "expect": {"value": 2.5}},
        {"label": "value clamped to range",
         "args": {"value": 150, "min_value": 0, "max_value": 100},
         "expect": {"value": 100}},
    ],
    invalid=[
        {"label": "not a number", "args": {"value": "high"}, "code": "not_a_number"},
        {"label": "min greater than max", "args": {"min_value": 100, "max_value": 0}, "code": "invalid_input"},
    ],
)
def adjust_slider(ctx, *, value=None, label: str = "Value", name: str = "slider",
                  min_value: int | float = 0, max_value: int | float = 100, step: int | float = 1) -> dict:
    """Lets the user pick a value by dragging a handle along a range."""
    low, high = min_value, max_value
    if low >= high:
        raise CardError("invalid_input", "Slider min_value must be less than max_value.")
    clean = coerce_value({"type": "number"}, value, label)
    if clean is not None:
        clean = low if clean < low else high if clean > high else clean  # keep inside the range
    node = view("input.slider", id=name, label=label, value=clean, min=low, max=high, step=step)
    return {"view": node, "value": clean}


@card(
    "Choose File", category=CATEGORY, group=GROUP,
    inputs=["filename"], outputs=["view", "filename"],
    role="view", effects=["view"],
    examples=[
        {"label": "file picker for CSV",
         "args": {"accept": ".csv", "label": "Upload inventory"},
         "expect": {"view": {"kind": "input.file", "props": {"accept": ".csv"}}, "filename": None}},
        {"label": "file selected",
         "args": {"filename": "data.csv", "accept": ".csv,.xlsx"},
         "expect": {"filename": "data.csv"}},
    ],
    invalid=[
        {"label": "filename not text", "args": {"filename": 123}, "code": "invalid_input"},
    ],
)
def choose_file(ctx, *, filename=None, label: str = "Choose file", name: str = "file",
                accept: str = "", multiple: bool = False) -> dict:
    """Lets the user browse and select a local file for upload or reading."""
    clean = None
    if filename is not None:
        if not isinstance(filename, str):
            raise CardError("invalid_input", "Filename must be text.")
        clean = filename.strip() if filename.strip() else None
    node = view("input.file", id=name, label=label, accept=accept, multiple=multiple, value=clean)
    return {"view": node, "filename": clean}


@card(
    "Confirm Action", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "delete confirmation",
         "args": {"message": "Delete this record?", "title": "Confirm Delete"},
         "expect": {"view": {"kind": "dialog.confirm", "props": {"message": "Delete this record?"}}}},
        {"label": "custom button labels",
         "args": {"message": "Save changes?", "confirm_label": "Yes", "cancel_label": "No"},
         "expect": {"view": {"props": {"confirm_label": "Yes", "cancel_label": "No"}}}},
    ],
    invalid=[
        {"label": "empty message", "args": {"message": ""}, "code": "required"},
    ],
)
def confirm_action(ctx, *, message: str = "", title: str = "Confirm", 
                   confirm_label: str = "Confirm", cancel_label: str = "Cancel") -> dict:
    """Asks the user to approve or cancel before proceeding with an action."""
    if not message.strip():
        raise CardError("required", "Confirmation needs a message.")
    node = view("dialog.confirm", title=title, message=message, 
                confirm_label=confirm_label, cancel_label=cancel_label)
    return {"view": node}


@card(
    "Show Message Banner", category=CATEGORY, group=GROUP,
    inputs=["message"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "success message",
         "args": {"message": "Order saved", "variant": "success"},
         "expect": {"view": {"kind": "display.banner", "props": {"message": "Order saved", "variant": "success"}}}},
        {"label": "error with dismissible",
         "args": {"message": "Failed to load", "variant": "error", "dismissible": True},
         "expect": {"view": {"props": {"variant": "error", "dismissible": True}}}},
        {"label": "warning banner",
         "args": {"message": "Stock is low", "variant": "warning"},
         "expect": {"view": {"props": {"variant": "warning"}}}},
    ],
    invalid=[
        {"label": "empty message", "args": {"message": ""}, "code": "required"},
    ],
)
def show_message_banner(ctx, *, message, variant: str = "info", 
                        dismissible: bool = True, icon: str = "") -> dict:
    """Displays a dismissible notice with success warning or error styling."""
    if not isinstance(message, str):
        message = str(message)
    if not message.strip():
        raise CardError("required", "Banner needs a message.")
    if variant not in ("success", "info", "warning", "error"):
        variant = "info"
    node = view("display.banner", message=message, variant=variant, dismissible=dismissible, icon=icon)
    return {"view": node}


@card(
    "Show Progress While Running", category=CATEGORY, group=GROUP,
    inputs=["current", "total"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "progress bar halfway",
         "args": {"current": 50, "total": 100, "label": "Importing records"},
         "expect": {"view": {"kind": "display.progress", "props": {"current": 50, "total": 100}}}},
        {"label": "indeterminate spinner",
         "args": {"label": "Processing..."},
         "expect": {"view": {"props": {"current": None, "total": None}}}},
        {"label": "completed progress",
         "args": {"current": 100, "total": 100},
         "expect": {"view": {"props": {"current": 100, "total": 100}}}},
    ],
    invalid=[
        {"label": "current exceeds total", "args": {"current": 150, "total": 100}, "code": "invalid_input"},
    ],
)
def show_progress_while_running(ctx, *, current=None, total=None, 
                                label: str = "Loading...", show_percentage: bool = True) -> dict:
    """Displays a progress bar or spinner during a long running step like importing data."""
    if current is not None and total is not None:
        current = int(current)
        total = int(total)
        if current > total:
            raise CardError("invalid_input", "Progress current cannot exceed total.")
    node = view("display.progress", label=label, current=current, total=total, show_percentage=show_percentage)
    return {"view": node}
