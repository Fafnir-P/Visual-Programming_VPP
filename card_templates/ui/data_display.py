"""Data Display (UI / Interface). Cards that present data to the user."""
from __future__ import annotations

from ..runtime import CardError, bounded, card, get_field, view

CATEGORY = "UI / Interface"
GROUP = "Data Display"


@card(
    "Show Records Table", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "table with three columns",
         "args": {"records": [{"name": "Bolt", "qty": 10, "price": 1.5}, {"name": "Nut", "qty": 20, "price": 0.8}],
                  "columns": [{"field": "name", "label": "Item"}, {"field": "qty", "label": "Quantity"}, {"field": "price", "label": "Price"}],
                  "sortable": True, "page_size": 50},
         "expect": {"view": {"kind": "display.table", "props": {"sortable": True, "page_size": 50}}}},
        {"label": "empty table",
         "args": {"records": [], "columns": [{"field": "name", "label": "Name"}]},
         "expect": {"view": {"kind": "display.table", "props": {"sortable": False, "page_size": 100}}}},
    ],
    invalid=[
        {"label": "records must be a list", "args": {"records": "not a list", "columns": []}, "code": "invalid_input"},
        {"label": "column missing field", "args": {"records": [], "columns": [{"label": "Name"}]}, "code": "invalid_input"},
    ],
)
def show_records_table(ctx, *, records=None, columns=None, sortable: bool = False, page_size: int = 100) -> dict:
    """Displays rows of data in sortable columns with optional pagination."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    cols = columns if isinstance(columns, list) else []
    for i, col in enumerate(cols):
        if not isinstance(col, dict):
            raise CardError("invalid_input", f"Column {i+1} must be a record.")
        if "field" not in col or not isinstance(col["field"], str):
            raise CardError("invalid_input", f"Column {i+1} needs a field name.")
        if "label" not in col:
            col["label"] = col["field"]
    if page_size < 1:
        raise CardError("invalid_input", "Page size must be at least 1.")
    items = bounded(records, what="records")
    node = view("display.table", records=items, columns=cols, sortable=sortable, page_size=page_size)
    return {"view": node}


@card(
    "List Records", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "list with title and subtitle fields",
         "args": {"records": [{"name": "Item A", "status": "active"}, {"name": "Item B", "status": "pending"}],
                  "title_field": "name", "subtitle_field": "status"},
         "expect": {"view": {"kind": "display.list", "props": {"title_field": "name", "subtitle_field": "status", "icon_field": ""}}}},
        {"label": "list with icon",
         "args": {"records": [{"label": "Order", "icon": "package"}], "title_field": "label", "icon_field": "icon"},
         "expect": {"view": {"kind": "display.list", "props": {"title_field": "label", "icon_field": "icon"}}}},
    ],
    invalid=[
        {"label": "records must be a list", "args": {"records": None, "title_field": "name"}, "code": "invalid_input"},
        {"label": "title field is required", "args": {"records": [], "title_field": ""}, "code": "required"},
    ],
)
def list_records(ctx, *, records=None, title_field: str = "", subtitle_field: str = "", icon_field: str = "") -> dict:
    """Shows data items one per row with icon and text summary."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if not title_field or not isinstance(title_field, str):
        raise CardError("required", "Title field is required.")
    items = bounded(records, what="records")
    node = view("display.list", records=items, title_field=title_field, subtitle_field=subtitle_field, icon_field=icon_field)
    return {"view": node}


