"""Form Inputs (UI / Interface). Cards that let users enter typed data."""
from __future__ import annotations

from ..runtime import CardError, card, coerce_value, view

CATEGORY = "UI / Interface"
GROUP = "Form Inputs"


@card(
    "Enter Text",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty field", "args": {"label": "Name"}, 
         "expect": {"view": {"kind": "input.text", "props": {"label": "Name"}}, "value": None}},
        {"label": "cleans whitespace", "args": {"value": "  Item ", "label": "Name"}, 
         "expect": {"value": "Item"}},
        {"label": "respects max length", "args": {"value": "Short", "max_length": 50}, 
         "expect": {"value": "Short"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": "", "required": True}, "code": "required"},
        {"label": "exceeds max length", "args": {"value": "x" * 101, "max_length": 100}, "code": "too_long"},
    ],
)
def enter_text(ctx, *, value=None, name: str = "text", label: str = "Text",
               required: bool = False, max_length: int = 100, placeholder: str = "",
               help_text: str = "") -> dict:
    """Lets the user type a single line of text into a labeled field."""
    spec = {"type": "text", "required": required, "max_length": max_length}
    clean = coerce_value(spec, value, label)
    node = view("input.text", id=name, label=label, value=clean or "", required=required,
                maxLength=max_length, placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Enter Paragraph",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty textarea", "args": {"label": "Notes"}, 
         "expect": {"view": {"kind": "input.textarea"}, "value": None}},
        {"label": "multiline text", "args": {"value": "Line one\nLine two", "label": "Description"}, 
         "expect": {"value": "Line one\nLine two"}},
        {"label": "respects max length", "args": {"value": "Text", "max_length": 500}, 
         "expect": {"value": "Text"}},
    ],
    invalid=[
        {"label": "required but blank", "args": {"value": "   ", "required": True}, "code": "required"},
        {"label": "too long", "args": {"value": "x" * 1001, "max_length": 1000}, "code": "too_long"},
    ],
)
def enter_paragraph(ctx, *, value=None, name: str = "paragraph", label: str = "Paragraph",
                    required: bool = False, max_length: int = 1000, placeholder: str = "",
                    rows: int = 4, help_text: str = "") -> dict:
    """Lets the user type multiple lines of text into a labeled box."""
    spec = {"type": "text", "required": required, "max_length": max_length, "strip": False}
    clean = coerce_value(spec, value, label)
    node = view("input.textarea", id=name, label=label, value=clean or "", required=required,
                maxLength=max_length, placeholder=placeholder, rows=rows, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Enter Number",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty number field", "args": {"label": "Quantity"}, 
         "expect": {"view": {"kind": "input.number"}, "value": None}},
        {"label": "valid number", "args": {"value": 42, "label": "Count"}, 
         "expect": {"value": 42}},
        {"label": "respects range", "args": {"value": 5, "min_value": 1, "max_value": 10}, 
         "expect": {"value": 5}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "below minimum", "args": {"value": 0, "min_value": 1}, "code": "too_small"},
    ],
)
def enter_number(ctx, *, value=None, name: str = "number", label: str = "Number",
                 required: bool = False, min_value=None, max_value=None,
                 placeholder: str = "", help_text: str = "") -> dict:
    """Lets the user type or adjust a numeric value with optional min and max."""
    spec = {"type": "number", "required": required, "min": min_value, "max": max_value}
    clean = coerce_value(spec, value, label)
    node = view("input.number", id=name, label=label, value=clean, required=required,
                min=min_value, max=max_value, placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Pick Date",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty date picker", "args": {"label": "Order Date"}, 
         "expect": {"view": {"kind": "input.date"}, "value": None}},
        {"label": "valid date", "args": {"value": "2026-03-15", "label": "Ship Date"}, 
         "expect": {"value": "2026-03-15"}},
        {"label": "respects min", "args": {"value": "2026-06-01", "min_date": "2026-01-01"}, 
         "expect": {"value": "2026-06-01"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "before minimum", "args": {"value": "2025-12-31", "min_date": "2026-01-01"}, "code": "too_small"},
    ],
)
def pick_date(ctx, *, value=None, name: str = "date", label: str = "Date",
              required: bool = False, min_date=None, max_date=None, help_text: str = "") -> dict:
    """Lets the user select a date from a calendar popup."""
    spec = {"type": "date", "required": required, "min": min_date, "max": max_date}
    clean = coerce_value(spec, value, label)
    node = view("input.date", id=name, label=label, value=clean, required=required,
                min=min_date, max=max_date, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Pick Time",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty time picker", "args": {"label": "Start Time"}, 
         "expect": {"view": {"kind": "input.time"}, "value": None}},
        {"label": "valid time", "args": {"value": "14:30", "label": "Delivery Time"}, 
         "expect": {"value": "14:30"}},
        {"label": "with seconds", "args": {"value": "09:15:30"}, 
         "expect": {"value": "09:15:30"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "invalid format", "args": {"value": "25:00"}, "code": "not_a_time"},
    ],
)
def pick_time(ctx, *, value=None, name: str = "time", label: str = "Time",
              required: bool = False, help_text: str = "") -> dict:
    """Lets the user select a time of day from hour and minute controls."""
    spec = {"type": "time", "required": required}
    clean = coerce_value(spec, value, label)
    node = view("input.time", id=name, label=label, value=clean, required=required, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Enter Email Address",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty email field", "args": {"label": "Email"}, 
         "expect": {"view": {"kind": "input.email"}, "value": None}},
        {"label": "valid email", "args": {"value": "user@example.com", "label": "Contact"}, 
         "expect": {"value": "user@example.com"}},
        {"label": "lowercases email", "args": {"value": "User@Example.COM"}, 
         "expect": {"value": "user@example.com"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": "", "required": True}, "code": "required"},
        {"label": "invalid format", "args": {"value": "not-an-email"}, "code": "bad_format"},
    ],
)
def enter_email_address(ctx, *, value=None, name: str = "email", label: str = "Email Address",
                        required: bool = False, placeholder: str = "", help_text: str = "") -> dict:
    """Lets the user type an email address into a validated field."""
    spec = {"type": "email", "required": required}
    clean = coerce_value(spec, value, label)
    node = view("input.email", id=name, label=label, value=clean or "", required=required,
                placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Enter Phone Number",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty phone field", "args": {"label": "Phone"}, 
         "expect": {"view": {"kind": "input.phone"}, "value": None}},
        {"label": "valid phone", "args": {"value": "(555) 123-4567", "label": "Contact Number"}, 
         "expect": {"value": "(555) 123-4567"}},
        {"label": "international format", "args": {"value": "+1-555-123-4567"}, 
         "expect": {"value": "+1-555-123-4567"}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "invalid format", "args": {"value": "abc"}, "code": "bad_format"},
    ],
)
def enter_phone_number(ctx, *, value=None, name: str = "phone", label: str = "Phone Number",
                       required: bool = False, placeholder: str = "", help_text: str = "") -> dict:
    """Lets the user type a phone number into a formatted field."""
    spec = {"type": "phone", "required": required}
    clean = coerce_value(spec, value, label)
    node = view("input.phone", id=name, label=label, value=clean or "", required=required,
                placeholder=placeholder, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Enter Currency Amount",
    category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["view", "value"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty currency field", "args": {"label": "Price", "currency": "USD"}, 
         "expect": {"view": {"kind": "input.currency"}, "value": None}},
        {"label": "rounds to cents", "args": {"value": 19.999, "label": "Amount"}, 
         "expect": {"value": 20.0}},
        {"label": "respects minimum", "args": {"value": 5.0, "min_value": 0}, 
         "expect": {"value": 5.0}},
    ],
    invalid=[
        {"label": "required but empty", "args": {"value": None, "required": True}, "code": "required"},
        {"label": "below minimum", "args": {"value": -1, "min_value": 0}, "code": "too_small"},
    ],
)
def enter_currency_amount(ctx, *, value=None, name: str = "amount", label: str = "Amount",
                          required: bool = False, min_value=None, max_value=None,
                          currency: str = "USD", help_text: str = "") -> dict:
    """Lets the user type a monetary value with currency symbol and formatting."""
    spec = {"type": "currency", "required": required, "min": min_value, "max": max_value}
    clean = coerce_value(spec, value, label)
    node = view("input.currency", id=name, label=label, value=clean, required=required,
                min=min_value, max=max_value, currency=currency, help=help_text)
    return {"view": node, "value": clean}


