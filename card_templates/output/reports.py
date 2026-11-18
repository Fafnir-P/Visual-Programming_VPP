"""Reports (Navigation / Output). Aggregated data views and summaries."""
from __future__ import annotations

from ..runtime import CardError, bounded, card, get_field, to_number, view

CATEGORY = "Navigation / Output"
GROUP = "Reports"


@card(
    "Summary Table", category=CATEGORY, group=GROUP,
    inputs=["data"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "summary with totals",
         "args": {"data": [{"label": "Total Orders", "value": 42}, {"label": "Revenue", "value": 12500}]},
         "expect": {"view": {"kind": "display.summary", "props": {"rows": [{"label": "Total Orders", "value": 42}, {"label": "Revenue", "value": 12500}]}}}},
        {"label": "summary with title",
         "args": {"data": [{"label": "Items", "value": 10}], "title": "Inventory Summary"},
         "expect": {"view": {"props": {"title": "Inventory Summary"}}}},
    ],
    invalid=[
        {"label": "data not a list", "args": {"data": "text"}, "code": "invalid_input"},
        {"label": "empty data", "args": {"data": []}, "code": "invalid_input"},
    ],
)
def summary_table(ctx, *, data, title: str = "Summary", show_borders: bool = True) -> dict:
    """Presents key totals and counts in a table layout for quick overview."""
    if not isinstance(data, list):
        raise CardError("invalid_input", "Summary data must be a list of records.")
    if not data:
        raise CardError("invalid_input", "Summary needs at least one row.")
    rows = bounded(data, limit=1000, what="summary rows")
    node = view("display.summary", title=title, rows=rows, show_borders=show_borders)
    return {"view": node}


@card(
    "Chart Over Time", category=CATEGORY, group=GROUP,
    inputs=["data"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "line chart",
         "args": {"data": [{"date": "2026-01-01", "value": 10}, {"date": "2026-01-02", "value": 15}],
                  "date_field": "date", "value_field": "value", "chart_type": "line"},
         "expect": {"view": {"kind": "display.chart", "props": {"chart_type": "line"}}}},
        {"label": "bar chart with title",
         "args": {"data": [{"month": "Jan", "count": 5}], "date_field": "month", "value_field": "count",
                  "chart_type": "bar", "title": "Monthly Sales"},
         "expect": {"view": {"props": {"title": "Monthly Sales", "chart_type": "bar"}}}},
    ],
    invalid=[
        {"label": "data not a list", "args": {"data": "text", "date_field": "date", "value_field": "value"}, "code": "invalid_input"},
        {"label": "empty data", "args": {"data": [], "date_field": "date", "value_field": "value"}, "code": "invalid_input"},
    ],
)
def chart_over_time(ctx, *, data, date_field: str = "date", value_field: str = "value",
                    title: str = "Chart", chart_type: str = "line") -> dict:
    """Displays a line or bar chart showing how a measure changes across dates or periods."""
    if not isinstance(data, list):
        raise CardError("invalid_input", "Chart data must be a list of records.")
    if not data:
        raise CardError("invalid_input", "Chart needs at least one data point.")
    points = bounded(data, limit=10000, what="chart points")
    if chart_type not in ("line", "bar", "area"):
        chart_type = "line"
    node = view("display.chart", title=title, chart_type=chart_type, data=points,
                date_field=date_field, value_field=value_field)
    return {"view": node}


@card(
    "Grouped Totals View", category=CATEGORY, group=GROUP,
    inputs=["data"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "group by category",
         "args": {"data": [{"category": "A", "total": 100}, {"category": "B", "total": 150}],
                  "group_field": "category", "value_field": "total"},
         "expect": {"view": {"kind": "display.grouped", "props": {"group_field": "category"}}}},
        {"label": "grouped with title",
         "args": {"data": [{"location": "Store1", "sales": 500}], "group_field": "location",
                  "value_field": "sales", "title": "Sales by Location"},
         "expect": {"view": {"props": {"title": "Sales by Location"}}}},
    ],
    invalid=[
        {"label": "data not a list", "args": {"data": "text", "group_field": "cat", "value_field": "val"}, "code": "invalid_input"},
        {"label": "empty data", "args": {"data": [], "group_field": "cat", "value_field": "val"}, "code": "invalid_input"},
    ],
)
def grouped_totals_view(ctx, *, data, group_field: str = "category", value_field: str = "value",
                        title: str = "Grouped Totals", sort_by: str = "group") -> dict:
    """Shows aggregated counts or sums organized by category or location."""
    if not isinstance(data, list):
        raise CardError("invalid_input", "Grouped data must be a list of records.")
    if not data:
        raise CardError("invalid_input", "Grouped view needs at least one record.")
    groups = bounded(data, limit=1000, what="groups")
    node = view("display.grouped", title=title, data=groups, group_field=group_field,
                value_field=value_field, sort_by=sort_by)
    return {"view": node}


@card(
    "Exception List", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["view"],
    role="view", effects=["view"],
    examples=[
        {"label": "low stock exceptions",
         "args": {"records": [{"item": "Bolt", "qty": 2, "reason": "Low stock"}],
                  "title": "Low Stock Items"},
         "expect": {"view": {"kind": "display.exceptions", "props": {"title": "Low Stock Items"}}}},
        {"label": "overdue records with columns",
         "args": {"records": [{"order": "1001", "days": 5}], "title": "Overdue Orders",
                  "columns": ["order", "days"]},
         "expect": {"view": {"props": {"columns": ["order", "days"]}}}},
    ],
    invalid=[
        {"label": "records not a list", "args": {"records": "text"}, "code": "invalid_input"},
    ],
)
def exception_list(ctx, *, records, title: str = "Exceptions", columns: list = None,
                   max_display: int = 100) -> dict:
    """Lists low-stock, overdue or out-of-limit records that need attention."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Exception records must be a list.")
    items = bounded(records, limit=max_display, what="exception records")
    cols = columns if columns else []
    node = view("display.exceptions", title=title, records=items, columns=cols)
    return {"view": node}