@card(
    "Display Record Card", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "card with selected fields",
         "args": {"record": {"name": "Bolt", "qty": 10, "price": 1.5, "internal": "X"},
                  "fields": [{"name": "name", "label": "Item"}, {"name": "qty", "label": "Stock"}]},
         "expect": {"view": {"kind": "display.card", "props": {"layout": "rows"}}}},
        {"label": "compact layout",
         "args": {"record": {"id": 1, "status": "active"}, "fields": [{"name": "status", "label": "Status"}], "layout": "compact"},
         "expect": {"view": {"kind": "display.card", "props": {"layout": "compact"}}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": [1, 2], "fields": []}, "code": "invalid_input"},
        {"label": "field missing name", "args": {"record": {}, "fields": [{"label": "Test"}]}, "code": "invalid_input"},
    ],
)
def display_record_card(ctx, *, record=None, fields=None, layout: str = "rows") -> dict:
    """Presents a single record's fields in labeled rows or compact layout."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a dict.")
    flds = fields if isinstance(fields, list) else []
    for i, fld in enumerate(flds):
        if not isinstance(fld, dict):
            raise CardError("invalid_input", f"Field {i+1} must be a record.")
        if "name" not in fld or not isinstance(fld["name"], str):
            raise CardError("invalid_input", f"Field {i+1} needs a name.")
        if "label" not in fld:
            fld["label"] = fld["name"]
    if layout not in ("rows", "compact"):
        raise CardError("invalid_input", "Layout must be 'rows' or 'compact'.")
    node = view("display.card", record=record, fields=flds, layout=layout)
    return {"view": node}


@card(
    "Show Detail View", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "detail view with sections",
         "args": {"record": {"name": "Bolt", "qty": 10, "category": "Hardware"},
                  "sections": [{"title": "Basic", "fields": ["name", "category"]}, {"title": "Stock", "fields": ["qty"]}]},
         "expect": {"view": {"kind": "display.detail"}}},
        {"label": "single section",
         "args": {"record": {"id": 1, "status": "shipped"}, "sections": [{"title": "Info", "fields": ["id", "status"]}]},
         "expect": {"view": {"kind": "display.detail", "props": {}}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": None, "sections": []}, "code": "invalid_input"},
        {"label": "section missing title", "args": {"record": {}, "sections": [{"fields": ["a"]}]}, "code": "invalid_input"},
    ],
)
def show_detail_view(ctx, *, record=None, sections=None) -> dict:
    """Displays all fields of one selected record in organized sections."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a dict.")
    secs = sections if isinstance(sections, list) else []
    for i, sec in enumerate(secs):
        if not isinstance(sec, dict):
            raise CardError("invalid_input", f"Section {i+1} must be a record.")
        if "title" not in sec or not isinstance(sec["title"], str):
            raise CardError("invalid_input", f"Section {i+1} needs a title.")
        if "fields" not in sec or not isinstance(sec["fields"], list):
            raise CardError("invalid_input", f"Section {i+1} needs a fields list.")
    node = view("display.detail", record=record, sections=secs)
    return {"view": node}


@card(
    "Show Status Badge", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "status with color",
         "args": {"value": "shipped", "color": "green"},
         "expect": {"view": {"kind": "display.badge", "props": {"value": "shipped", "color": "green"}}}},
        {"label": "default gray badge",
         "args": {"value": "pending"},
         "expect": {"view": {"kind": "display.badge", "props": {"value": "pending", "color": "gray"}}}},
    ],
    invalid=[
        {"label": "value is required", "args": {"value": ""}, "code": "required"},
        {"label": "invalid color", "args": {"value": "test", "color": "purple"}, "code": "invalid_input"},
    ],
)
def show_status_badge(ctx, *, value="", color: str = "gray") -> dict:
    """Displays a colored label indicating state like pending approved or shipped."""
    if not value or (isinstance(value, str) and not value.strip()):
        raise CardError("required", "Badge value is required.")
    allowed = ("gray", "blue", "green", "yellow", "red", "orange")
    if color not in allowed:
        raise CardError("invalid_input", f"Color must be one of: {', '.join(allowed)}.")
    text = str(value).strip() if isinstance(value, str) else str(value)
    node = view("display.badge", value=text, color=color)
    return {"view": node}


@card(
    "Display Barcode From Code", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "code128 barcode",
         "args": {"value": "ABC123", "format": "code128"},
         "expect": {"view": {"kind": "display.barcode", "props": {"value": "ABC123", "format": "code128", "width": 2, "height": 50}}}},
        {"label": "qr code",
         "args": {"value": "https://example.com/item/42", "format": "qr", "width": 3},
         "expect": {"view": {"kind": "display.barcode", "props": {"value": "https://example.com/item/42", "format": "qr", "width": 3}}}},
    ],
    invalid=[
        {"label": "value is required", "args": {"value": ""}, "code": "required"},
        {"label": "invalid format", "args": {"value": "123", "format": "unknown"}, "code": "invalid_input"},
    ],
)
def display_barcode_from_code(ctx, *, value="", format: str = "code128", width: int = 2, height: int = 50) -> dict:
    """Shows a barcode image created from the product code or identifier of a record."""
    if not value or (isinstance(value, str) and not value.strip()):
        raise CardError("required", "Barcode value is required.")
    allowed = ("code128", "ean13", "upca", "qr")
    if format not in allowed:
        raise CardError("invalid_input", f"Format must be one of: {', '.join(allowed)}.")
    if width < 1:
        raise CardError("invalid_input", "Width must be at least 1.")
    if height < 1:
        raise CardError("invalid_input", "Height must be at least 1.")
    text = str(value).strip() if isinstance(value, str) else str(value)
    node = view("display.barcode", value=text, format=format, width=width, height=height)
    return {"view": node}
