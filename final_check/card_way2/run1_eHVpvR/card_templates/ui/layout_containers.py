"""Layout Containers (UI / Interface). Cards that arrange and organize other view elements."""
from __future__ import annotations

from ..runtime import CardError, card, view

CATEGORY = "UI / Interface"
GROUP = "Layout Containers"


@card(
    "Arrange In Grid", category=CATEGORY, group=GROUP,
    inputs=["children"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "two columns three rows",
         "args": {"children": [view("display.text", text=f"Item {i}") for i in range(6)], "columns": 2},
         "expect": {"view": {"kind": "layout.grid", "props": {"columns": 2, "gap": 16}}}},
        {"label": "empty grid is allowed",
         "args": {"children": [], "columns": 3, "gap": 8},
         "expect": {"view": {"kind": "layout.grid", "props": {"columns": 3, "gap": 8}, "children": []}}},
    ],
    invalid=[
        {"label": "columns must be positive", "args": {"children": [], "columns": 0}, "code": "invalid_input"},
        {"label": "gap cannot be negative", "args": {"children": [], "gap": -5}, "code": "invalid_input"},
    ],
)
def arrange_in_grid(ctx, *, children=None, columns: int = 2, gap: int = 16) -> dict:
    """Displays child cards in rows and columns with equal spacing."""
    if columns < 1:
        raise CardError("invalid_input", "Grid needs at least 1 column.")
    if gap < 0:
        raise CardError("invalid_input", "Gap cannot be negative.")
    kids = children if isinstance(children, list) else []
    node = view("layout.grid", children=kids, columns=columns, gap=gap)
    return {"view": node}


@card(
    "Stack In Panel", category=CATEGORY, group=GROUP,
    inputs=["children"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "panel with title and border",
         "args": {"children": [view("display.text", text="Content")], "title": "Details", "border": True},
         "expect": {"view": {"kind": "layout.panel", "props": {"title": "Details", "border": True}}}},
        {"label": "panel without title",
         "args": {"children": [view("display.text", text="A"), view("display.text", text="B")]},
         "expect": {"view": {"kind": "layout.panel", "props": {"title": "", "border": False}}}},
    ],
    invalid=[
        {"label": "children must be a list", "args": {"children": "not a list"}, "code": "invalid_input"},
        {"label": "title must be text", "args": {"children": [], "title": 123}, "code": "invalid_input"},
    ],
)
def stack_in_panel(ctx, *, children=None, title: str = "", border: bool = False) -> dict:
    """Groups child cards vertically in a bordered section with optional title."""
    if not isinstance(children, list):
        raise CardError("invalid_input", "Children must be a list of view nodes.")
    if not isinstance(title, str):
        raise CardError("invalid_input", "Title must be text.")
    node = view("layout.panel", children=children, title=title, border=border)
    return {"view": node}


@card(
    "Organize In Tabs", category=CATEGORY, group=GROUP,
    inputs=["tabs"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "three tabs with labels and content",
         "args": {"tabs": [{"label": "Overview", "children": [view("display.text", text="Tab 1")]},
                           {"label": "Details", "children": [view("display.text", text="Tab 2")]},
                           {"label": "History", "children": []}]},
         "expect": {"view": {"kind": "layout.tabs"}}},
        {"label": "single tab",
         "args": {"tabs": [{"label": "Main", "children": []}]},
         "expect": {"view": {"kind": "layout.tabs", "children": []}}},
    ],
    invalid=[
        {"label": "tabs must be a list", "args": {"tabs": "not a list"}, "code": "invalid_input"},
        {"label": "tab missing label", "args": {"tabs": [{"children": []}]}, "code": "invalid_input"},
    ],
)
def organize_in_tabs(ctx, *, tabs=None) -> dict:
    """Shows one group of cards at a time under clickable tab labels."""
    if not isinstance(tabs, list) or not tabs:
        raise CardError("invalid_input", "Tabs must be a list with at least one tab.")
    for i, tab in enumerate(tabs):
        if not isinstance(tab, dict):
            raise CardError("invalid_input", f"Tab {i+1} must be a record.")
        if "label" not in tab or not isinstance(tab["label"], str):
            raise CardError("invalid_input", f"Tab {i+1} needs a label.")
        if "children" not in tab or not isinstance(tab["children"], list):
            raise CardError("invalid_input", f"Tab {i+1} needs a children list.")
    node = view("layout.tabs", tabs=tabs)
    return {"view": node}


