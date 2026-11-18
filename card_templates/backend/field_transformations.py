"""Field Transformations (Backend Processing). Convert, format, extract and combine field values."""
from __future__ import annotations

import re

from ..runtime import (
    CardError,
    as_text,
    card,
    coerce_value,
    get_field,
    is_blank,
    round_half_up,
    to_date,
    to_datetime,
    to_number,
)

CATEGORY = "Backend Processing"
GROUP = "Field Transformations"


@card(
    "Convert Field Type",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["record"],
    examples=[
        {
            "label": "text to number",
            "args": {"record": {"qty": "42"}, "field": "qty", "target_type": "number"},
            "expect": {"record": {"qty": 42}},
        },
        {
            "label": "number to text",
            "args": {"record": {"price": 19.99}, "field": "price", "target_type": "text"},
            "expect": {"record": {"price": "19.99"}},
        },
        {
            "label": "date to text",
            "args": {"record": {"due": "2026-03-15"}, "field": "due", "target_type": "text"},
            "expect": {"record": {"due": "2026-03-15"}},
        },
    ],
    invalid=[
        {
            "label": "bad text to number",
            "args": {"record": {"qty": "abc"}, "field": "qty", "target_type": "number"},
            "code": "not_a_number",
        },
        {
            "label": "bad text to date",
            "args": {"record": {"due": "tomorrow"}, "field": "due", "target_type": "date"},
            "code": "not_a_date",
        },
    ],
)
def convert_field_type(ctx, *, record, field: str = "value", target_type: str = "text") -> dict:
    """Changes a field from one data type to another, such as text to number or date to text."""
    rec = dict(record)
    value = get_field(rec, field)
    spec = {"type": target_type}
    rec[field] = coerce_value(spec, value, field)
    return {"record": rec}


@card(
    "Format Currency Value",
    category=CATEGORY,
    group=GROUP,
    inputs=["value"],
    outputs=["text"],
    examples=[
        {
            "label": "simple amount",
            "args": {"value": 1234.5, "symbol": "$"},
            "expect": {"text": "$1,234.50"},
        },
        {
            "label": "zero",
            "args": {"value": 0, "symbol": "€", "separator": " "},
            "expect": {"text": "€0.00"},
        },
        {
            "label": "negative",
            "args": {"value": -99.99, "symbol": "£"},
            "expect": {"text": "-£99.99"},
        },
    ],
    invalid=[
        {"label": "not a number", "args": {"value": "abc"}, "code": "not_a_number"},
    ],
)
def format_currency_value(
    ctx, *, value, symbol: str = "$", separator: str = ",", decimals: int = 2
) -> dict:
    """Displays a number as currency with symbol, decimal places, and thousands separator."""
    num = round_half_up(to_number(value, "value"), decimals)
    sign = "-" if num < 0 else ""
    num = abs(num)
    parts = f"{num:.{decimals}f}".split(".")
    whole = parts[0]
    if separator:
        whole = f"{int(whole):,}".replace(",", separator)
    text = f"{sign}{symbol}{whole}.{parts[1]}"
    return {"text": text}


@card(
    "Extract Substring",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["text"],
    examples=[
        {
            "label": "first three",
            "args": {"text": "ABC-123", "start": 0, "length": 3},
            "expect": {"text": "ABC"},
        },
        {
            "label": "from middle",
            "args": {"text": "ABC-123", "start": 4, "length": 2},
            "expect": {"text": "12"},
        },
        {
            "label": "blank text gives blank",
            "args": {"text": "", "start": 0, "length": 5},
            "expect": {"text": ""},
        },
    ],
    invalid=[
        {
            "label": "negative start",
            "args": {"text": "ABC", "start": -1, "length": 2},
            "code": "invalid_input",
        },
    ],
)
def extract_substring(ctx, *, text, start: int = 0, length: int = 10) -> dict:
    """Pulls out a portion of text from a field using start position and length."""
    if start < 0:
        raise CardError("invalid_input", "Start position cannot be negative.")
    if length < 0:
        raise CardError("invalid_input", "Length cannot be negative.")
    s = as_text(text, "text")
    return {"text": s[start : start + length]}


