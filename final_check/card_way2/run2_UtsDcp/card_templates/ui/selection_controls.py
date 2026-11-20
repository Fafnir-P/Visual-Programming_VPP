"""Selection Controls (UI / Interface). Cards that let users pick from options."""
from __future__ import annotations

from ..runtime import CardError, card, coerce_value, view

CATEGORY = "UI / Interface"
GROUP = "Selection Controls"


@card(
    "Choose From Dropdown",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty dropdown", "args": {"label": "Status", "choices": ["pending", "shipped", "delivered"]}, 
         "expect": {"view": {"kind": "input.dropdown"}, "value": None}},
        {"label": "selected value", "args": {"value": "shipped", "choices": ["pending", "shipped", "delivered"]}, 
         "expect": {"value": "shipped"}},
        {"label": "case insensitive match", "args": {"value": "PENDING", "choices": ["pending", "shipped"]}, 
         "expect": {"value": "pending"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "choices": ["A", "B"], "required": True}, "code": "required"},
        {"label": "not in choices", "args": {"value": "unknown", "choices": ["A", "B"]}, "code": "not_allowed"},
    ],
)
def choose_from_dropdown(ctx, *, value=None, name: str = "dropdown", label: str = "Choose",
                         choices: list = None, required: bool = False, placeholder: str = "",
                         help_text: str = "") -> dict:
    """Lets the user pick one option from a collapsible list."""
    if not choices:
        choices = []
    spec = {"type": "choice", "required": required, "choices": choices}
    clean = coerce_value(spec, value, label)
    node = view("input.dropdown", id=name, label=label, value=clean, choices=choices,
                required=required, placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Select Multiple Options",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty selection", "args": {"label": "Features", "choices": ["wifi", "parking", "pool"]}, 
         "expect": {"view": {"kind": "input.multiselect"}, "value": None}},
        {"label": "multiple selected", "args": {"value": ["wifi", "pool"], "choices": ["wifi", "parking", "pool"]}, 
         "expect": {"value": ["wifi", "pool"]}},
        {"label": "respects min count", "args": {"value": ["A", "B"], "choices": ["A", "B", "C"], "min_selections": 1}, 
         "expect": {"value": ["A", "B"]}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": [], "choices": ["A", "B"], "required": True}, "code": "required"},
        {"label": "invalid choice", "args": {"value": ["unknown"], "choices": ["A", "B"]}, "code": "not_allowed"},
    ],
)
def select_multiple_options(ctx, *, value=None, name: str = "multiselect", label: str = "Select Multiple",
                            choices: list = None, required: bool = False, min_selections: int = None,
                            max_selections: int = None, help_text: str = "") -> dict:
    """Lets the user check multiple items from a displayed list."""
    if not choices:
        choices = []
    spec = {"type": "multichoice", "required": required, "choices": choices,
            "min_length": min_selections, "max_length": max_selections}
    clean = coerce_value(spec, value, label)
    node = view("input.multiselect", id=name, label=label, value=clean or [], choices=choices,
                required=required, minSelections=min_selections, maxSelections=max_selections, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Choose One Option",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty radio group", "args": {"label": "Priority", "choices": ["low", "medium", "high"]}, 
         "expect": {"view": {"kind": "input.radio"}, "value": None}},
        {"label": "selected option", "args": {"value": "high", "choices": ["low", "medium", "high"]}, 
         "expect": {"value": "high"}},
        {"label": "required selection", "args": {"value": "medium", "choices": ["low", "medium", "high"], "required": True}, 
         "expect": {"value": "medium"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "choices": ["A", "B"], "required": True}, "code": "required"},
        {"label": "not in choices", "args": {"value": "X", "choices": ["A", "B"]}, "code": "not_allowed"},
    ],
)
def choose_one_option(ctx, *, value=None, name: str = "radio", label: str = "Choose One",
                      choices: list = None, required: bool = False, help_text: str = "") -> dict:
    """Lets the user select exactly one choice from visible radio buttons."""
    if not choices:
        choices = []
    spec = {"type": "choice", "required": required, "choices": choices}
    clean = coerce_value(spec, value, label)
    node = view("input.radio", id=name, label=label, value=clean, choices=choices,
                required=required, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Toggle Checkbox",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "unchecked by default", "args": {"label": "Agree"}, 
         "expect": {"view": {"kind": "input.checkbox"}, "value": False}},
        {"label": "checked", "args": {"value": True, "label": "Active"}, 
         "expect": {"value": True}},
        {"label": "coerces yes to true", "args": {"value": "yes"}, 
         "expect": {"value": True}},
    ],
    invalid=[
        {"label": "invalid bool", "args": {"value": "maybe"}, "code": "not_a_bool"},
    ],
)
def toggle_checkbox(ctx, *, value=None, name: str = "checkbox", label: str = "Option",
                    help_text: str = "") -> dict:
    """Lets the user check or uncheck a single yes or no option."""
    spec = {"type": "bool"}
    clean = coerce_value(spec, value, label)
    if clean is None:
        clean = False
    node = view("input.checkbox", id=name, label=label, checked=clean, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Pick From Searchable List",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty search", "args": {"label": "City", "choices": ["New York", "Los Angeles", "Chicago"]}, 
         "expect": {"view": {"kind": "input.autocomplete"}, "value": None}},
        {"label": "selected from list", "args": {"value": "Chicago", "choices": ["New York", "Los Angeles", "Chicago"]}, 
         "expect": {"value": "Chicago"}},
        {"label": "many choices", "args": {"value": "A", "choices": ["A", "B", "C", "D", "E"]}, 
         "expect": {"value": "A"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "choices": ["A", "B"], "required": True}, "code": "required"},
        {"label": "not in choices", "args": {"value": "X", "choices": ["A", "B"]}, "code": "not_allowed"},
    ],
)
def pick_from_searchable_list(ctx, *, value=None, name: str = "autocomplete", label: str = "Search and Pick",
                              choices: list = None, required: bool = False, placeholder: str = "",
                              help_text: str = "") -> dict:
    """Lets the user type to narrow a long list and pick one entry."""
    if not choices:
        choices = []
    spec = {"type": "choice", "required": required, "choices": choices}
    clean = coerce_value(spec, value, label)
    node = view("input.autocomplete", id=name, label=label, value=clean, choices=choices,
                required=required, placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Rate With Stars",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty rating", "args": {"label": "Rating", "max_stars": 5}, 
         "expect": {"view": {"kind": "input.rating"}, "value": None}},
        {"label": "three stars", "args": {"value": 3, "max_stars": 5}, 
         "expect": {"value": 3}},
        {"label": "custom max stars", "args": {"value": 7, "max_stars": 10}, 
         "expect": {"value": 7}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "above max", "args": {"value": 6, "max_stars": 5}, "code": "too_large"},
    ],
)
def rate_with_stars(ctx, *, value=None, name: str = "rating", label: str = "Rating",
                    required: bool = False, max_stars: int = 5, help_text: str = "") -> dict:
    """Lets the user choose a rating by clicking one to five stars."""
    spec = {"type": "integer", "required": required, "min": 1, "max": max_stars}
    clean = coerce_value(spec, value, label)
    node = view("input.rating", id=name, label=label, value=clean, maxStars=max_stars,
                required=required, help=help_text)
    return {"view": node, "value": clean}
