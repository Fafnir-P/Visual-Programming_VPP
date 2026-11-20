"""Shared runtime for the card templates. Python 3.13, standard library only.

What lives here (every card template builds on these, nothing else is needed):

* CardError            expected, user-fixable failure (code + message)
* Context              what a card receives as its first argument
* card / REGISTRY      the decorator that records a card's contract
* Store                small SQLite wrapper for the app's saved data
* conditions           one filter language for lists AND saved data
* coerce_value         one place that turns raw input into a clean value
* view                 declarative view nodes (dicts) for UI cards
* helpers              numbers, dates, dotted fields, safe arithmetic

Rules the templates follow (framework sections 4, 4.1, 5.1, 6.1 to 6.3):

* A card is a function ``name(ctx, *, input..., config=default...) -> dict``.
  It returns a dict of named outputs. Routing cards return
  ``{"route": <port>, "value": <record>}``.
* Cards never call outside services and never touch the file system. File
  cards take file text in and give file text out; the trusted shell handles
  the actual files.
* Cards never open their own top-level transaction. The engine wraps one
  event in ``ctx.store.transaction()`` and calls ``ctx.store.apply_once``.
  Multi-step cards may use ``with ctx.store.transaction():`` (it nests).
* Failures raise CardError. The engine rolls the event back and follows the
  card's error path.
"""
from __future__ import annotations

import ast
import contextlib
import dataclasses
import datetime as dt
import inspect
import json
import math
import re
import sqlite3
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Iterator

# ---------------------------------------------------------------------------
# Limits (the platform may tighten these; templates never loosen them)
# ---------------------------------------------------------------------------

MAX_LOOP_ITEMS = 10_000        # most items one loop card may handle
MAX_IMPORT_BYTES = 5_000_000   # largest file text an import card accepts
MAX_IMPORT_ROWS = 50_000
MAX_TEXT_LENGTH = 100_000


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class CardError(Exception):
    """An expected failure the user can fix (bad input, rule broken, not found).

    ``code`` is a short stable word such as ``required`` or ``not_found``.
    """

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


# ---------------------------------------------------------------------------
# Small value helpers
# ---------------------------------------------------------------------------

def csv_safe_cell(value: Any) -> Any:
    """Make a cell safe to open in a spreadsheet: text that starts with = + - @ (or a tab or
    carriage return) would run as a formula, so it gets a leading apostrophe. Numbers are left alone."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def is_blank(value: Any) -> bool:
    """True for None, empty or whitespace-only text, and empty lists/dicts."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


_NUMBER_WITH_COMMAS = re.compile(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$")


def to_number(value: Any, name: str = "value") -> int | float:
    """Turn a number or numeric text into int/float. Raises ``not_a_number``."""
    if isinstance(value, bool):
        raise CardError("not_a_number", f"{name} must be a number.")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise CardError("not_a_number", f"{name} must be a finite number.")
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if _NUMBER_WITH_COMMAS.match(text):
            text = text.replace(",", "")
        try:
            if re.fullmatch(r"[+-]?\d+", text):
                return int(text)
            number = float(text)
        except ValueError:
            raise CardError("not_a_number", f"{name} must be a number.") from None
        if not math.isfinite(number):
            raise CardError("not_a_number", f"{name} must be a finite number.")
        return number
    raise CardError("not_a_number", f"{name} must be a number.")


def as_int(value: Any, name: str = "value") -> int:
    """A whole number (a float like 2.0 is accepted). Text, true/false and 0.5 raise ``invalid_input``."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise CardError("invalid_input", f"{name} must be a whole number.")


def as_text(value: Any, name: str = "value") -> str:
    """Text in, text out. None gives "". Anything that is not text raises ``invalid_input``."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise CardError("invalid_input", f"{name} must be text.")
    return value


def try_number(value: Any) -> int | float | None:
    try:
        return to_number(value)
    except CardError:
        return None


def to_decimal(value: Any, name: str = "value") -> Decimal:
    number = to_number(value, name)
    try:
        return Decimal(str(number))
    except InvalidOperation:
        raise CardError("not_a_number", f"{name} must be a number.") from None


def round_half_up(value: Any, places: int = 2) -> float:
    """Round the way people do on paper (2.675 -> 2.68), not banker's rounding."""
    quant = Decimal(1).scaleb(-places)
    return float(to_decimal(value).quantize(quant, rounding=ROUND_HALF_UP))


def to_date(value: Any, name: str = "date") -> dt.date:
    """Accept a date, a datetime, 'YYYY-MM-DD' or an ISO date-time string."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        text = value.strip().replace("/", "-")
        try:
            return dt.date.fromisoformat(text[:10])
        except ValueError:
            pass
    raise CardError("not_a_date", f"{name} must be a date such as 2026-01-31.")


def to_datetime(value: Any, name: str = "date and time") -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip().replace("/", "-")
        try:
            return dt.datetime.fromisoformat(text)
        except ValueError:
            pass
        try:
            d = dt.date.fromisoformat(text[:10])
            return dt.datetime(d.year, d.month, d.day)
        except ValueError:
            pass
    raise CardError("not_a_date", f"{name} must be a date or a date and time such as 2026-01-31T09:30:00.")


def iso(value: Any) -> str:
    """Date -> 'YYYY-MM-DD', datetime -> 'YYYY-MM-DDTHH:MM:SS'."""
    if isinstance(value, dt.datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def get_field(record: dict, path: str, default: Any = None) -> Any:
    """Read ``a`` or ``a.b.c`` from nested dicts. Missing -> default."""
    current: Any = record
    for part in str(path).split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def snake(text: str) -> str:
    """'Enter Text' -> 'enter_text'."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def bounded(items: Iterable[Any], limit: int = MAX_LOOP_ITEMS, what: str = "items") -> list:
    """Make a list and refuse more than ``limit`` items (loops must be bounded)."""
    out = list(items)
    if len(out) > limit:
        raise CardError("limit_exceeded", f"Too many {what}: {len(out)} (limit {limit}).")
    return out


def require_keys(data: Any, keys: Iterable[str], what: str = "input") -> None:
    if not isinstance(data, dict):
        raise CardError("invalid_input", f"{what} must be a record.")
    missing = [k for k in keys if k not in data]
    if missing:
        raise CardError("missing_field", f"{what} is missing: {', '.join(missing)}.", {"fields": missing})


# ---------------------------------------------------------------------------
# Safe arithmetic (no eval): used by calculated fields and calculation cards
# ---------------------------------------------------------------------------

_SAFE_FUNCS: dict[str, Callable[..., Any]] = {"min": min, "max": max, "abs": abs, "round": round}
_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}