@card(
    "Combine Multiple Fields",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["text"],
    examples=[
        {
            "label": "name from parts",
            "args": {"record": {"first": "Anna", "last": "Smith"}, "fields": ["first", "last"], "separator": " "},
            "expect": {"text": "Anna Smith"},
        },
        {
            "label": "three fields",
            "args": {
                "record": {"city": "Boston", "state": "MA", "zip": "02101"},
                "fields": ["city", "state", "zip"],
                "separator": ", ",
            },
            "expect": {"text": "Boston, MA, 02101"},
        },
        {
            "label": "blank fields skipped",
            "args": {"record": {"a": "X", "b": None, "c": "Y"}, "fields": ["a", "b", "c"], "separator": "-"},
            "expect": {"text": "X-Y"},
        },
    ],
    invalid=[
        {
            "label": "empty field list",
            "args": {"record": {"a": "X"}, "fields": []},
            "code": "invalid_input",
        },
    ],
)
def combine_multiple_fields(ctx, *, record, fields: list, separator: str = " ") -> dict:
    """Joins two or more fields into one with optional separator text between them."""
    if not fields:
        raise CardError("invalid_input", "At least one field is required.")
    parts = []
    for f in fields:
        val = get_field(record, f)
        if not is_blank(val):
            parts.append(str(val))
    return {"text": separator.join(parts)}


@card(
    "Round Numeric Value",
    category=CATEGORY,
    group=GROUP,
    inputs=["value"],
    outputs=["value"],
    examples=[
        {
            "label": "two places",
            "args": {"value": 3.14159, "places": 2},
            "expect": {"value": 3.14},
        },
        {
            "label": "whole number",
            "args": {"value": 7.6, "places": 0},
            "expect": {"value": 8.0},
        },
        {
            "label": "already rounded",
            "args": {"value": 10, "places": 2},
            "expect": {"value": 10.0},
        },
    ],
    invalid=[
        {"label": "not a number", "args": {"value": "abc"}, "code": "not_a_number"},
    ],
)
def round_numeric_value(ctx, *, value, places: int = 2) -> dict:
    """Rounds a number to a specified number of decimal places or to the nearest whole number."""
    num = to_number(value, "value")
    return {"value": round_half_up(num, places)}


@card(
    "Trim Whitespace",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["text"],
    examples=[
        {
            "label": "leading and trailing spaces",
            "args": {"text": "  hello  "},
            "expect": {"text": "hello"},
        },
        {
            "label": "line breaks removed",
            "args": {"text": "\n\n  text  \n"},
            "expect": {"text": "text"},
        },
        {
            "label": "already clean",
            "args": {"text": "clean"},
            "expect": {"text": "clean"},
        },
    ],
    invalid=[{"label": "a number is not text", "args": {"text": 5}, "code": "invalid_input"}],
)
def trim_whitespace(ctx, *, text) -> dict:
    """Removes leading and trailing spaces or line breaks from a text field."""
    s = as_text(text, "text")
    return {"text": s.strip()}


@card(
    "Change Text Case",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["text"],
    examples=[
        {
            "label": "uppercase",
            "args": {"text": "hello", "case": "upper"},
            "expect": {"text": "HELLO"},
        },
        {
            "label": "lowercase",
            "args": {"text": "WORLD", "case": "lower"},
            "expect": {"text": "world"},
        },
        {
            "label": "title case",
            "args": {"text": "hello world", "case": "title"},
            "expect": {"text": "Hello World"},
        },
    ],
    invalid=[
        {
            "label": "unknown case",
            "args": {"text": "test", "case": "reverse"},
            "code": "invalid_input",
        },
    ],
)
def change_text_case(ctx, *, text, case: str = "upper") -> dict:
    """Converts text to uppercase, lowercase, or title case as specified."""
    s = as_text(text, "text")
    if case == "upper":
        return {"text": s.upper()}
    if case == "lower":
        return {"text": s.lower()}
    if case == "title":
        return {"text": s.title()}
    raise CardError("invalid_input", f"Case must be upper, lower or title (got {case!r}).")


