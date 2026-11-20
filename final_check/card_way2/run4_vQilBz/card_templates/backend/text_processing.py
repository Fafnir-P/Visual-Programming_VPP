"""Text Processing (Backend Processing). Split, search, replace and extract text patterns."""
from __future__ import annotations

import re

from ..runtime import MAX_TEXT_LENGTH, CardError, as_text, bounded, card, get_field, is_blank, try_number

CATEGORY = "Backend Processing"
GROUP = "Text Processing"

_QUANTIFIER = re.compile(r"\{\d*(,\d*)?\}")


def _check_safe_pattern(pattern, text_length: int) -> None:
    """Refuse patterns that can make the regex engine run for minutes: nested repeats such as (a+)+,
    a repeated group with | inside, more than 2 open-ended repeats, a pattern over 200 characters, or
    text too long for the pattern. A search with k open-ended repeats costs about length^(k+1) steps,
    so the text limit is 100000 with none, 10000 with one and 1000 with two."""
    if not isinstance(pattern, str) or not pattern or len(pattern) > 200:
        raise CardError("invalid_input", "Pattern must be 1 to 200 characters.")
    groups = []          # one flag pair per open group: [has a repeat inside, has | inside]
    last_group = None    # the group that just closed, if the previous item was ")"
    open_ended = 0
    i, n = 0, len(pattern)
    while i < n:
        ch = pattern[i]
        group_closed, last_group = last_group, None
        if ch == "\\":
            i += 2
            continue
        if ch == "[":
            i += 2 if pattern[i + 1:i + 2] == "^" else 1
            i += 1   # a "]" right after "[" or "[^" is a letter
            while i < n and pattern[i] != "]":
                i += 2 if pattern[i] == "\\" else 1
            i += 1
            continue
        if ch == "(":
            groups.append([False, False])
            if pattern[i + 1:i + 2] == "?":   # (?: (?= (?<name> (?i) ...: skip the marker, it is not a repeat
                i += 2
                while i < n and pattern[i] not in ":)=!>":
                    i += 1
                i += 0 if pattern[i:i + 1] == ")" else 1
                continue
        elif ch == ")":
            if groups:
                last_group = groups.pop()
                if groups:
                    groups[-1][0] = groups[-1][0] or last_group[0]
                    groups[-1][1] = groups[-1][1] or last_group[1]
        elif ch == "|":
            if groups:
                groups[-1][1] = True
        else:
            size = 1
            repeat = ch in "*+?"
            unbounded = ch in "*+"
            if ch == "{":
                m = _QUANTIFIER.match(pattern, i)
                if m:
                    size, repeat, unbounded = m.end() - i, True, m.group(1) == "," or m.group().endswith(",}")
            if repeat:
                if ch != "?" and group_closed and (group_closed[0] or group_closed[1]):
                    raise CardError("bad_expression", "Pattern repeats a group that already repeats or has choices; that can hang.")
                open_ended += unbounded
                if groups:
                    groups[-1][0] = True
                i += size
                if pattern[i:i + 1] in ("?", "+"):   # lazy or possessive mark
                    i += 1
                continue
        i += 1
    if open_ended > 2:
        raise CardError("bad_expression", "Pattern has more than 2 open-ended repeats (* + {n,}); that can hang.")
    limit = (MAX_TEXT_LENGTH, 10_000, 1_000)[open_ended]
    if text_length > limit:
        raise CardError("limit_exceeded", f"Text is too long for this pattern (limit {limit} characters).")


@card(
    "Split Text By Separator",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["values"],
    examples=[
        {
            "label": "comma separated",
            "args": {"text": "apple,banana,cherry", "separator": ","},
            "expect": {"values": ["apple", "banana", "cherry"]},
        },
        {
            "label": "tab separated",
            "args": {"text": "one\ttwo\tthree", "separator": "\t"},
            "expect": {"values": ["one", "two", "three"]},
        },
        {
            "label": "trim spaces",
            "args": {"text": " a , b , c ", "separator": ",", "trim": True},
            "expect": {"values": ["a", "b", "c"]},
        },
    ],
    invalid=[
        {"label": "a number is not text", "args": {"text": 5}, "code": "invalid_input"},
        {"label": "empty separator", "args": {"text": "a b", "separator": ""}, "code": "invalid_input"},
    ],
)
def split_text_by_separator(ctx, *, text, separator: str = ",", trim: bool = True) -> dict:
    """Splits text into separate values wherever a separator such as a comma, tab or vertical bar appears."""
    s = as_text(text, "text")
    if not isinstance(separator, str) or separator == "":
        raise CardError("invalid_input", "Separator must be at least one character.")
    parts = s.split(separator)
    if trim:
        parts = [p.strip() for p in parts]
    return {"values": parts}