@card(
    "Pick Date Range",
    category=CATEGORY, group=GROUP,
    inputs=["start_date", "end_date"], outputs=["view", "start_date", "end_date"],
    phase="runtime", effects=["view"], idempotent=True, role="view",
    examples=[
        {"label": "empty range", "args": {"label": "Period"}, 
         "expect": {"view": {"kind": "input.daterange"}, "start_date": None, "end_date": None}},
        {"label": "valid range", "args": {"start_date": "2026-01-01", "end_date": "2026-01-31"}, 
         "expect": {"start_date": "2026-01-01", "end_date": "2026-01-31"}},
        {"label": "both required", "args": {"start_date": "2026-02-01", "end_date": "2026-02-28", "required": True}, 
         "expect": {"start_date": "2026-02-01", "end_date": "2026-02-28"}},
    ],
    invalid=[
        {"label": "start required but missing", "args": {"start_date": None, "end_date": "2026-01-31", "required": True}, 
         "code": "required"},
        {"label": "end before start", "args": {"start_date": "2026-02-01", "end_date": "2026-01-01"}, 
         "code": "invalid_input"},
    ],
)
def pick_date_range(ctx, *, start_date=None, end_date=None, name: str = "daterange",
                    label: str = "Date Range", required: bool = False, help_text: str = "") -> dict:
    """Lets the user choose a start date and an end date together from one calendar."""
    spec_start = {"type": "date", "required": required}
    spec_end = {"type": "date", "required": required}
    start_clean = coerce_value(spec_start, start_date, "Start date")
    end_clean = coerce_value(spec_end, end_date, "End date")
    if start_clean and end_clean and start_clean > end_clean:
        raise CardError("invalid_input", "Start date must be before or equal to end date.")
    node = view("input.daterange", id=name, label=label, startDate=start_clean, endDate=end_clean,
                required=required, help=help_text)
    return {"view": node, "start_date": start_clean, "end_date": end_clean}