@card(
    "Generate Unique Identifier",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["record"],
    effects=["writes_store"],
    idempotent=False,
    examples=[
        {
            "label": "first id",
            "args": {"record": {"name": "Item"}, "field": "code", "prefix": "ORD"},
            "expect": {"record": {"name": "Item", "code": "ORD-1"}},
        },
        {
            "label": "second id increments",
            "tables": {},
            "args": {"record": {"x": "a"}, "field": "id", "prefix": "INV", "counter": "inv"},
            "expect": {"record": {"x": "a", "id": "INV-1"}},
        },
    ],
    invalid=[
        {"label": "record is not a record", "args": {"record": "x"}, "code": "invalid_input"},
        {"label": "counter name is not allowed", "args": {"record": {}, "counter": "bad name"}, "code": "bad_name"},
    ],
)
def generate_unique_identifier(
    ctx, *, record, field: str = "code", prefix: str = "ID", counter: str = "default"
) -> dict:
    """Creates a unique code for each new record from a prefix and a counter saved with the table."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a record.")
    rec = dict(record)
    num = ctx.store.next_counter(counter)
    rec[field] = f"{prefix}-{num}"
    return {"record": rec}


@card(
    "Extract Domain From Email",
    category=CATEGORY,
    group=GROUP,
    inputs=["email"],
    outputs=["domain"],
    examples=[
        {
            "label": "simple email",
            "args": {"email": "user@example.com"},
            "expect": {"domain": "example.com"},
        },
        {
            "label": "subdomain",
            "args": {"email": "admin@mail.company.org"},
            "expect": {"domain": "mail.company.org"},
        },
        {
            "label": "uppercase lowered",
            "args": {"email": "Test@DOMAIN.COM"},
            "expect": {"domain": "domain.com"},
        },
    ],
    invalid=[
        {"label": "no at sign", "args": {"email": "notanemail"}, "code": "bad_format"},
        {"label": "blank", "args": {"email": ""}, "code": "bad_format"},
    ],
)
def extract_domain_from_email(ctx, *, email) -> dict:
    """Pulls the domain portion from an email address field for grouping or filtering."""
    text = str(email).strip().lower() if email else ""
    if "@" not in text or text.count("@") != 1:
        raise CardError("bad_format", "Email must contain one @ sign.")
    domain = text.split("@")[1]
    if not domain or "." not in domain:
        raise CardError("bad_format", "Email domain is not valid.")
    return {"domain": domain}


@card(
    "Format Phone Number",
    category=CATEGORY,
    group=GROUP,
    inputs=["phone"],
    outputs=["text"],
    examples=[
        {
            "label": "ten digits",
            "args": {"phone": "6175551234", "format": "(###) ###-####"},
            "expect": {"text": "(617) 555-1234"},
        },
        {
            "label": "with leading one",
            "args": {"phone": "16175551234", "format": "+# (###) ###-####"},
            "expect": {"text": "+1 (617) 555-1234"},
        },
        {
            "label": "already formatted kept",
            "args": {"phone": "(617) 555-1234", "format": "(###) ###-####"},
            "expect": {"text": "(617) 555-1234"},
        },
    ],
    invalid=[
        {
            "label": "too few digits",
            "args": {"phone": "123", "format": "(###) ###-####"},
            "code": "bad_format",
        },
    ],
)
def format_phone_number(ctx, *, phone, format: str = "(###) ###-####") -> dict:
    """Standardizes phone numbers to a consistent display format with area code and separators."""
    text = str(phone) if phone else ""
    digits = re.sub(r"\D", "", text)
    needed = format.count("#")
    if len(digits) != needed:
        raise CardError(
            "bad_format",
            f"Phone number must have {needed} digits (found {len(digits)}).",
        )
    result = []
    idx = 0
    for char in format:
        if char == "#":
            result.append(digits[idx])
            idx += 1
        else:
            result.append(char)
    return {"text": "".join(result)}