def safe_eval(expression: str, names: dict[str, Any] | None = None) -> int | float:
    """Evaluate ``qty * price - discount`` style arithmetic. Numbers, names,
    + - * / // %, brackets, and min/max/abs/round only."""
    names = names or {}
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 200:
        raise CardError("bad_expression", "Formula must be 1 to 200 characters.")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError:
        raise CardError("bad_expression", "Formula could not be read.") from None

    def walk(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise CardError("unknown_name", f"Formula uses an unknown field: {node.id}.")
            return to_number(names[node.id], node.id)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = walk(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _SAFE_FUNCS and not node.keywords):
            return _SAFE_FUNCS[node.func.id](*[walk(a) for a in node.args])
        raise CardError("bad_expression", "Formula uses something that is not allowed.")

    try:
        result = walk(tree)
    except ZeroDivisionError:
        raise CardError("divide_by_zero", "Formula divides by zero.") from None
    except (TypeError, OverflowError, ValueError):
        raise CardError("bad_expression", "Formula could not be worked out.") from None
    if isinstance(result, float) and not math.isfinite(result):
        raise CardError("bad_expression", "Formula result is not a finite number.")
    return result


# ---------------------------------------------------------------------------
# One place that cleans and checks a single value
# ---------------------------------------------------------------------------

FIELD_TYPES = ("text", "number", "integer", "bool", "date", "datetime", "time",
               "choice", "multichoice", "email", "phone", "currency")

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(:([0-5]\d))?$")
_TRUE = {"true", "yes", "y", "1", "on"}
_FALSE = {"false", "no", "n", "0", "off"}


def coerce_value(spec: dict, value: Any, name: str = "value") -> Any:
    """Clean ``value`` according to ``spec`` or raise CardError.

    spec keys (all optional): type, required, choices, min, max, min_length,
    max_length, pattern, strip. Blank values give None unless ``required``.
    Dates come back as 'YYYY-MM-DD', date-times as ISO text, times as 'HH:MM'.
    """
    kind = spec.get("type", "text")
    if kind not in FIELD_TYPES:
        raise CardError("bad_type", f"Unknown field type: {kind}.")
    if is_blank(value):
        if spec.get("required"):
            raise CardError("required", f"{name} is required.", {"field": name})
        return False if kind == "bool" else None

    def check_range(number: Any, label: str) -> None:
        low, high = spec.get("min"), spec.get("max")
        if low is not None and number < low:
            raise CardError("too_small", f"{name} must be at least {low}.", {"field": name})
        if high is not None and number > high:
            raise CardError("too_large", f"{name} must be at most {high}.", {"field": name})

    if kind in ("text", "email", "phone"):
        text = value if isinstance(value, str) else str(value)
        if spec.get("strip", True):
            text = text.strip()
        if len(text) > MAX_TEXT_LENGTH:
            raise CardError("too_long", f"{name} is too long.", {"field": name})
        if kind == "email":
            text = text.lower()
            if not _EMAIL.match(text):
                raise CardError("bad_format", f"{name} must be an email address.", {"field": name})
        if kind == "phone":
            if not re.fullmatch(r"[+()\-.\s\d]+", text) or not 7 <= len(re.sub(r"\D", "", text)) <= 15:
                raise CardError("bad_format", f"{name} must be a phone number.", {"field": name})
        if spec.get("min_length") is not None and len(text) < spec["min_length"]:
            raise CardError("too_short", f"{name} needs at least {spec['min_length']} characters.", {"field": name})
        if spec.get("max_length") is not None and len(text) > spec["max_length"]:
            raise CardError("too_long", f"{name} can have at most {spec['max_length']} characters.", {"field": name})
        if spec.get("pattern") and not re.fullmatch(spec["pattern"], text):
            raise CardError("bad_format", f"{name} is not in the expected format.", {"field": name})
        if spec.get("choices") and text not in spec["choices"]:
            raise CardError("not_allowed", f"{name} is not one of the allowed values.", {"field": name})
        return text

    if kind in ("number", "currency", "integer"):
        number = to_number(value, name)
        if kind == "integer":
            if isinstance(number, float):
                if not number.is_integer():
                    raise CardError("not_an_integer", f"{name} must be a whole number.", {"field": name})
                number = int(number)
        elif kind == "currency":
            number = round_half_up(number, 2)
        check_range(number, name)
        return number

    if kind == "bool":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        raise CardError("not_a_bool", f"{name} must be yes or no.", {"field": name})

    if kind == "date":
        text = to_date(value, name).isoformat()
        if spec.get("min") is not None and text < to_date(spec["min"]).isoformat():
            raise CardError("too_small", f"{name} must be on or after {spec['min']}.", {"field": name})
        if spec.get("max") is not None and text > to_date(spec["max"]).isoformat():
            raise CardError("too_large", f"{name} must be on or before {spec['max']}.", {"field": name})
        return text

    if kind == "datetime":
        text = iso(to_datetime(value, name))
        if spec.get("min") is not None and text < iso(to_datetime(spec["min"])):
            raise CardError("too_small", f"{name} must be at or after {spec['min']}.", {"field": name})
        if spec.get("max") is not None and text > iso(to_datetime(spec["max"])):
            raise CardError("too_large", f"{name} must be at or before {spec['max']}.", {"field": name})
        return text

    if kind == "time":
        match = _TIME.match(str(value).strip())
        if not match:
            raise CardError("not_a_time", f"{name} must be a time such as 14:30.", {"field": name})
        text = f"{int(match.group(1)):02d}:{match.group(2)}" + (f":{match.group(4)}" if match.group(4) else "")
        for bound, code, word in (("min", "too_small", "at or after"), ("max", "too_large", "at or before")):
            if spec.get(bound) is not None:
                limit = _TIME.match(str(spec[bound]).strip())
                limit_text = f"{int(limit.group(1)):02d}:{limit.group(2)}" if limit else str(spec[bound])
                if (text[:5] < limit_text) if bound == "min" else (text[:5] > limit_text):
                    raise CardError(code, f"{name} must be {word} {spec[bound]}.", {"field": name})
        return text

    if kind == "choice":
        choices = spec.get("choices") or []
        text = str(value).strip()
        for option in choices:
            if str(option).casefold() == text.casefold():
                return option
        raise CardError("not_allowed", f"{name} must be one of: {', '.join(map(str, choices))}.", {"field": name})

    if kind == "multichoice":
        choices = spec.get("choices") or []
        items = value if isinstance(value, (list, tuple)) else [value]
        out: list[Any] = []
        for item in items:
            match = next((o for o in choices if str(o).casefold() == str(item).strip().casefold()), None)
            if match is None:
                raise CardError("not_allowed", f"{name} has a value that is not allowed: {item}.", {"field": name})
            if match not in out:
                out.append(match)
        if spec.get("min_length") is not None and len(out) < spec["min_length"]:
            raise CardError("too_short", f"{name} needs at least {spec['min_length']} choices.", {"field": name})
        if spec.get("max_length") is not None and len(out) > spec["max_length"]:
            raise CardError("too_long", f"{name} can have at most {spec['max_length']} choices.", {"field": name})
        return out

    raise CardError("bad_type", f"Unknown field type: {kind}.")  # pragma: no cover


def validate_against(schema: dict[str, dict], data: dict) -> dict[str, Any]:
    """Check a whole record against ``{field: spec}``. Returns the cleaned
    record or raises CardError('invalid_record') listing every problem."""
    if not isinstance(data, dict):
        raise CardError("invalid_input", "Expected a record.")
    problems: list[dict] = []
    cleaned: dict[str, Any] = {}
    for field_name, spec in schema.items():
        try:
            cleaned[field_name] = coerce_value(spec, data.get(field_name), field_name)
        except CardError as err:
            problems.append({"field": field_name, "code": err.code, "message": err.message})
    unknown = [k for k in data if k not in schema]
    for key in unknown:
        problems.append({"field": key, "code": "unknown_field", "message": f"{key} is not expected."})
    if problems:
        raise CardError("invalid_record", f"{len(problems)} problem(s) found.", {"problems": problems})
    return cleaned


# ---------------------------------------------------------------------------
# Conditions: one filter language for lists and for saved data
# ---------------------------------------------------------------------------
#   {"field": "status", "op": "eq", "value": "shipped"}
#   {"all": [cond, cond]}     {"any": [cond, cond]}
# ops: eq ne gt gte lt lte contains startswith endswith in not_in is_empty not_empty between
# Text is compared ignoring upper/lower case. Numbers compare as numbers.

OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "contains", "startswith", "endswith",
       "in", "not_in", "is_empty", "not_empty", "between")