@card(
    "Split Into Columns", category=CATEGORY, group=GROUP,
    inputs=["children"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "two equal columns",
         "args": {"children": [view("display.text", text="Left"), view("display.text", text="Right")], "widths": [1, 1]},
         "expect": {"view": {"kind": "layout.columns", "props": {"widths": [1, 1], "gap": 16}}}},
        {"label": "three columns with custom widths",
         "args": {"children": [view("display.text", text=str(i)) for i in range(3)], "widths": [2, 1, 1], "gap": 8},
         "expect": {"view": {"kind": "layout.columns", "props": {"widths": [2, 1, 1], "gap": 8}}}},
    ],
    invalid=[
        {"label": "widths and children must match", "args": {"children": [view("display.text", text="A")], "widths": [1, 1]}, "code": "invalid_input"},
        {"label": "width cannot be zero", "args": {"children": [view("display.text", text="A")], "widths": [0]}, "code": "invalid_input"},
    ],
)
def split_into_columns(ctx, *, children=None, widths=None, gap: int = 16) -> dict:
    """Divides the space into side by side sections for child cards."""
    kids = children if isinstance(children, list) else []
    if not kids:
        raise CardError("invalid_input", "Columns need at least one child.")
    ws = widths if isinstance(widths, list) else [1] * len(kids)
    if len(ws) != len(kids):
        raise CardError("invalid_input", f"Number of widths ({len(ws)}) must match number of children ({len(kids)}).")
    if any(w <= 0 for w in ws):
        raise CardError("invalid_input", "Column widths must be positive.")
    if gap < 0:
        raise CardError("invalid_input", "Gap cannot be negative.")
    node = view("layout.columns", children=kids, widths=ws, gap=gap)
    return {"view": node}


@card(
    "Collapse Section", category=CATEGORY, group=GROUP,
    inputs=["children"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "collapsed by default",
         "args": {"children": [view("display.text", text="Content")], "title": "Details", "collapsed": True},
         "expect": {"view": {"kind": "layout.collapsible", "props": {"title": "Details", "collapsed": True}}}},
        {"label": "expanded by default",
         "args": {"children": [view("display.text", text="A"), view("display.text", text="B")], "title": "Options", "collapsed": False},
         "expect": {"view": {"kind": "layout.collapsible", "props": {"title": "Options", "collapsed": False}}}},
    ],
    invalid=[
        {"label": "title is required", "args": {"children": [], "title": ""}, "code": "required"},
        {"label": "children must be a list", "args": {"children": None, "title": "Test"}, "code": "invalid_input"},
    ],
)
def collapse_section(ctx, *, children=None, title: str = "", collapsed: bool = False) -> dict:
    """Hides or shows child cards when the user clicks the section header."""
    if not title or not isinstance(title, str) or not title.strip():
        raise CardError("required", "Section title is required.")
    if not isinstance(children, list):
        raise CardError("invalid_input", "Children must be a list of view nodes.")
    node = view("layout.collapsible", children=children, title=title.strip(), collapsed=collapsed)
    return {"view": node}


@card(
    "Set App Title", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "simple title",
         "args": {"title": "Inventory Manager"},
         "expect": {"view": {"kind": "layout.app_title", "props": {"title": "Inventory Manager", "subtitle": ""}}}},
        {"label": "title with subtitle",
         "args": {"title": "Orders", "subtitle": "Active shipments"},
         "expect": {"view": {"kind": "layout.app_title", "props": {"title": "Orders", "subtitle": "Active shipments"}}}},
    ],
    invalid=[
        {"label": "title is required", "args": {"title": ""}, "code": "required"},
        {"label": "title must be text", "args": {"title": 123}, "code": "invalid_input"},
    ],
)
def set_app_title(ctx, *, title: str = "", subtitle: str = "") -> dict:
    """Sets the name shown at the top of the app and in the window title."""
    if not isinstance(title, str):
        raise CardError("invalid_input", "App title must be text.")
    if not title.strip():
        raise CardError("required", "App title is required.")
    if not isinstance(subtitle, str):
        raise CardError("invalid_input", "Subtitle must be text.")
    node = view("layout.app_title", title=title.strip(), subtitle=subtitle.strip())
    return {"view": node}