@card(
    "Search Text For Pattern",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["found", "match"],
    examples=[
        {
            "label": "word found",
            "args": {"text": "The quick brown fox", "pattern": "quick"},
            "expect": {"found": True, "match": "quick"},
        },
        {
            "label": "case insensitive",
            "args": {"text": "HELLO", "pattern": "hello", "case_sensitive": False},
            "expect": {"found": True, "match": "HELLO"},
        },
        {
            "label": "not found",
            "args": {"text": "test", "pattern": "xyz"},
            "expect": {"found": False, "match": None},
        },
    ],
    invalid=[
        {
            "label": "bad regex",
            "args": {"text": "test", "pattern": "["},
            "code": "bad_expression",
        },
        {
            "label": "nested repeat could hang",
            "args": {"text": "a" * 28 + "!", "pattern": "(a+)+$"},
            "code": "bad_expression",
        },
        {
            "label": "text too long for a pattern with one repeat",
            "args": {"text": "a" * 10_001, "pattern": "a+"},
            "code": "limit_exceeded",
        },
    ],
)
def search_text_for_pattern(ctx, *, text, pattern: str, case_sensitive: bool = False) -> dict:
    """Finds whether a text field contains a specified word, phrase, or pattern.

    Limits (so a pattern cannot hang the app): pattern up to 200 characters; no repeated group that
    already repeats or holds a choice ("(a+)+", "(a|b)*"); at most 2 open-ended repeats (* + {n,});
    text up to 100000 characters with no open-ended repeat, 10000 with one, 1000 with two.
    """
    s = as_text(text, "text")
    _check_safe_pattern(pattern, len(s))
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        match = re.search(pattern, s, flags)
    except re.error:
        raise CardError("bad_expression", "Pattern is not valid.") from None
    if match:
        return {"found": True, "match": match.group()}
    return {"found": False, "match": None}


@card(
    "Replace Text In Field",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["text"],
    examples=[
        {
            "label": "replace word",
            "args": {"text": "cat and dog", "find": "dog", "replace": "fox"},
            "expect": {"text": "cat and fox"},
        },
        {
            "label": "all occurrences",
            "args": {"text": "a a a", "find": "a", "replace": "b"},
            "expect": {"text": "b b b"},
        },
        {
            "label": "not found leaves unchanged",
            "args": {"text": "hello", "find": "xyz", "replace": "abc"},
            "expect": {"text": "hello"},
        },
    ],
    invalid=[
        {"label": "a number is not text", "args": {"text": 5, "find": "a"}, "code": "invalid_input"},
        {"label": "nothing to find", "args": {"text": "abc", "find": ""}, "code": "invalid_input"},
    ],
)
def replace_text_in_field(ctx, *, text, find: str, replace: str = "") -> dict:
    """Substitutes all occurrences of specified text with replacement text in a field."""
    s = as_text(text, "text")
    if not isinstance(find, str) or find == "":
        raise CardError("invalid_input", "Say which text to find.")
    return {"text": s.replace(find, replace)}


@card(
    "Split Text Into Lines",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["lines"],
    examples=[
        {
            "label": "three lines",
            "args": {"text": "line1\nline2\nline3"},
            "expect": {"lines": ["line1", "line2", "line3"]},
        },
        {
            "label": "blank lines removed",
            "args": {"text": "a\n\nb\n", "skip_blank": True},
            "expect": {"lines": ["a", "b"]},
        },
        {
            "label": "blank lines kept",
            "args": {"text": "a\n\nb", "skip_blank": False},
            "expect": {"lines": ["a", "", "b"]},
        },
    ],
    invalid=[{"label": "a number is not text", "args": {"text": 5}, "code": "invalid_input"}],
)
def split_text_into_lines(ctx, *, text, skip_blank: bool = True) -> dict:
    """Breaks multi-line text into separate strings, one per line, for individual processing."""
    s = as_text(text, "text")
    lines = s.splitlines()
    if skip_blank:
        lines = [ln for ln in lines if ln.strip()]
    return {"lines": lines}