_NO_VALUE_OPS = {"is_empty", "not_empty"}
_META_FIELDS = ("id", "_version", "_created_at", "_updated_at", "_archived")


def validate_condition(cond: Any, allowed_fields: Iterable[str] | None = None, _depth: int = 0) -> None:
    if _depth > 8:
        raise CardError("invalid_condition", "Conditions are nested too deeply.")
    if not isinstance(cond, dict):
        raise CardError("invalid_condition", "A condition must be a record.")
    if "all" in cond or "any" in cond:
        key = "all" if "all" in cond else "any"
        if len(cond) != 1 or not isinstance(cond[key], list):
            raise CardError("invalid_condition", f"'{key}' must hold a list of conditions.")
        for sub in cond[key]:
            validate_condition(sub, allowed_fields, _depth + 1)
        return
    if "field" not in cond or not isinstance(cond["field"], str) or not cond["field"]:
        raise CardError("invalid_condition", "A condition needs a 'field'.")
    op = cond.get("op")
    if op not in OPS:
        raise CardError("invalid_condition", f"Unknown operator: {op}.")
    if op not in _NO_VALUE_OPS and "value" not in cond:
        raise CardError("invalid_condition", f"Operator '{op}' needs a 'value'.")
    if op in ("in", "not_in") and not isinstance(cond["value"], (list, tuple)):
        raise CardError("invalid_condition", f"Operator '{op}' needs a list.")
    if op == "between" and not (isinstance(cond["value"], (list, tuple)) and len(cond["value"]) == 2):
        raise CardError("invalid_condition", "Operator 'between' needs [low, high].")
    if allowed_fields is not None and cond["field"] not in set(allowed_fields):
        raise CardError("unknown_field", f"Unknown field: {cond['field']}.", {"field": cond["field"]})


def _pair(a: Any, b: Any) -> tuple[Any, Any] | None:
    """Make two values comparable: numbers as numbers, text ignoring case."""
    if isinstance(a, bool) or isinstance(b, bool):
        return (a, b) if isinstance(a, bool) and isinstance(b, bool) else None
    na, nb = try_number(a), try_number(b)
    if na is not None and nb is not None:
        return na, nb
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().casefold(), b.strip().casefold()
    return None


