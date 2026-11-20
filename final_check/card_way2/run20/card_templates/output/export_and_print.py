"""Export and Print (Navigation / Output). Output formatting for printing and export."""
from __future__ import annotations

from ..runtime import CardError, card, view

CATEGORY = "Navigation / Output"
GROUP = "Export and Print"


@card(
    "Print-Friendly Page", category=CATEGORY, group=GROUP,
    inputs=["content"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "print layout with content",
         "args": {"content": {"kind": "display.text", "id": None, "props": {"text": "Order summary"}, "children": []},
                  "title": "Order Receipt"},
         "expect": {"view": {"kind": "print.page", "props": {"title": "Order Receipt"}}}},
        {"label": "print with header and footer",
         "args": {"content": {"kind": "layout.stack", "id": None, "props": {}, "children": []},
                  "show_header": True, "show_footer": True},
         "expect": {"view": {"props": {"show_header": True, "show_footer": True}}}},
    ],
    invalid=[
        {"label": "missing content", "args": {"title": "Print"}, "code": "required"},
        {"label": "content not a view", "args": {"content": "plain text"}, "code": "invalid_input"},
    ],
)
def print_friendly_page(ctx, *, content=None, title: str = "Document", 
                        show_header: bool = False, show_footer: bool = False,
                        page_size: str = "A4", orientation: str = "portrait") -> dict:
    """Formats the current view for clean printing, without menus or navigation elements."""
    if content is None:
        raise CardError("required", "Print page needs content.")
    if not isinstance(content, dict) or "kind" not in content:
        raise CardError("invalid_input", "Content must be a view node.")
    if orientation not in ("portrait", "landscape"):
        orientation = "portrait"
    node = view("print.page", title=title, show_header=show_header, show_footer=show_footer,
                page_size=page_size, orientation=orientation, children=[content])
    return {"view": node}