@card(
    "Fill Text Template",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["text"],
    examples=[
        {
            "label": "simple placeholder",
            "args": {"record": {"name": "Anna"}, "template": "Hello {name}!"},
            "expect": {"text": "Hello Anna!"},
        },
        {
            "label": "multiple fields",
            "args": {
                "record": {"first": "John", "last": "Doe"},
                "template": "{first} {last}",
            },
            "expect": {"text": "John Doe"},
        },
        {
            "label": "missing field is blank",
            "args": {"record": {"a": "X"}, "template": "{a} {b}"},
            "expect": {"text": "X "},
        },
    ],
    invalid=[
        {"label": "record is not a record", "args": {"record": "x", "template": "{a}"}, "code": "invalid_input"},
        {"label": "template is not text", "args": {"record": {}, "template": 5}, "code": "invalid_input"},
    ],
)
def fill_text_template(ctx, *, record, template: str = "{value}") -> dict:
    """Inserts field values into a template with placeholders to generate formatted text output."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a record.")
    if not isinstance(template, str):
        raise CardError("invalid_input", "Template must be text.")
    def value_for(match) -> str:
        value = get_field(record, match.group(1), "")
        return "" if value is None else str(value)

    # one pass over the template: a value that itself contains {braces} is never filled again
    return {"text": re.sub(r"\{([a-zA-Z0-9_.]+)\}", value_for, template)}


@card(
    "Extract Number From Text",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["number"],
    examples=[
        {
            "label": "integer",
            "args": {"text": "Order 123 shipped"},
            "expect": {"number": 123},
        },
        {
            "label": "decimal",
            "args": {"text": "Price is $19.99 each"},
            "expect": {"number": 19.99},
        },
        {
            "label": "negative",
            "args": {"text": "Temperature: -5 degrees"},
            "expect": {"number": -5},
        },
    ],
    invalid=[
        {
            "label": "no number found",
            "args": {"text": "no digits here"},
            "code": "not_a_number",
        },
    ],
)
def extract_number_from_text(ctx, *, text) -> dict:
    """Finds the first whole or decimal number in a text field and ignores the other characters."""
    s = as_text(text, "text")
    match = re.search(r"-?\d+(?:\.\d+)?", s)
    if not match:
        raise CardError("not_a_number", "No number found in text.")
    num = try_number(match.group())
    if num is None:
        raise CardError("not_a_number", "No number found in text.")
    return {"number": num}


@card(
    "Remove Special Characters",
    category=CATEGORY,
    group=GROUP,
    inputs=["text"],
    outputs=["text"],
    examples=[
        {
            "label": "keep letters and numbers",
            "args": {"text": "Hello, World! 123"},
            "expect": {"text": "Hello World 123"},
        },
        {
            "label": "all special removed",
            "args": {"text": "@#$%^&*()"},
            "expect": {"text": ""},
        },
        {
            "label": "already clean",
            "args": {"text": "abc 123"},
            "expect": {"text": "abc 123"},
        },
    ],
    invalid=[{"label": "a number is not text", "args": {"text": 5}, "code": "invalid_input"}],
)
def remove_special_characters(ctx, *, text) -> dict:
    """Strips out non-alphanumeric characters from text, keeping only letters, numbers, and spaces."""
    s = as_text(text, "text")
    return {"text": re.sub(r"[^a-zA-Z0-9\s]", "", s)}


@card(
    "Label Text By Keywords",
    category=CATEGORY,
    group=GROUP,
    inputs=["record"],
    outputs=["record"],
    examples=[
        {
            "label": "match found",
            "args": {
                "record": {"note": "urgent delivery needed"},
                "field": "note",
                "keywords": {"urgent": "High Priority", "normal": "Standard"},
                "label_field": "priority",
            },
            "expect": {"record": {"note": "urgent delivery needed", "priority": "High Priority"}},
        },
        {
            "label": "no match gives default",
            "args": {
                "record": {"text": "nothing here"},
                "field": "text",
                "keywords": {"special": "Flag"},
                "label_field": "label",
                "default": "None",
            },
            "expect": {"record": {"text": "nothing here", "label": "None"}},
        },
        {
            "label": "case insensitive",
            "args": {
                "record": {"text": "URGENT"},
                "field": "text",
                "keywords": {"urgent": "High"},
                "label_field": "level",
            },
            "expect": {"record": {"text": "URGENT", "level": "High"}},
        },
    ],
    invalid=[
        {
            "label": "empty keywords",
            "args": {"record": {"x": "y"}, "field": "x", "keywords": {}},
            "code": "invalid_input",
        },
    ],
)
def label_text_by_keywords(
    ctx, *, record, field: str = "text", keywords: dict, label_field: str = "label", default: str = ""
) -> dict:
    """Gives each text record a label by matching keywords from a list the builder sets."""
    if not keywords:
        raise CardError("invalid_input", "At least one keyword is required.")
    rec = dict(record)
    text = str(get_field(rec, field, "")).lower()
    label = default
    for keyword, tag in keywords.items():
        if keyword.lower() in text:
            label = tag
            break
    rec[label_field] = label
    return {"record": rec}