def _equal(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    pair = _pair(a, b)
    return pair is not None and pair[0] == pair[1]


def matches(record: dict, cond: dict) -> bool:
    """Does ``record`` satisfy ``cond``? (in-memory evaluation)"""
    validate_condition(cond)
    if "all" in cond:
        return all(matches(record, c) for c in cond["all"])
    if "any" in cond:
        return any(matches(record, c) for c in cond["any"])
    value = get_field(record, cond["field"])
    op = cond["op"]
    target = cond.get("value")
    if op == "is_empty":
        return is_blank(value)
    if op == "not_empty":
        return not is_blank(value)
    if op == "eq":
        return _equal(value, target)
    if op == "ne":
        return not _equal(value, target)
    if op == "in":
        return any(_equal(value, t) for t in target)
    if op == "not_in":
        return not any(_equal(value, t) for t in target)
    if op in ("contains", "startswith", "endswith"):
        if value is None:
            return False
        needle = str(target).casefold()
        if isinstance(value, (list, tuple)):
            return op == "contains" and any(str(v).casefold() == needle for v in value)
        hay = str(value).casefold()
        return (needle in hay if op == "contains"
                else hay.startswith(needle) if op == "startswith" else hay.endswith(needle))
    if op == "between":
        low, high = _pair(value, target[0]), _pair(value, target[1])
        return bool(low and high and low[0] >= low[1] and high[0] <= high[1])
    pair = _pair(value, target)
    if pair is None:
        return False
    a, b = pair
    return a > b if op == "gt" else a >= b if op == "gte" else a < b if op == "lt" else a <= b


def _ux_name(table: str, field: str) -> str:
    """Unique-index name. ":" cannot appear in an identifier, so (a_b, c) and (a, b_c) differ."""
    return "ux:" + table + ":" + field


def _q(name: str) -> str:
    return '"' + name + '"'


def _like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def compile_condition(cond: dict, allowed_fields: Iterable[str], multi_fields: Iterable[str] = ()) -> tuple[str, list]:
    """Turn a condition into ``(sql, params)``. Field names must be in
    ``allowed_fields``; values are always parameters, never pasted in.
    ``multi_fields`` are multichoice fields (saved as a JSON list): ``contains`` then
    means "has this whole choice", the same as in memory."""
    allowed = set(allowed_fields)
    multi = set(multi_fields)
    validate_condition(cond, allowed)

    def param(v: Any) -> Any:
        return int(v) if isinstance(v, bool) else v

    def one(c: dict) -> tuple[str, list]:
        if "all" in c or "any" in c:
            key = "all" if "all" in c else "any"
            parts = [one(s) for s in c[key]]
            if not parts:
                return ("1", []) if key == "all" else ("0", [])
            joiner = " AND " if key == "all" else " OR "
            return "(" + joiner.join(p[0] for p in parts) + ")", [x for p in parts for x in p[1]]
        col, op, v = _q(c["field"]), c["op"], c.get("value")
        if op == "is_empty":
            return f"({col} IS NULL OR TRIM(CAST({col} AS TEXT)) = '')", []
        if op == "not_empty":
            return f"({col} IS NOT NULL AND TRIM(CAST({col} AS TEXT)) <> '')", []
        if op == "eq":
            return (f"{col} IS NULL", []) if v is None else (f"{col} = ? COLLATE NOCASE", [param(v)])
        if op == "ne":
            return (f"{col} IS NOT NULL", []) if v is None else (f"({col} IS NULL OR {col} <> ? COLLATE NOCASE)", [param(v)])
        if op in ("in", "not_in"):
            if not v:
                return ("0", []) if op == "in" else ("1", [])
            inner = " OR ".join(f"{col} = ? COLLATE NOCASE" for _ in v)
            if op == "in":
                return f"({inner})", [param(x) for x in v]
            return f"({col} IS NULL OR NOT ({inner}))", [param(x) for x in v]
        if op == "contains" and c["field"] in multi:
            return f"LOWER(CAST({col} AS TEXT)) LIKE ? ESCAPE '\\'", ["%" + _like(json.dumps(str(v).casefold())) + "%"]
        if op in ("contains", "startswith", "endswith"):
            text = _like(str(v).casefold())
            pattern = f"%{text}%" if op == "contains" else f"{text}%" if op == "startswith" else f"%{text}"
            return f"LOWER(CAST({col} AS TEXT)) LIKE ? ESCAPE '\\'", [pattern]
        if op == "between":
            return f"{col} BETWEEN ? AND ?", [param(v[0]), param(v[1])]
        sign = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[op]
        return f"{col} {sign} ? COLLATE NOCASE", [param(v)]

    return one(cond)


# ---------------------------------------------------------------------------
# Declarative view nodes for UI cards (never HTML; the platform renders them)
# ---------------------------------------------------------------------------

VIEW_NAMESPACES = ("layout", "input", "display", "action", "dialog", "nav", "print")
_VIEW_KIND = re.compile(r"^(" + "|".join(VIEW_NAMESPACES) + r")\.[a-z][a-z0-9_]*$")
_FORBIDDEN_PROPS = {"html", "script", "style", "css", "js", "javascript", "src", "href", "url", "innerhtml"}
_FORBIDDEN_END = re.compile(r"(url|href|src|html|uri)$")


def view(kind: str, *, id: str | None = None, children: list[dict] | None = None,
         props: dict | None = None, **extra: Any) -> dict:
    """Build a view node: ``{"kind", "id", "props", "children"}``.

    Only JSON-friendly props. No HTML, scripts, styles, URLs or event handlers
    (framework 6.1: the platform renders validated declarative data).
    """
    if not isinstance(kind, str) or not _VIEW_KIND.match(kind):
        raise CardError("invalid_view", f"View kind must look like 'input.text' (got {kind!r}).")
    if props is not None and not isinstance(props, dict):
        raise CardError("invalid_view", "props must be a record.")
    props = {**(props or {}), **extra}
    for key in props:
        low = key.lower()
        if low in _FORBIDDEN_PROPS or _FORBIDDEN_END.search(low) or re.match(r"on[a-z]", low):
            raise CardError("invalid_view", f"View property not allowed: {key}.")
    try:
        json.dumps(props)
    except (TypeError, ValueError):
        raise CardError("invalid_view", "View properties must be plain data.") from None
    kids = children or []
    for child in kids:
        if not (isinstance(child, dict) and {"kind", "props", "children"} <= set(child)):
            raise CardError("invalid_view", "Children must be view nodes.")
    return {"kind": kind, "id": id, "props": props, "children": kids}


# ---------------------------------------------------------------------------
# Store: the app's saved data (SQLite)
# ---------------------------------------------------------------------------

_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def check_identifier(name: Any, what: str = "name") -> str:
    """Table and field names: letters, digits, underscore; start with a letter."""
    if not isinstance(name, str) or not _IDENT.match(name):
        raise CardError("bad_name", f"A {what} must start with a letter and use only letters, digits and underscores.")
    return name


_SQL_TYPE = {"text": "TEXT", "email": "TEXT", "phone": "TEXT", "choice": "TEXT", "multichoice": "TEXT",
             "date": "TEXT", "datetime": "TEXT", "time": "TEXT",
             "number": "REAL", "currency": "REAL", "integer": "INTEGER", "bool": "INTEGER"}


class Store:
    """SQLite wrapper. Names are whitelisted, values are always parameters."""

    def __init__(self, path: str = ":memory:"):
        self._db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._depth = 0
        self.clock: Callable[[], dt.datetime] = dt.datetime.now
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS _vp_tables(name TEXT PRIMARY KEY, schema TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS _vp_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT, tbl TEXT NOT NULL, rec_id INTEGER NOT NULL,
                version INTEGER NOT NULL, changed_at TEXT NOT NULL, action TEXT NOT NULL,
                before TEXT, after TEXT);
            CREATE TABLE IF NOT EXISTS _vp_applied_events(event_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS _vp_counters(name TEXT PRIMARY KEY, value INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS _vp_outbox(
                key TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, instructions TEXT NOT NULL,
                expected_schema TEXT, source TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, result TEXT);
            CREATE TABLE IF NOT EXISTS _vp_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, message TEXT NOT NULL,
                details TEXT, at TEXT NOT NULL);
        """)

    def close(self) -> None:
        self._db.close()

    def __del__(self) -> None:
        try:
            self._db.close()
        except Exception:  # noqa: BLE001
            pass

    # -- transactions ------------------------------------------------------

    @property
    def in_transaction(self) -> bool:
        return self._depth > 0

    @contextlib.contextmanager
    def transaction(self) -> Iterator["Store"]:
        """Commit on success, roll back on any error. Nested calls use savepoints."""
        name = f"sp{self._depth}"
        self._db.execute("BEGIN IMMEDIATE" if self._depth == 0 else f"SAVEPOINT {name}")
        self._depth += 1
        try:
            yield self
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self._db.execute("ROLLBACK")
            else:
                self._db.execute(f"ROLLBACK TO {name}")
                self._db.execute(f"RELEASE {name}")
            raise
        else:
            self._depth -= 1
            self._db.execute("COMMIT" if self._depth == 0 else f"RELEASE {name}")

    def apply_once(self, event_id: str) -> bool:
        """Mark an event as applied. False means it was applied before (skip it).
        The engine calls this inside the event's transaction."""
        if not event_id:
            raise CardError("invalid_input", "An event needs an id.")
        with self.transaction():
            row = self._db.execute("SELECT 1 FROM _vp_applied_events WHERE event_id=?", (event_id,)).fetchone()
            if row:
                return False
            self._db.execute("INSERT INTO _vp_applied_events VALUES(?,?)", (event_id, iso(self.clock())))
            return True

    def next_counter(self, name: str) -> int:
        """1, 2, 3 ... per counter name (for reference numbers)."""
        check_identifier(name, "counter name")
        with self.transaction():
            self._db.execute("INSERT OR IGNORE INTO _vp_counters VALUES(?,0)", (name,))
            self._db.execute("UPDATE _vp_counters SET value=value+1 WHERE name=?", (name,))
            return self._db.execute("SELECT value FROM _vp_counters WHERE name=?", (name,)).fetchone()[0]

    # -- schema ------------------------------------------------------------

    def _user_table_name(self, name: Any) -> str:
        check_identifier(name, "table name")
        if name.lower().startswith(("sqlite", "vp_")):
            raise CardError("bad_name", "That table name is reserved.")
        return name

    def tables(self) -> list[str]:
        return [r["name"] for r in self._db.execute("SELECT name FROM _vp_tables ORDER BY name")]

    def schema(self, table: str) -> dict:
        row = self._db.execute("SELECT schema FROM _vp_tables WHERE name=?", (table,)).fetchone()
        if not row:
            raise CardError("no_such_table", f"There is no table called {table}.", {"table": table})
        return json.loads(row["schema"])

    def _save_schema(self, table: str, schema: dict) -> None:
        self._db.execute("INSERT OR REPLACE INTO _vp_tables VALUES(?,?)", (table, json.dumps(schema)))

    @staticmethod
    def _normalise_field(field: dict) -> dict:
        if not isinstance(field, dict):
            raise CardError("invalid_input", "A field must be a record.")
        name = check_identifier(field.get("name"), "field name")
        if name in _META_FIELDS:
            raise CardError("bad_name", f"{name} is reserved.")
        kind = field.get("type", "text")
        if kind not in FIELD_TYPES:
            raise CardError("bad_type", f"Unknown field type: {kind}.")
        out = {"name": name, "type": kind, "required": bool(field.get("required", False)),
               "unique": bool(field.get("unique", False)), "default": field.get("default")}
        for key in ("choices", "min", "max", "min_length", "max_length", "pattern", "references", "protect_delete", "computed"):
            if field.get(key) is not None:
                out[key] = field[key]
        if kind in ("choice", "multichoice") and not out.get("choices"):
            raise CardError("invalid_input", f"{name} needs a list of choices.")
        if out.get("references"):
            check_identifier(out["references"], "table name")
        if out.get("computed") is not None:
            expr = out["computed"].get("expr") if isinstance(out["computed"], dict) else None
            safe_eval(expr or "", {n: 1 for n in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr or "") if n not in _SAFE_FUNCS})
        return out

    def define_table(self, name: str, fields: list[dict], *, if_exists: str = "error") -> dict:
        """Create a table. if_exists: 'error' | 'skip'."""
        self._user_table_name(name)
        if name in self.tables():
            if if_exists == "skip":
                return self.schema(name)
            raise CardError("table_exists", f"Table {name} already exists.", {"table": name})
        if not isinstance(fields, list):
            raise CardError("invalid_input", "Fields must be a list (it may be empty; add fields later).")
        normal = [self._normalise_field(f) for f in fields]
        names = [f["name"] for f in normal]
        if len(set(names)) != len(names):
            raise CardError("duplicate_field", "Two fields have the same name.")
        with self.transaction():
            stored = [f for f in normal if "computed" not in f]
            columns = ", ".join(f"{_q(f['name'])} {_SQL_TYPE[f['type']]}" for f in stored)
            self._db.execute(
                f"CREATE TABLE {_q(name)} (id INTEGER PRIMARY KEY AUTOINCREMENT, _version INTEGER NOT NULL DEFAULT 1, "
                f"_created_at TEXT NOT NULL, _updated_at TEXT NOT NULL, _archived INTEGER NOT NULL DEFAULT 0"
                + (", " + columns if columns else "") + ")")
            for f in stored:
                if f["unique"]:
                    self._db.execute(f"CREATE UNIQUE INDEX {_q(_ux_name(name, f['name']))} ON {_q(name)}({_q(f['name'])} COLLATE NOCASE)")
            schema = {"name": name, "fields": normal, "history": None}
            self._save_schema(name, schema)
        return schema

    def add_field(self, table: str, field: dict) -> dict:
        schema = self.schema(table)
        normal = self._normalise_field(field)
        if any(f["name"] == normal["name"] for f in schema["fields"]):
            raise CardError("duplicate_field", f"{normal['name']} already exists.")
        with self.transaction():
            if "computed" not in normal:
                self._db.execute(f"ALTER TABLE {_q(table)} ADD COLUMN {_q(normal['name'])} {_SQL_TYPE[normal['type']]}")
                if normal["unique"]:
                    self._db.execute(f"CREATE UNIQUE INDEX {_q(_ux_name(table, normal['name']))} ON {_q(table)}({_q(normal['name'])} COLLATE NOCASE)")
            schema["fields"].append(normal)
            self._save_schema(table, schema)
        return schema

    _CHANGEABLE = ("default", "required", "unique", "choices", "min", "max", "min_length", "max_length",
                   "pattern", "references", "protect_delete")

    def update_field(self, table: str, name: str, changes: dict) -> dict:
        """Change the rules of an existing field (default, required, unique, choices, limits, link).
        The type and name cannot change. Making a field unique fails if it already has repeats."""
        schema = self.schema(table)
        index = next((i for i, f in enumerate(schema["fields"]) if f["name"] == name), None)
        if index is None:
            raise CardError("unknown_field", f"{table} has no field {name}.", {"field": name})
        if not isinstance(changes, dict) or not changes:
            raise CardError("invalid_input", "Nothing to change.")
        for key in changes:
            if key not in self._CHANGEABLE:
                raise CardError("invalid_input", f"{key} cannot be changed on an existing field.", {"field": key})
        old = schema["fields"][index]
        merged = {**old, **changes}
        for key in [k for k, v in merged.items() if v is None and k in self._CHANGEABLE]:
            merged.pop(key)
        new = self._normalise_field(merged)
        with self.transaction():
            if "computed" not in new and new["unique"] != old.get("unique", False):
                index_name = _q(_ux_name(table, name))
                if new["unique"]:
                    try:
                        self._db.execute(f"CREATE UNIQUE INDEX {index_name} ON {_q(table)}({_q(name)} COLLATE NOCASE)")
                    except sqlite3.IntegrityError:
                        raise CardError("duplicate_value", f"{name} has repeated values, so it cannot be made unique.",
                                        {"field": name}) from None
                else:
                    self._db.execute(f"DROP INDEX IF EXISTS {index_name}")
            schema["fields"][index] = new
            self._save_schema(table, schema)
        return schema
    def enable_history(self, table: str, keep: int = 10) -> dict:
        if not isinstance(keep, int) or not 1 <= keep <= 100:
            raise CardError("invalid_input", "Keep between 1 and 100 versions.")
        schema = self.schema(table)
        schema["history"] = {"keep": keep}
        self._save_schema(table, schema)
        return schema

    @staticmethod
    def _multi_fields(schema: dict) -> list[str]:
        return [f["name"] for f in schema["fields"] if f.get("type") == "multichoice"]

    def field_names(self, table: str, *, include_computed: bool = False) -> list[str]:
        schema = self.schema(table)
        names = [f["name"] for f in schema["fields"] if include_computed or "computed" not in f]
        return list(_META_FIELDS) + names

    # -- reading and writing -----------------------------------------------

    def _decode(self, schema: dict, row: sqlite3.Row) -> dict:
        rec = dict(row)
        rec["_archived"] = bool(rec["_archived"])
        for f in schema["fields"]:
            if "computed" in f:
                continue
            value = rec.get(f["name"])
            if value is None:
                continue
            if f["type"] == "bool":
                rec[f["name"]] = bool(value)
            elif f["type"] == "multichoice":
                rec[f["name"]] = json.loads(value)
        for f in schema["fields"]:
            if "computed" in f:
                try:
                    rec[f["name"]] = safe_eval(f["computed"]["expr"], {k: v for k, v in rec.items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
                except CardError:
                    rec[f["name"]] = None
        return rec

    def _encode(self, schema: dict, rec: dict) -> dict:
        out: dict[str, Any] = {}
        types = {f["name"]: f["type"] for f in schema["fields"]}
        for key, value in rec.items():
            if value is None:
                out[key] = None
            elif types.get(key) == "multichoice":
                out[key] = json.dumps(value)
            elif isinstance(value, bool):
                out[key] = int(value)
            else:
                out[key] = value
        return out

    def _default(self, spec: dict) -> Any:
        default = spec.get("default")
        if default == "{today}":
            return self.clock().date().isoformat()
        if default == "{now}":
            return iso(self.clock())
        return default

    def _check_references(self, schema: dict, rec: dict) -> None:
        for f in schema["fields"]:
            ref = f.get("references")
            if ref and rec.get(f["name"]) is not None and self.get(ref, rec[f["name"]]) is None:
                raise CardError("missing_reference", f"{f['name']} points to a record in {ref} that does not exist.",
                                {"field": f["name"], "table": ref})

    def _check_unique(self, schema: dict, table: str, rec: dict, own_id: int | None) -> None:
        for f in schema["fields"]:
            if f.get("unique") and rec.get(f["name"]) is not None:
                row = self._db.execute(
                    f"SELECT id FROM {_q(table)} WHERE {_q(f['name'])} = ? COLLATE NOCASE", (self._encode(schema, rec)[f["name"]],)).fetchone()
                if row and row["id"] != own_id:
                    raise CardError("duplicate_value", f"{f['name']} must be unique; {rec[f['name']]} is already used.",
                                    {"field": f["name"]})

    def _log_history(self, schema: dict, table: str, rec_id: int, version: int, action: str, before: dict | None, after: dict | None) -> None:
        if not schema.get("history"):
            return
        self._db.execute("INSERT INTO _vp_history(tbl,rec_id,version,changed_at,action,before,after) VALUES(?,?,?,?,?,?,?)",
                         (table, rec_id, version, iso(self.clock()), action,
                          json.dumps(before) if before is not None else None, json.dumps(after) if after is not None else None))
        keep = schema["history"]["keep"]
        self._db.execute("DELETE FROM _vp_history WHERE tbl=? AND rec_id=? AND id NOT IN "
                         "(SELECT id FROM _vp_history WHERE tbl=? AND rec_id=? ORDER BY id DESC LIMIT ?)",
                         (table, rec_id, table, rec_id, keep))

    def insert(self, table: str, record: dict) -> dict:
        schema = self.schema(table)
        if not isinstance(record, dict):
            raise CardError("invalid_input", "A record must be a set of fields.")
        stored = {f["name"]: f for f in schema["fields"] if "computed" not in f}
        for key in record:
            if key not in stored:
                raise CardError("unknown_field", f"{table} has no field {key}.", {"field": key})
        clean = {name: coerce_value(spec, record.get(name, self._default(spec)), name) for name, spec in stored.items()}
        with self.transaction():
            self._check_unique(schema, table, clean, None)
            self._check_references(schema, clean)
            now = iso(self.clock())
            enc = self._encode(schema, clean)
            cols = ["_created_at", "_updated_at"] + list(enc)
            cur = self._db.execute(
                f"INSERT INTO {_q(table)} ({', '.join(_q(c) for c in cols)}) VALUES ({', '.join('?' * len(cols))})",
                [now, now] + list(enc.values()))
            created = self.get(table, cur.lastrowid)
            self._log_history(schema, table, created["id"], 1, "create", None, created)
            return created

    def insert_many(self, table: str, records: list[dict], limit: int = MAX_LOOP_ITEMS) -> list[dict]:
        """All records are stored, or none are. Import cards pass ``limit=MAX_IMPORT_ROWS``."""
        with self.transaction():
            return [self.insert(table, r) for r in bounded(records, limit, "records")]

    def get(self, table: str, record_id: Any) -> dict | None:
        schema = self.schema(table)
        try:
            rid = int(record_id)
        except (TypeError, ValueError):
            return None
        row = self._db.execute(f"SELECT * FROM {_q(table)} WHERE id=?", (rid,)).fetchone()
        return self._decode(schema, row) if row else None

    def update(self, table: str, record_id: Any, changes: dict, *, expected_version: int | None = None) -> dict:
        schema = self.schema(table)
        current = self.get(table, record_id)
        if current is None:
            raise CardError("not_found", f"No record {record_id} in {table}.", {"table": table, "id": record_id})
        if expected_version is not None and current["_version"] != expected_version:
            raise CardError("version_conflict", "The record changed since it was read.",
                            {"expected": expected_version, "found": current["_version"]})
        if not isinstance(changes, dict) or not changes:
            raise CardError("invalid_input", "Nothing to change.")
        stored = {f["name"]: f for f in schema["fields"] if "computed" not in f}
        clean = {}
        for key, value in changes.items():
            if key not in stored:
                raise CardError("unknown_field", f"{table} has no field {key}.", {"field": key})
            clean[key] = coerce_value(stored[key], value, key)
        with self.transaction():
            self._check_unique(schema, table, clean, current["id"])
            self._check_references(schema, clean)
            enc = self._encode(schema, clean)
            sets = ", ".join(f"{_q(c)}=?" for c in enc)
            version = current["_version"] + 1
            self._db.execute(f"UPDATE {_q(table)} SET {sets}, _version=?, _updated_at=? WHERE id=?",
                             list(enc.values()) + [version, iso(self.clock()), current["id"]])
            updated = self.get(table, current["id"])
            self._log_history(schema, table, current["id"], version, "update", current, updated)
            return updated

    def set_archived(self, table: str, record_id: Any, archived: bool) -> dict:
        current = self.get(table, record_id)
        if current is None:
            raise CardError("not_found", f"No record {record_id} in {table}.", {"table": table, "id": record_id})
        schema = self.schema(table)
        with self.transaction():
            version = current["_version"] + 1
            self._db.execute(f"UPDATE {_q(table)} SET _archived=?, _version=?, _updated_at=? WHERE id=?",
                             (int(archived), version, iso(self.clock()), current["id"]))
            updated = self.get(table, current["id"])
            self._log_history(schema, table, current["id"], version, "archive" if archived else "restore", current, updated)
            return updated

    def delete(self, table: str, record_id: Any) -> dict:
        schema = self.schema(table)
        current = self.get(table, record_id)
        if current is None:
            raise CardError("not_found", f"No record {record_id} in {table}.", {"table": table, "id": record_id})
        for other in self.tables():
            for f in self.schema(other)["fields"]:
                if f.get("references") == table and f.get("protect_delete"):
                    used = self._db.execute(f"SELECT COUNT(*) FROM {_q(other)} WHERE {_q(f['name'])}=?", (current["id"],)).fetchone()[0]
                    if used:
                        raise CardError("in_use", f"{used} record(s) in {other} still point to this record.",
                                        {"table": other, "field": f["name"], "count": used})
        with self.transaction():
            self._db.execute(f"DELETE FROM {_q(table)} WHERE id=?", (current["id"],))
            self._log_history(schema, table, current["id"], current["_version"] + 1, "delete", current, None)
        return current

    def find(self, table: str, where: dict | None = None, *, order_by: list | str | None = None,
             limit: int | None = None, offset: int = 0, include_archived: bool = False) -> list[dict]:
        schema = self.schema(table)
        sql, params = f"SELECT * FROM {_q(table)}", []
        clauses = [] if include_archived else ["_archived = 0"]
        allowed = self.field_names(table)
        if where:
            text, p = compile_condition(where, allowed, self._multi_fields(schema))
            clauses.append(text)
            params += p
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        if order_by:
            items = [order_by] if isinstance(order_by, (str, dict)) else list(order_by)
            parts = []
            for item in items:
                if isinstance(item, str):
                    item = {"field": item.lstrip("-"), "desc": item.startswith("-")}
                if item.get("field") not in allowed:
                    raise CardError("unknown_field", f"Cannot sort by {item.get('field')}.", {"field": item.get("field")})
                parts.append(f"{_q(item['field'])} COLLATE NOCASE {'DESC' if item.get('desc') else 'ASC'}")
            sql += " ORDER BY " + ", ".join(parts) + ", id ASC"
        else:
            sql += " ORDER BY id ASC"
        if limit is not None or offset:
            if limit is not None and (not isinstance(limit, int) or limit < 0):
                raise CardError("invalid_input", "Limit must be a whole number, 0 or more.")
            if not isinstance(offset, int) or offset < 0:
                raise CardError("invalid_input", "Offset must be a whole number, 0 or more.")
            sql += " LIMIT ? OFFSET ?"
            params += [-1 if limit is None else limit, offset]
        return [self._decode(schema, r) for r in self._db.execute(sql, params)]

    def count(self, table: str, where: dict | None = None, *, include_archived: bool = False) -> int:
        schema = self.schema(table)
        clauses = [] if include_archived else ["_archived = 0"]
        params: list = []
        if where:
            text, params = compile_condition(where, self.field_names(table), self._multi_fields(schema))
            clauses.append(text)
        sql = f"SELECT COUNT(*) FROM {_q(table)}" + (" WHERE " + " AND ".join(clauses) if clauses else "")
        return self._db.execute(sql, params).fetchone()[0]

    def history(self, table: str, record_id: Any) -> list[dict]:
        """Kept versions of one record, oldest first."""
        self.schema(table)
        rows = self._db.execute("SELECT * FROM _vp_history WHERE tbl=? AND rec_id=? ORDER BY id", (table, int(record_id))).fetchall()
        return [{"version": r["version"], "changed_at": r["changed_at"], "action": r["action"],
                 "before": json.loads(r["before"]) if r["before"] else None,
                 "after": json.loads(r["after"]) if r["after"] else None} for r in rows]

    # -- manual-action outbox (framework 5.1) -------------------------------

    def outbox_put(self, key: str, kind: str, payload: dict, instructions: str = "",
                   expected_schema: dict | None = None, source: dict | None = None) -> dict:
        """Add a waiting item. Same key twice returns the first one (safe to replay)."""
        if not isinstance(key, str) or not key or len(key) > 200:
            raise CardError("invalid_input", "An outbox item needs a key.")
        with self.transaction():
            existing = self.outbox_get(key)
            if existing:
                return existing
            now = iso(self.clock())
            self._db.execute("INSERT INTO _vp_outbox VALUES(?,?,?,?,?,?,?,?,?,NULL)",
                             (key, kind, json.dumps(payload), instructions,
                              json.dumps(expected_schema) if expected_schema is not None else None,
                              json.dumps(source) if source is not None else None, "pending", now, now))
            return self.outbox_get(key)  # type: ignore[return-value]

    def outbox_get(self, key: str) -> dict | None:
        r = self._db.execute("SELECT * FROM _vp_outbox WHERE key=?", (key,)).fetchone()
        if not r:
            return None
        return {"key": r["key"], "kind": r["kind"], "payload": json.loads(r["payload"]), "instructions": r["instructions"],
                "expected_schema": json.loads(r["expected_schema"]) if r["expected_schema"] else None,
                "source": json.loads(r["source"]) if r["source"] else None, "status": r["status"],
                "created_at": r["created_at"], "updated_at": r["updated_at"],
                "result": json.loads(r["result"]) if r["result"] else None}

    def outbox_list(self, status: str | None = None) -> list[dict]:
        rows = self._db.execute("SELECT key FROM _vp_outbox" + (" WHERE status=?" if status else "") + " ORDER BY created_at, key",
                                (status,) if status else ()).fetchall()
        return [self.outbox_get(r["key"]) for r in rows]  # type: ignore[misc]

    OUTBOX_STATUSES = ("pending", "in_progress", "done", "failed")

    def outbox_set(self, key: str, status: str, result: dict | None = None) -> dict:
        if status not in self.OUTBOX_STATUSES:
            raise CardError("invalid_input", f"Status must be one of {', '.join(self.OUTBOX_STATUSES)}.")
        if self.outbox_get(key) is None:
            raise CardError("not_found", f"No waiting item {key}.", {"key": key})
        self._db.execute("UPDATE _vp_outbox SET status=?, updated_at=?, result=COALESCE(?, result) WHERE key=?",
                         (status, iso(self.clock()), json.dumps(result) if result is not None else None, key))
        return self.outbox_get(key)  # type: ignore[return-value]

    # -- event log ----------------------------------------------------------

    def log_event(self, kind: str, message: str, details: dict | None = None) -> dict:
        cur = self._db.execute("INSERT INTO _vp_events(kind,message,details,at) VALUES(?,?,?,?)",
                               (str(kind)[:60], str(message)[:2000], json.dumps(details) if details else None, iso(self.clock())))
        return {"id": cur.lastrowid, "kind": kind, "message": message, "details": details or {}}

    def events(self, kind: str | None = None) -> list[dict]:
        rows = self._db.execute("SELECT * FROM _vp_events" + (" WHERE kind=?" if kind else "") + " ORDER BY id",
                                (kind,) if kind else ()).fetchall()
        return [{"id": r["id"], "kind": r["kind"], "message": r["message"],
                 "details": json.loads(r["details"]) if r["details"] else {}, "at": r["at"]} for r in rows]


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Context:
    """What every card receives first.

    store     saved data (SQLite)
    clock     returns 'now' (tests pass a fixed clock)
    preview   True while the local preview is running (triggers need it)
    event_id  id of the event being handled (the engine uses it for replay safety)
    settings  read-only app settings the generator fills in
    """

    store: Store
    clock: Callable[[], dt.datetime] = dt.datetime.now
    preview: bool = True
    event_id: str | None = None
    settings: dict = dataclasses.field(default_factory=dict)
    logs: list = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        self.store.clock = self.clock

    def now(self) -> dt.datetime:
        return self.clock().replace(microsecond=0)

    def today(self) -> dt.date:
        return self.clock().date()

    def log(self, level: str, message: str, **details: Any) -> None:
        self.logs.append({"level": level, "message": message, "details": details})

    def require_preview(self) -> None:
        """Triggers call this first: they run only while the local preview runs."""
        if not self.preview:
            raise CardError("preview_only", "This card runs only while the app preview is running.")

    @classmethod
    def for_tests(cls, now: str = "2026-01-15T09:30:00", preview: bool = True, event_id: str | None = None,
                  store: Store | None = None, settings: dict | None = None) -> "Context":
        fixed = dt.datetime.fromisoformat(now)
        return cls(store=store or Store(), clock=lambda: fixed, preview=preview, event_id=event_id, settings=settings or {})


# ---------------------------------------------------------------------------
# Card registry and decorator
# ---------------------------------------------------------------------------

CATEGORIES = ("UI / Interface", "Backend Processing", "Data Modeling / Storage", "Logic / Validation",
              "Triggers / Orchestration", "Integrations / Connectors", "AI Capabilities", "Navigation / Output")
PHASES = ("generation", "runtime", "human")
EFFECTS = ("reads_store", "writes_store", "outbox", "view", "file_text_in", "file_text_out")
ROLES = ("data", "view", "trigger", "flow", "route", "start", "end")


@dataclasses.dataclass
class CardSpec:
    name: str
    category: str
    group: str
    func: Callable[..., dict]
    module: str
    inputs: tuple[str, ...]
    config: tuple[str, ...]
    required_config: tuple[str, ...]
    outputs: tuple[str, ...]
    phase: str
    effects: tuple[str, ...]
    idempotent: bool
    role: str
    examples: list[dict]
    invalid: list[dict]
    summary: str

    def contract(self) -> dict:
        return {"name": self.name, "category": self.category, "group": self.group,
                "module": self.module, "function": self.func.__name__,
                "inputs": list(self.inputs), "config": list(self.config),
                "required_config": list(self.required_config), "outputs": list(self.outputs),
                "phase": self.phase, "effects": list(self.effects), "idempotent": self.idempotent,
                "role": self.role, "examples": len(self.examples), "invalid_cases": len(self.invalid),
                "summary": self.summary}


REGISTRY: dict[str, CardSpec] = {}


def card(name: str, *, category: str, group: str, inputs: Iterable[str], outputs: Iterable[str],
         phase: str = "runtime", effects: Iterable[str] = (), idempotent: bool = True, role: str = "data",
         examples: Iterable[dict] = (), invalid: Iterable[dict] = ()) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
    """Register a card template and record its contract.

    inputs   keyword names that carry DATA from other cards
    (config) every other keyword-only parameter. A config parameter WITHOUT a default is a
             required setting the builder must fill in (listed as required_config)
    outputs  names of the keys the function returns (route cards: the port names)
    phase    generation | runtime | human
    effects  reads_store writes_store outbox view file_text_in file_text_out
    role     data | view | trigger | flow | route | start | end
             (start = where the app begins, end = where it finishes; the only role that may have no outputs is end)
    examples [{"label","args","expect", optional "tables","rows","expect_rows","now","preview","event_id"}]
    invalid  [{"label","args","code", optional "tables","rows","now","preview"}]
    """
    def decorate(fn: Callable[..., dict]) -> Callable[..., dict]:
        if name in REGISTRY:
            raise ValueError(f"Duplicate card name: {name}")
        if category not in CATEGORIES:
            raise ValueError(f"{name}: unknown category {category!r}")
        if phase not in PHASES:
            raise ValueError(f"{name}: unknown phase {phase!r}")
        if role not in ROLES:
            raise ValueError(f"{name}: unknown role {role!r}")
        effect_list = tuple(effects)
        for effect in effect_list:
            if effect not in EFFECTS:
                raise ValueError(f"{name}: unknown effect {effect!r}")
        params = list(inspect.signature(fn).parameters.values())
        if not params or params[0].name != "ctx":
            raise ValueError(f"{name}: first parameter must be ctx")
        rest = params[1:]
        if any(p.kind is not inspect.Parameter.KEYWORD_ONLY for p in rest):
            raise ValueError(f"{name}: all parameters after ctx must be keyword-only (put * after ctx)")
        input_names = tuple(inputs)
        param_names = {p.name for p in rest}
        if not set(input_names) <= param_names:
            raise ValueError(f"{name}: inputs {set(input_names) - param_names} are not function parameters")
        config_params = [p for p in rest if p.name not in input_names]
        output_names = tuple(outputs)
        if not output_names:
            if role != "end":
                raise ValueError(f"{name}: outputs must not be empty")
        ex, inv = list(examples), list(invalid)
        if not ex:
            raise ValueError(f"{name}: at least one example is required")
        if rest and not inv:
            raise ValueError(f"{name}: at least one invalid case is required")
        doc = (inspect.getdoc(fn) or "").strip().splitlines()
        if not doc:
            raise ValueError(f"{name}: write a docstring (first line = what the card does)")
        REGISTRY[name] = CardSpec(
            name=name, category=category, group=group, func=fn, module=fn.__module__, inputs=input_names,
            config=tuple(p.name for p in config_params),
            required_config=tuple(p.name for p in config_params if p.default is inspect.Parameter.empty),
            outputs=output_names, phase=phase, effects=effect_list,
            idempotent=idempotent, role=role, examples=ex, invalid=inv, summary=doc[0])
        fn.card_spec = REGISTRY[name]  # type: ignore[attr-defined]
        return fn
    return decorate
